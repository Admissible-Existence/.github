"""Non-authoritative evidence correlation of two independently run native synthetic paths.

This does not fetch private CHF source, claim generic SDK invocation, or convert
supplied threshold values or synthetic lineage into measurements.
"""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = json.loads((HERE / "same-specimen-capability-map.json").read_text(encoding="utf-8"))


class SameSourceTwoNativeOwners(unittest.TestCase):
    def test_exact_original_source_digest_reused_by_both(self):
        original = EVIDENCE["frozen_source_sha256"]
        self.assertEqual(EVIDENCE["source_owners"]["STCM"]["native_original_source_evidence"]["same_frozen_source_sha256"], original)
        self.assertEqual(EVIDENCE["source_owners"]["CHF"]["bounded_original_source_callable"]["same_frozen_source_sha256"], original)

    def test_source_native_original_stcm_remains_constructed_fixture(self):
        source = EVIDENCE["source_owners"]["STCM"]["native_original_source_evidence"]
        self.assertEqual(source["native_run_id"], 36091077891)
        self.assertIn("CONSTRUCTED_PRIOR_NOT_REAL", source["scope"])
        self.assertEqual(EVIDENCE["source_owners"]["STCM"]["authentic_prior_receipt"], "NOT_RECEIVED")

    def test_chf_four_original_inequalities_now_native_but_bounded(self):
        source = EVIDENCE["source_owners"]["CHF"]["bounded_original_source_callable"]
        self.assertEqual(source["native_owner_pr"], "Admissible-Existence/CHF#5")
        self.assertEqual(source["native_hosted_conclusion"], "success")
        self.assertTrue(source["original_source_bytes_verified"])
        self.assertEqual(source["consequence_horizon_disposition"], "NOT_ESTABLISHED")
        self.assertIn("ONLY", source["evaluates"])

    def test_original_chf_positive_adversarial_and_missing_cases_are_distinct(self):
        controls = EVIDENCE["source_owners"]["CHF"]["bounded_original_source_callable"]["synthetic_native_controls"]
        self.assertEqual(set(controls), {
            "ALL_FOUR_DECLARED_THRESHOLDS_SATISFIED",
            "BELOW_DECLARED_THRESHOLD", "UNKNOWN_INPUT", "DENY_ORIGINAL_SOURCE_HASH",
        })

    def test_original_source_math_remains_separately_owned(self):
        self.assertEqual(EVIDENCE["source_owners"]["CHF"]["repository"], "Admissible-Existence/CHF")
        self.assertEqual(EVIDENCE["source_owners"]["STCM"]["repository"], "Admissible-Existence/STCM")
        self.assertEqual(EVIDENCE["sdk"]["integration_owner"],
                         "ADMISSIBLE-EXISTENCE-MATHEMATICAL-PROCESSING-INTEGRATION")

    def test_generic_sdk_native_math_is_not_false_positive(self):
        self.assertEqual(EVIDENCE["sdk"]["native_mathematical_processor_binding"], "NOT_ESTABLISHED")
        self.assertIn("NOT_FULL_HORIZON", EVIDENCE["comparison_status"])

    def test_no_promoted_real_evidence(self):
        self.assertEqual(EVIDENCE["authority_effect"], "NONE")
        self.assertEqual(EVIDENCE["source_owners"]["CHF"]["bounded_original_source_callable"]["input_provenance"],
                         "SYNTHETIC_NOT_EXTERNAL_MEASUREMENT")
        self.assertIn("physical heat", EVIDENCE["source_owners"]["CHF"]["bounded_original_source_callable"]["does_not_evaluate"])


if __name__ == "__main__":
    unittest.main()
