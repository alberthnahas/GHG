from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a82_bkt_reports as R  # noqa: E402


class RenumberTests(unittest.TestCase):
    def test_captions_and_references_renumber_by_order(self) -> None:
        text = ("see Figure 13 and Table 101.\n\n![a](x.png)\n\n**Figure 13.** first.\n\n**Table 101. Head.**\n\n| a |\n\n"
                "![b](y.png)\n\n**Figure 2.** second (Figures 13 and 2).\n\n**Table 7. Other.**\n")
        out = R.renumber(text)
        self.assertIn("**Figure 1.** first", out); self.assertIn("**Figure 2.** second (Figures 1 and 2)", out)
        self.assertIn("see Figure 1 and Table 1.", out); self.assertIn("**Table 2. Other.**", out)

    def test_templates_exist_for_every_document(self) -> None:
        for stem, template in R.DOCS.items():
            self.assertTrue((ROOT / "docs" / template).exists(), template)


if __name__ == "__main__":
    unittest.main()
