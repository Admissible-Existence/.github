"""Synthetic-only STCM/CHF witness negative controls (no authentic execution)."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from validate_inert_comparison import check_specimen, check_receipt_binding

ROOT = Path(__file__).resolve().parent
SOURCE = b'{"synthetic":"source-v0"}\n'
SOURCE_HASH = "sha256:" + hashlib.sha256(SOURCE).hexdigest()


def load(name):
    return json.loads((ROOT / "fixtures" / (name + ".json")).read_text())


class InertComparisonTests(unittest.TestCase):
    def test_frozen_bytes_bound_before_any_interpretation(self):
        self.assertEqual(load("positive_synthetic")["source"]["sha256"], SOURCE_HASH)

    def test_positive_synthetic_never_promotes(self):
        self.assertEqual(check_specimen(load("positive_synthetic"), SOURCE), "INERT_UNVERIFIED_WITNESS")

    def test_computational_state_change_does_not_imply_erasure(self):
        x = load("computational_change_no_erasure")
        self.assertEqual(x["thermodynamic_claim"]["erase_count_status"], "not_applicable")
        self.assertEqual(check_specimen(x, SOURCE), "INERT_UNVERIFIED_WITNESS")

    def test_computed_landauer_not_measured_heat(self):
        x = load("claimed_erasure_without_heat_measurement")
        self.assertEqual(x["thermodynamic_claim"]["physical_heat_status"], "not_observed")
        self.assertEqual(check_specimen(x, SOURCE), "INERT_UNVERIFIED_WITNESS")

    def test_mismatched_specimen_bytes_denied(self):
        self.assertEqual(check_specimen(load("specimen_digest_mismatch"), SOURCE), "DENY_SPECIMEN_MISMATCH")

    def test_coincident_timestamps_not_causal_proof(self):
        self.assertEqual(check_specimen(load("coincident_timestamps_no_causal_proof"), SOURCE), "UNKNOWN_CAUSAL_RELATION")

    def test_missing_causal_witness_denied(self):
        x = load("positive_synthetic")
        x["transition"]["causal_witness_sha256"] = None
        self.assertEqual(check_specimen(x, SOURCE), "DENY_CAUSAL_WITNESS_MISSING")

    def test_claimed_measured_heat_without_reference_denied(self):
        x = load("positive_synthetic")
        x["thermodynamic_claim"]["physical_heat_status"] = "measured"
        self.assertEqual(check_specimen(x, SOURCE), "DENY_PHYSICAL_MEASUREMENT_REFERENCE_MISSING")

    def test_false_measurement_reference_denied(self):
        x = load("positive_synthetic")
        x["thermodynamic_claim"]["physical_heat_measurement_sha256"] = "sha256:" + "a" * 64
        self.assertEqual(check_specimen(x, SOURCE), "DENY_CONTRADICTORY_PHYSICAL_MEASUREMENT")

    def test_bad_landauer_calculation_denied(self):
        x = load("claimed_erasure_without_heat_measurement")
        x["thermodynamic_claim"]["landauer_bound_joules"] *= 2
        self.assertEqual(check_specimen(x, SOURCE), "DENY_LANDAUER_CALCULATION_MISMATCH")

    def test_receipt_specimen_mismatch_denied(self):
        a = "sha256:" + "a" * 64
        b = "sha256:" + "b" * 64
        self.assertEqual(check_receipt_binding(a, [{"specimen_sha256": a, "receipt_sha256": a}, {"specimen_sha256": b, "receipt_sha256": b}]), "DENY_RECEIPT_MISMATCH")

    def test_missing_native_receipts_unknown(self):
        self.assertEqual(check_receipt_binding(SOURCE_HASH, []), "UNKNOWN_NATIVE_RECEIPTS_MISSING")

    def test_receipt_digest_binding_inert(self):
        r = [{"specimen_sha256": SOURCE_HASH, "receipt_sha256": "sha256:" + "c" * 64}]
        self.assertEqual(check_receipt_binding(SOURCE_HASH, r), "INERT_DIGEST_BINDING_ONLY")

    def test_false_verified_fixture_never_proves_authenticity(self):
        x = load("positive_synthetic")
        x["independent_witness"]["custody_status"] = "verified"
        self.assertEqual(check_specimen(x, SOURCE), "INERT_SYNTHETIC_ONLY")


if __name__ == "__main__":
    unittest.main()
