import unittest
from validate_xf001_external_intake import disposition, GOAL, COSV

H="sha256:"+"a"*64
def specimen():
    return {
      "protocol_id":"XF-001","goal_task_id":GOAL,"cosv_id":COSV,
      "specimen_id":"external-specimen","transition_id":"external-transition",
      "original_state":{"format":"external/native","sha256":H},
      "resulting_state":{"format":"external/native","sha256":H},
      "source_bindings":[{"format":"external/source","sha256":H}],
      "independent_witness":{"identity":"external-witness","evidence_sha256":H,"custody_status":"verified"},
      "external_accounting":{"receipt_sha256":H}
    }

class TestXF001Intake(unittest.TestCase):
    def test_complete_envelope_is_ready_not_executed(self):
        self.assertEqual(disposition(specimen()),"ALLOW_XF001_NATIVE_EVALUATION_INPUT_READY")
    def test_missing_external_receipt_fails_closed(self):
        x=specimen(); x["external_accounting"]={}
        self.assertEqual(disposition(x),"FAIL_CLOSED_EXTERNAL_RECEIPT_BINDING")
    def test_unverified_witness_custody_fails_closed(self):
        x=specimen(); x["independent_witness"]["custody_status"]="unverified"
        self.assertEqual(disposition(x),"FAIL_CLOSED_WITNESS_CUSTODY")
    def test_wrong_owner_fails_closed(self):
        x=specimen(); x["goal_task_id"]="OTHER"
        self.assertEqual(disposition(x),"FAIL_CLOSED_CANONICAL_OWNER_BINDING")
if __name__=="__main__": unittest.main()
