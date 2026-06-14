import unittest
from argparse import Namespace

from dzcz_merchant_ops.cli import built_in_workflows, command_workflow_show


class BuiltInWorkflowTests(unittest.TestCase):
    def test_fixed_bilibili_like_workflow_does_not_require_ai(self) -> None:
        workflows = built_in_workflows()

        workflow = workflows["bilibili.video.like.fixed"]

        self.assertEqual(workflow["platform"], "bilibili")
        self.assertEqual(workflow["operation"], "video.like")
        self.assertEqual(workflow["required_inputs"], ["video_url"])
        self.assertFalse(workflow["requires_ai"])
        self.assertEqual(workflow["status"], "stable")
        self.assertEqual(workflow["executor"], "agent_browser.deterministic")
        self.assertEqual(workflow["session_policy"], "reuse_ops_session")
        self.assertEqual(workflow["success_condition"]["json_path"], "operation_result.confirmed")
        self.assertTrue(workflow["failure_hints"])

    def test_workflow_show_returns_structured_fixed_workflow(self) -> None:
        payload = command_workflow_show(
            Namespace(
                data_dir=".",
                workflow_id="bilibili.video.like.fixed",
            )
        )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["workflow"]["workflow_id"], "bilibili.video.like.fixed")
        self.assertEqual(payload["workflow"]["status"], "stable")
        self.assertEqual(payload["workflow"]["open_url_input"], "video_url")
        self.assertIn("operation_result.after.liked", payload["workflow"]["success_condition"]["description"])


if __name__ == "__main__":
    unittest.main()
