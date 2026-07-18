import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowContractTests(unittest.TestCase):
    def test_normal_run_is_interactive(self):
        text = (ROOT / "article-pipeline" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认交互模式", text)
        self.assertIn("直接跑完", text)
        self.assertNotIn("跳过确认直接跑完", text)
        self.assertNotIn("自动选最佳选题，直接进入角度", text)

    def test_three_gates_are_named_in_main_prompt(self):
        text = (ROOT / "article-pipeline" / "references" / "main-agent-prompt.md").read_text(encoding="utf-8")
        for gate in ("热点与选题确认", "角度确认", "定调与文章计划确认"):
            self.assertIn(gate, text)

    def test_authenticated_xhs_is_forbidden(self):
        text = (ROOT / "sourcing-hotspots" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("禁止个人小红书登录态", text)
        self.assertIn("full_hotspot_run.py", text)
        self.assertNotIn("小红书搜索（≥5个关键词", text)

    def test_hotspot_prompt_does_not_require_comment_crawling(self):
        text = (ROOT / "sourcing-hotspots" / "references" / "hotspot-agent-prompt.md").read_text(encoding="utf-8")
        self.assertIn("热点阶段禁止深挖评论", text)
        self.assertNotIn("必须引用具体的评论或讨论内容", text)

    def test_hotspot_prompt_has_single_source_of_truth(self):
        pointer = (ROOT / "article-pipeline" / "references" / "hotspot-agent-prompt.md").read_text(encoding="utf-8")
        self.assertIn("../../sourcing-hotspots/references/hotspot-agent-prompt.md", pointer)

    def test_screening_is_code_model_code(self):
        text = (ROOT / "screening-topics" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("代码预筛短名单", text)
        self.assertIn("模型只负责", text)
        self.assertIn("finalize_screening.py", text)

    def test_product_flow_does_not_use_xhs_cookie(self):
        text = (ROOT / "xhs-product-recommendation" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("禁止使用个人小红书 Cookie", text)
        self.assertNotIn("小红书用户实拍/评价（用cookie访问）", text)


if __name__ == "__main__":
    unittest.main()
