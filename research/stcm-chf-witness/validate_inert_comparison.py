#!/usr/bin/env python3
"""Inert synthetic-only specimen checks; no native STCM/CHF execution or authority."""
import hashlib
import json
import math
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent
SCHEMA = json.loads((ROOT / "common-specimen.schema.json").read_text())
BOLTZMANN_J_PER_K = 1.380649e-23


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def check_specimen(specimen, frozen_source_bytes: bytes):
    jsonschema.Draft202012Validator(SCHEMA).validate(specimen)
    if specimen["source"]["sha256"] != sha256_bytes(frozen_source_bytes):
        return "DENY_SPECIMEN_MISMATCH"
    transition = specimen["transition"]
    if transition["causal_relation"] == "established" and (
        not transition.get("predecessor_receipt_sha256") or not transition.get("causal_witness_sha256")
    ):
        return "DENY_CAUSAL_WITNESS_MISSING"
    if transition["causal_relation"] != "established":
        return "UNKNOWN_CAUSAL_RELATION"
    therm = specimen.get("thermodynamic_claim")
    if therm:
        if therm["physical_heat_status"] == "measured" and not therm.get("physical_heat_measurement_sha256"):
            return "DENY_PHYSICAL_MEASUREMENT_REFERENCE_MISSING"
        if therm["physical_heat_status"] != "measured" and therm.get("physical_heat_measurement_sha256"):
            return "DENY_CONTRADICTORY_PHYSICAL_MEASUREMENT"
        if therm["erase_count_status"] in ("not_applicable", "unknown", "not_observed") and any(
            therm.get(field) is not None for field in ("irreversible_erase_count", "landauer_bound_joules")
        ):
            return "DENY_UNSUPPORTED_ERASE_CLAIM"
        if therm.get("landauer_bound_joules") is not None:
            n, t = therm.get("irreversible_erase_count"), therm.get("temperature_kelvin")
            if n is None or t is None:
                return "DENY_LANDAUER_INPUTS_MISSING"
            expected = n * BOLTZMANN_J_PER_K * t * math.log(2)
            if not math.isclose(therm["landauer_bound_joules"], expected, rel_tol=1e-8, abs_tol=0):
                return "DENY_LANDAUER_CALCULATION_MISMATCH"
    if specimen["independent_witness"]["custody_status"] != "verified":
        return "INERT_UNVERIFIED_WITNESS"
    return "INERT_SYNTHETIC_ONLY"


def check_receipt_binding(specimen_sha256, receipts):
    """All independently supplied receipt envelopes must identify the same frozen specimen."""
    if not receipts:
        return "UNKNOWN_NATIVE_RECEIPTS_MISSING"
    if any(r.get("specimen_sha256") != specimen_sha256 for r in receipts):
        return "DENY_RECEIPT_MISMATCH"
    if any(not r.get("receipt_sha256") for r in receipts):
        return "UNKNOWN_NATIVE_RECEIPT_DIGEST_MISSING"
    return "INERT_DIGEST_BINDING_ONLY"
