import json, unittest
from pathlib import Path
ROOT=Path(__file__).parent
class TestXF001MutualReview(unittest.TestCase):
 def setUp(self): self.c=json.loads((ROOT/'xf001-stegverse-mutual-review.json').read_text())
 def test_owner_and_identity(self):
  self.assertEqual(self.c['goal_task_id'],'STCM-CHF-THERMODYNAMIC-WITNESS-COMPARISON-001'); self.assertEqual(self.c['cosv_id'],'10111010112000')
 def test_no_flint_wait_state(self):
  self.assertIn('FLINT_SPECIMEN_BYTES',self.c['not_required_for_stegverse_protocol_review']); self.assertEqual(self.c['external_semantics_policy'],'OPAQUE_UNPOPULATED')
 def test_existing_owner_routing(self):
  self.assertEqual(self.c['native_owner_routing']['CHF']['sdk_route'],'stegverse.route.source-native-math.v1'); self.assertEqual(self.c['native_owner_routing']['STCM']['sdk_binding_state'],'NOT_ESTABLISHED_FOR_STCM')
 def test_comparison_preserves_residuals(self):
  x=self.c['receipt_comparison']; self.assertTrue(x['preserve_all_discrepancies']); self.assertTrue(x['preserve_unexplained_residuals']); self.assertFalse(x['external_receipt_semantics_inferred'])
 def test_no_execution_claim(self): self.assertEqual(self.c['authority_effect'],'NONE'); self.assertEqual(self.c['common_specimen_execution_state'],'NOT_STARTED')
if __name__=='__main__': unittest.main()
