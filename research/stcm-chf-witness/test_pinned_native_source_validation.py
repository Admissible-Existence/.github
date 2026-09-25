"""Source-only adversarial checks for pinned native acquisition and evidence classes."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from validate_pinned_native_sources import check_source, assess_stcm, digest


def git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class PinnedNativeSourceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        git("init", cwd=self.root)
        git("config", "user.name", "synthetic-only-tests", cwd=self.root)
        git("config", "user.email", "synthetic@example.invalid", cwd=self.root)
        (self.root / "src.py").write_text("print('synthetic-only source')\n")
        git("add", "src.py", cwd=self.root)
        git("commit", "-m", "synthetic fixture only", cwd=self.root)
        self.commit = git("rev-parse", "HEAD", cwd=self.root)
        self.blob = git("hash-object", "src.py", cwd=self.root)
        self.spec = {"repo": "SYNTHETIC_ONLY", "commit": self.commit,
                     "blob_guards": {"src.py": self.blob}}

    def test_exact_commit_and_git_blob_accept_only_original_bytes(self):
        result = check_source(self.root, self.spec)
        self.assertEqual(result["exact_commit"], self.commit)
        self.assertEqual(result["verified_blob_sources"]["src.py"]["git_blob_sha1"], self.blob)
        self.assertEqual(result["verified_blob_sources"]["src.py"]["sha256_original_bytes"],
                         digest((self.root / "src.py").read_bytes()))

    def test_modified_original_bytes_fail_closed(self):
        (self.root / "src.py").write_text("print('forged content')\n")
        with self.assertRaisesRegex(ValueError, "source blob differs"):
            check_source(self.root, self.spec)

    def test_substituted_revision_fails_closed(self):
        self.spec["commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit differs"):
            check_source(self.root, self.spec)

    def test_missing_original_source_fails_closed(self):
        (self.root / "src.py").unlink()
        with self.assertRaisesRegex(ValueError, "source file absent"):
            check_source(self.root, self.spec)

    def test_native_baseline_without_expected_report_cannot_pass(self):
        spec = dict(self.spec, entry="src.py", report="missing-native-report.json")
        actual = assess_stcm(self.root, spec)
        self.assertFalse(actual["baseline_validation_pass"])
        self.assertIsNone(actual["native_report_sha256"])

    def test_nonzero_native_result_never_qualifies(self):
        (self.root / "native.py").write_text("raise SystemExit(19)\n")
        spec = dict(self.spec, entry="native.py", report="missing-report.json")
        actual = assess_stcm(self.root, spec)
        self.assertEqual(actual["native_execution"]["returncode"], 19)
        self.assertFalse(actual["baseline_validation_pass"])

    def test_hash_function_is_over_original_bytes(self):
        self.assertEqual(digest(b"one"), "sha256:" + hashlib.sha256(b"one").hexdigest())


if __name__ == "__main__":
    unittest.main()
