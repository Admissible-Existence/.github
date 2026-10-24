#!/usr/bin/env python3
"""Outbound-only Service Gateway transport for organization federation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("org_kernel", ROOT / "org-kernel" / "kernel.py")
K = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(K)

GATEWAY_ENV = "STEGVERSE_ORG_FEDERATION_GATEWAY_URL"
TIMEOUT_ENV = "STEGVERSE_ORG_FEDERATION_GATEWAY_TIMEOUT_SECONDS"


class FederationGatewayTransportError(RuntimeError):
    pass


def gateway_base_url() -> str:
    raw = os.getenv(GATEWAY_ENV, "").strip().rstrip("/")
    if not raw:
        raise FederationGatewayTransportError("organization federation gateway URL not configured")
    if not raw.startswith("https://"):
        raise FederationGatewayTransportError("organization federation gateway must use HTTPS")
    return raw


def timeout_seconds() -> float:
    raw = os.getenv(TIMEOUT_ENV, "10").strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise FederationGatewayTransportError("invalid federation gateway timeout") from exc
    if value <= 0 or value > 60:
        raise FederationGatewayTransportError("federation gateway timeout outside bounds")
    return value


def _json_request(method: str, path: str, *, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    url = gateway_base_url() + path
    raw = None if body is None else json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hdrs = {"Accept": "application/json", **(headers or {})}
    if raw is not None:
        hdrs["Content-Type"] = "application/json"
    req = Request(url, data=raw, headers=hdrs, method=method)
    try:
        with urlopen(req, timeout=timeout_seconds()) as resp:
            payload = resp.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise FederationGatewayTransportError(f"gateway request failed: {exc}") from exc
    try:
        return json.loads(payload.decode("utf-8"))
    except (RecursionError, MemoryError) as exc:
        # The response may be a readable envelope around one unusable member
        # (a deeply nested frame): read its top level without recursion, so
        # the frame is refused by name instead of the fetch failing forever.
        shallow = _shallow_envelope(payload, exc)
        if shallow is None:
            raise FederationGatewayTransportError("gateway response is not JSON") from exc
        return shallow
    except Exception as exc:
        raise FederationGatewayTransportError("gateway response is not JSON") from exc


class UnusableFrame:
    """A gateway-offered frame inside a readable envelope that does not decode."""

    def __init__(self, error: BaseException, raw: str) -> None:
        self.error = error
        self.raw_sha256 = "sha256:" + hashlib.sha256(raw.encode("utf-8", "surrogatepass")).hexdigest()
        # Whatever identity its own top level still yields, read without
        # recursion, so the BLOCKED acknowledgement names the frame it retires.
        members = _shallow_members(raw, nested=False) or {}
        self.identity = {name: members[name] for name in ("packet_id", "frame_sha256")
                         if isinstance(members.get(name), str)}


def _json_value_end(text: str, index: int) -> int:
    """The end of the JSON value starting at index, found without recursion."""
    if text[index] == '"':
        return json.decoder.scanstring(text, index + 1)[1]
    if text[index] in "[{":
        depth = 0
        while True:
            char = text[index]
            if char == '"':
                index = json.decoder.scanstring(text, index + 1)[1]
                continue
            if char in "[{":
                depth += 1
            elif char in "]}":
                depth -= 1
                if depth == 0:
                    return index + 1
            index += 1
    end = index
    while end < len(text) and text[end] not in ",}] \t\r\n":
        end += 1
    return end


def _shallow_envelope(payload: bytes, error: BaseException) -> dict[str, Any] | None:
    """The top-level object of a response whose full decode recursed too deep.

    Each member is decoded on its own; a member that still does not decode is
    kept as an UnusableFrame. Returns None unless the top level is an object
    whose `state` decodes, so an unreadable envelope stays unreadable."""
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None
    members = _shallow_members(text)
    if members is None or not isinstance(members.get("state"), str):
        return None
    return members


def _shallow_members(text: str, *, nested: bool = True) -> dict[str, Any] | None:
    """The members of a top-level JSON object, each decoded on its own without
    recursion; None if the top level is not a readable object. A member that
    does not decode is an UnusableFrame (or omitted, when nested is False)."""
    try:
        whitespace = " \t\r\n"
        index = 0
        while text[index] in whitespace:
            index += 1
        if text[index] != "{":
            return None
        index += 1
        members: dict[str, Any] = {}
        while True:
            while text[index] in whitespace:
                index += 1
            if text[index] == "}":
                break
            key, index = json.decoder.scanstring(text, index + 1)
            while text[index] in whitespace:
                index += 1
            if text[index] != ":":
                return None
            index += 1
            while text[index] in whitespace:
                index += 1
            end = _json_value_end(text, index)
            raw = text[index:end]
            try:
                members[key] = K.strict_json_loads(raw)
            except K.JSON_DECODE_ERRORS as member_error:
                if nested:
                    members[key] = UnusableFrame(member_error, raw)
            index = end
            while text[index] in whitespace:
                index += 1
            if text[index] == ",":
                index += 1
            elif text[index] != "}":
                return None
    except (ValueError, IndexError):
        return None
    return members


def submit_frame(frame: dict[str, Any]) -> dict[str, Any]:
    validated = K.recover_packet(frame)
    origin_org = validated["origin"]["org"]
    return _json_request(
        "POST",
        "/api/org-federation/v1/frames",
        body=frame,
        headers={"X-StegVerse-Origin-Organization": origin_org},
    )


def fetch_frame(organization: str) -> dict[str, Any]:
    query = urlencode({"organization": organization})
    return _json_request(
        "GET",
        "/api/org-federation/v1/frames?" + query,
        headers={"X-StegVerse-Organization": organization},
    )


def acknowledge_frame(organization: str, frame: dict[str, Any], state: str,
                      epoch: int | None = None, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    """Acknowledge a frame. No clock is read: `observed_at` is the frame's
    validated epoch's heartbeat id, or null when the frame lends none."""
    frame = frame if isinstance(frame, dict) else {}
    ack = {
        "schema": "stegverse.org-federation-rendezvous.ack/v1",
        "organization": organization,
        "packet_id": frame.get("packet_id"),
        "frame_sha256": frame.get("frame_sha256"),
        "state": state,
        "observed_at": "HB:" + str(epoch) if epoch is not None else None,
        "derived_from_clock": False,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
        **(identity or {}),
    }
    return _json_request(
        "POST",
        "/api/org-federation/v1/acknowledgements",
        body=ack,
        headers={"X-StegVerse-Organization": organization},
    )


def publish_ecosystem_via_gateway(
    *,
    repo_root: Path,
    message_class: str,
    subject: str,
    body: dict[str, Any],
    requested_action: str | None = None,
    communication_id: str | None = None,
    epoch: int | None = None,
) -> dict[str, Any]:
    registry = K.load_registry(repo_root)
    directory = K.load_federation_directory(repo_root)
    orgs = [row["organization"] for row in directory["organizations"]]
    built = K.build_ecosystem_packets(
        origin_org=registry["organization"],
        origin_service=K.organization_slug(registry["organization"]) + ".org-control",
        organizations=orgs,
        message_class=message_class,
        subject=subject,
        body=body,
        requested_action=requested_action,
        communication_id=communication_id,
    )
    results = []
    for packet in built["packets"]:
        frame = K.carrier_frame(packet, epoch=epoch)
        stored = submit_frame(frame)
        results.append({
            "organization": packet["destination"]["org"],
            "packet_id": packet["packet_id"],
            "frame_sha256": frame["frame_sha256"],
            "gateway_state": stored.get("state"),
        })
    return {
        "communication_id": built["communication_id"],
        "organization_count": len(results),
        "published_count": sum(1 for row in results if row["gateway_state"] == "PENDING"),
        "gateway_execution_authority": "NONE",
        "organizations": results,
    }


def _persist_response(repo_root: Path, packet: dict[str, Any], execution_result: dict[str, Any]) -> Path:
    payload = packet.get("payload") or {}
    communication_id = str(payload.get("communication_id") or "unknown")
    out = repo_root / "resident-runtime" / "control" / "responses.d"
    out.mkdir(parents=True, exist_ok=True)
    name = K.sha({
        "communication_id": communication_id,
        "packet_id": packet["packet_id"],
        "origin_org": packet["origin"]["org"],
    }).split(":", 1)[1] + ".json"
    record = {
        "schema_version": "stegverse.ecosystem-response-observation.v1",
        "communication_id": communication_id,
        "packet_id": packet["packet_id"],
        "origin_org": packet["origin"]["org"],
        "message_class": payload.get("message_class"),
        "application_result": execution_result.get("application_result"),
        "reconstruction": execution_result.get("reconstruction"),
        "authority_effect": execution_result.get("authority_effect"),
    }
    path = out / name
    if path.exists():
        if json.loads(path.read_text()) != record:
            raise FederationGatewayTransportError("response observation write-once collision")
    else:
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


def _fetch_refusal(organization: str, detail: str) -> dict[str, Any]:
    return {
        "schema_version": "stegverse.org-federation-gateway-cycle.v1",
        "organization": organization,
        "state": "FAIL_CLOSED",
        "frames_consumed": 0,
        "responses_emitted": 0,
        "gateway_execution_authority": "NONE",
        "disposition": "FAIL_CLOSED",
        "failure_code": "GATEWAY_FETCH_INVALID",
        "failed_predicate": "GATEWAY_FETCH_IS_A_JSON_OBJECT_WITH_A_KNOWN_STATE",
        "detail": detail[:512],
        "required_evidence_or_repair": "the gateway answers the fetch with a JSON object: state NO_FRAME, or FRAME_AVAILABLE with an object frame",
        "retry_entrypoint": "resident-runtime/federation_gateway_transport.py::resident_gateway_cycle",
        "owning_existing_goal": K.HB_EPOCH_OWNING_EXISTING_GOAL,
        "next_attempt": "the next cycle fetches again; nothing was ingested, written or acknowledged",
        "derived_from_clock": False,
        "consequence_committed": False,
    }


def resident_gateway_cycle(repo_root: Path) -> dict[str, Any]:
    registry = K.load_registry(repo_root)
    organization = registry["organization"]
    # A fetch that is not a JSON object with a known state is a six-field
    # refusal; nothing escapes the cycle as an exception.
    try:
        fetched = fetch_frame(organization)
    except FederationGatewayTransportError as error:
        return _fetch_refusal(organization, str(error))
    if not isinstance(fetched, dict):
        return _fetch_refusal(organization, "gateway fetch is not a JSON object")
    if fetched.get("state") == "NO_FRAME":
        return {
            "schema_version": "stegverse.org-federation-gateway-cycle.v1",
            "organization": organization,
            "state": "NO_FRAME",
            "frames_consumed": 0,
            "responses_emitted": 0,
            "gateway_execution_authority": "NONE",
        }
    if fetched.get("state") != "FRAME_AVAILABLE":
        return _fetch_refusal(organization, "unexpected gateway fetch state " + repr(fetched.get("state")))
    frame = fetched.get("frame")
    if isinstance(frame, UnusableFrame):
        # A readable envelope around a frame that does not decode (deeply
        # nested): the frame's own defect, so it is refused terminally and
        # acknowledged BLOCKED rather than offered again forever.
        return _blocked_unusable(organization, frame)
    try:
        return _gateway_frame_cycle(repo_root, organization, frame)
    except (OSError, FederationGatewayTransportError) as error:
        # This boundary's own I/O or transport failed: the frame is not at
        # fault and is not acknowledged, so the gateway offers it again.
        return _pending_io(organization, frame, error)
    except Exception as error:
        if K.is_own_state_fault(error):
            return _pending_io(organization, frame, error)
        refusal = K.frame_ingest_refusal(frame, error)
        try:
            ack = acknowledge_frame(organization, frame, "BLOCKED")
        except (OSError, FederationGatewayTransportError) as ack_error:
            return _pending_io(organization, frame, ack_error)
        return {
            "schema_version": "stegverse.org-federation-gateway-cycle.v1",
            "organization": organization,
            "state": "BLOCKED",
            "packet_id": frame.get("packet_id") if isinstance(frame, dict) else None,
            "frames_consumed": 0,
            "responses_emitted": 0,
            "ingest_refusal": refusal,
            "ack_state": ack.get("state") if isinstance(ack, dict) else None,
            "gateway_execution_authority": "NONE",
        }


def _blocked_unusable(organization: str, frame: UnusableFrame) -> dict[str, Any]:
    refusal = {**K.frame_ingest_refusal(frame.identity, frame.error), "frame_raw_sha256": frame.raw_sha256}
    try:
        ack = acknowledge_frame(organization, dict(frame.identity), "BLOCKED",
                                identity={"frame_raw_sha256": frame.raw_sha256})
    except (OSError, FederationGatewayTransportError) as ack_error:
        return _pending_io(organization, None, ack_error)
    return {
        "schema_version": "stegverse.org-federation-gateway-cycle.v1",
        "organization": organization,
        "state": "BLOCKED",
        "packet_id": frame.identity.get("packet_id"),
        "frames_consumed": 0,
        "responses_emitted": 0,
        "ingest_refusal": refusal,
        "ack_state": ack.get("state") if isinstance(ack, dict) else None,
        "gateway_execution_authority": "NONE",
    }


def _pending_io(organization: str, frame: Any, error: BaseException) -> dict[str, Any]:
    return {
        "schema_version": "stegverse.org-federation-gateway-cycle.v1",
        "organization": organization,
        "state": "PENDING_IO",
        "packet_id": frame.get("packet_id") if isinstance(frame, dict) else None,
        "frames_consumed": 0,
        "responses_emitted": 0,
        "ingest_refusal": K.dispatch_io_refusal(frame, error),
        "ack_state": None,
        "gateway_execution_authority": "NONE",
    }


def _submit_response_once(repo_root: Path, response: dict[str, Any], epoch: int) -> tuple[dict[str, Any], bool]:
    """Submit a response once per response packet id.

    The frame is recorded before it is submitted and marked submitted after,
    so a cycle retried after a later fault (an ack that failed) does not
    submit it again; a retry before the mark resubmits the same recorded bytes.
    Returns the frame and whether this call submitted it.
    """
    path = _response_record_path(repo_root, response["packet_id"])
    request_id = ((response.get("payload") or {}).get("body") or {}).get("request_packet_id")
    if path.is_file():
        record = json.loads(path.read_text())
        if record.get("request_packet_id") != request_id:
            raise ValueError("communication_id_collision")
        frame = record["frame"]
        if record.get("submitted") is True:
            return frame, False
    else:
        frame = K.carrier_frame(response, epoch=epoch)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"packet_id": response["packet_id"], "request_packet_id": request_id,
                                    "frame": frame, "submitted": False}, indent=2, sort_keys=True) + "\n")
    submit_frame(frame)
    path.write_text(json.dumps({"packet_id": response["packet_id"], "request_packet_id": request_id,
                                "frame": frame, "submitted": True}, indent=2, sort_keys=True) + "\n")
    return frame, True


def _response_record_path(repo_root: Path, response_packet_id: str) -> Path:
    return (repo_root / "resident-runtime" / "federation" / "responses-submitted.d"
            / (hashlib.sha256(response_packet_id.encode()).hexdigest() + ".json"))


def _gateway_collision(repo_root: Path, frame: Any) -> dict[str, Any] | None:
    """The collision refusal for a request whose response id already answers another request, or None."""
    try:
        packet = K.recover_packet(frame)
    except Exception:
        return None
    if (packet.get("payload") or {}).get("message_class") not in K.RESPONDED_REQUEST_CLASSES:
        return None
    path = _response_record_path(repo_root, K.response_packet_id(packet))
    if not path.is_file():
        return None
    answered = json.loads(path.read_text()).get("request_packet_id")
    if answered == packet["packet_id"]:
        return None
    return K.communication_collision_refusal(packet, answered)


def _gateway_frame_cycle(repo_root: Path, organization: str, frame: Any) -> dict[str, Any]:
    # Any error ingesting the frame, a non-object frame included, is a
    # six-field refusal, acknowledged BLOCKED. An I/O failure of this
    # boundary's own leaves it pending and unacknowledged. A second, different
    # request under a communication id already answered is refused before it
    # is dispatched.
    result = _gateway_collision(repo_root, frame) or K.ingest_frame(repo_root, frame)
    if result.get("failure_code") == K.FRAME_DISPATCH_IO_FAILED:
        return {
            "schema_version": "stegverse.org-federation-gateway-cycle.v1",
            "organization": organization,
            "state": "PENDING_IO",
            "packet_id": result.get("packet_id"),
            "frames_consumed": 0,
            "responses_emitted": 0,
            "ingest_refusal": result,
            "ack_state": None,
            "gateway_execution_authority": "NONE",
        }
    packet = result.get("packet") or {}
    # The response carries the frame's validated epoch. The epoch is read only
    # from a frame ingest accepted, whose hashes recomputed, so a BLOCKED ack
    # never echoes an epoch from a tampered frame. A frame that lends none (a
    # clock-flagged or clock-sampled one) gets no response, and no clock is
    # read on this route.
    if result.get("status") == "CONSUMED":
        epoch, failure = K.carried_frame_epoch(frame)
    else:
        epoch, failure = None, None
    response_emitted = 0
    response_ref = None
    response_refusal = None
    if result.get("status") == "CONSUMED":
        execution = result["execution_result"]
        message_class = (packet.get("payload") or {}).get("message_class")
        if message_class in {"ecosystem.monitor.request", "ecosystem.work.request", "ecosystem.communication"}:
            if epoch is None:
                response_refusal = K.response_epoch_refusal(failure)
            else:
                response = K.build_control_response(packet, execution)
                response_frame, submitted = _submit_response_once(repo_root, response, epoch)
                response_emitted = 1 if submitted else 0
                response_ref = response_frame["frame_sha256"]
        elif message_class in {"ecosystem.monitor.response", "ecosystem.work.ack", "ecosystem.communication.ack"}:
            _persist_response(repo_root, packet, execution)
        ack_state = "CONSUMED"
    else:
        ack_state = "BLOCKED"
    ack = acknowledge_frame(organization, frame, ack_state, epoch=epoch)
    return {
        "schema_version": "stegverse.org-federation-gateway-cycle.v1",
        "organization": organization,
        "state": ack_state,
        "packet_id": frame.get("packet_id") if isinstance(frame, dict) else None,
        "frame_sha256": frame.get("frame_sha256") if isinstance(frame, dict) else None,
        "frames_consumed": 1 if ack_state == "CONSUMED" else 0,
        "responses_emitted": response_emitted,
        "response_frame_sha256": response_ref,
        "response_refusal": response_refusal,
        "ingest_refusal": None if result.get("status") == "CONSUMED" else result,
        "ack_state": ack.get("state"),
        "gateway_execution_authority": "NONE",
    }


def collect_local_responses(repo_root: Path, communication_id: str) -> dict[str, Any]:
    directory = repo_root / "resident-runtime" / "control" / "responses.d"
    rows = []
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            try:
                value = json.loads(path.read_text())
            except Exception:
                continue
            if value.get("communication_id") == communication_id:
                rows.append(value)
    orgs = sorted({row.get("origin_org") for row in rows if row.get("origin_org")})
    return {
        "communication_id": communication_id,
        "response_count": len(orgs),
        "organizations": orgs,
        "complete": len(orgs) == 14,
    }
