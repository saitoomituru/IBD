import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "experiments" / "season0" / "fquery_cli.py"


def _document(fam_ref, revision_ref):
    return {
        "fam_ref": fam_ref,
        "revision_ref": revision_ref,
        "l_topology": {"parent": None, "children": [], "siblings": [], "prev": None, "next": None},
        "fold_refs": [],
        "q_refs": {"registry_refs": [], "fact_scope": "test"},
        "provenance": {"source": "test-fixture"},
    }


class FquerCliTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = str(Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    def _run(self, request):
        completed = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return completed

    def test_put_then_resolve_round_trip_via_real_subprocess(self):
        put_completed = self._run({
            "operation": "put",
            "root": self.root,
            "document": _document("fam:fquery-cli-1", "rev-1"),
        })
        self.assertEqual(put_completed.returncode, 0, put_completed.stderr)
        put_response = json.loads(put_completed.stdout)
        self.assertEqual(put_response["status"], "ok")
        self.assertEqual(put_response["document"]["fam_ref"], "fam:fquery-cli-1")

        resolve_completed = self._run({
            "operation": "resolve",
            "root": self.root,
            "fam_ref": "fam:fquery-cli-1",
            "revision_policy": {"mode": "latest"},
        })
        self.assertEqual(resolve_completed.returncode, 0, resolve_completed.stderr)
        resolve_response = json.loads(resolve_completed.stdout)
        self.assertEqual(resolve_response["status"], "ok")
        self.assertEqual(resolve_response["result"]["status"], "resolved")
        self.assertEqual(resolve_response["result"]["revision_ref"], "rev-1")
        self.assertEqual(resolve_response["result"]["document"]["fam_ref"], "fam:fquery-cli-1")

    def test_resolve_unknown_fam_ref_returns_structured_last_order_not_a_crash(self):
        completed = self._run({
            "operation": "resolve",
            "root": self.root,
            "fam_ref": "fam:does-not-exist",
            "revision_policy": {"mode": "latest"},
        })
        self.assertEqual(completed.returncode, 0, completed.stderr)
        response = json.loads(completed.stdout)
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["result"]["status"], "unknown")

    def test_invalid_json_request_exits_nonzero_with_structured_error(self):
        completed = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            input="not-json",
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 1)
        response = json.loads(completed.stdout)
        self.assertEqual(response["status"], "error")

    def test_missing_document_required_field_returns_contract_error(self):
        completed = self._run({
            "operation": "put",
            "root": self.root,
            "document": {"fam_ref": "fam:missing-fields"},
        })
        self.assertEqual(completed.returncode, 1)
        response = json.loads(completed.stdout)
        self.assertEqual(response["status"], "error")
        self.assertIn("contract-error", response["reason"])


if __name__ == "__main__":
    unittest.main()
