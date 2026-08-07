import unittest

from scripts.process_heartbeat_response import authority_is_false, make_receipts, select_message


class HeartbeatResponseTests(unittest.TestCase):
    def setUp(self):
        self.authority = {"execution":False,"activation":False,"publication":False,"custody":False,"release":False}
        self.message = {
            "message_id":"msg-00000001",
            "exchange_id":"ex-00000001",
            "source_org":"StegVerse-Labs",
            "destination_org":"Admissible-Existence",
            "stage":"SENT",
            "detail_class":"AWARENESS",
            "retention_class":"PROJECT",
            "authority":self.authority,
        }
        self.config = {
            "organization":"Admissible-Existence",
            "supported_detail_classes":["MEMORY","ACTION","AWARENESS","AUTHORITY","EVIDENCE","BLOCKER","CAPABILITY","CONTEXT"],
            "response_detail_class":"CAPABILITY",
        }

    def test_selects_exact_destination(self):
        self.assertEqual(select_message({"messages":[self.message]}, "Admissible-Existence")["message_id"], "msg-00000001")

    def test_rejects_authority_escalation(self):
        message = dict(self.message)
        message["authority"] = dict(self.authority, execution=True)
        with self.assertRaises(ValueError):
            select_message({"messages":[message]}, "Admissible-Existence")

    def test_emits_received_then_responded_without_authority(self):
        received, responded = make_receipts(self.message, self.config, "2026-08-07T14:42:00Z")
        self.assertEqual(received["stage"], "RECEIVED")
        self.assertEqual(responded["stage"], "RESPONDED")
        self.assertEqual(responded["detail_class"], "CAPABILITY")
        self.assertTrue(authority_is_false(received["authority"]))
        self.assertTrue(authority_is_false(responded["authority"]))
        self.assertFalse(responded["classification"]["action_admitted"])

    def test_missing_destination_fails_closed(self):
        with self.assertRaises(ValueError):
            select_message({"messages":[]}, "Admissible-Existence")


if __name__ == "__main__":
    unittest.main()
