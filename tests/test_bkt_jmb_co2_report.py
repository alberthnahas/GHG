from __future__ import annotations
import sys, unittest
from pathlib import Path
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a94_co2_figures as F  # noqa: E402
import a95_bkt_jmb_co2_report as R  # noqa: E402


class FigureHelperTests(unittest.TestCase):
    def test_gapped_breaks_only_across_a_gap(self) -> None:
        frame = pd.DataFrame(dict(time_utc=pd.to_datetime(["2023-12-01", "2023-12-02", "2023-12-12", "2023-12-13"]),
                                  value=[1., 2., 3., 4.]))
        out = F.gapped(frame, ("value",))
        self.assertEqual(len(out), 5)
        blank = out[out.value.isna()]
        self.assertEqual(len(blank), 1)
        self.assertTrue(pd.Timestamp("2023-12-02") < blank.time_utc.iloc[0] < pd.Timestamp("2023-12-12"))
        self.assertTrue(out.time_utc.is_monotonic_increasing)

    def test_gapped_leaves_consecutive_days_alone(self) -> None:
        frame = pd.DataFrame(dict(time_utc=pd.date_range("2023-12-01", periods=4, freq="D"), value=[1., 2., 3., 4.]))
        self.assertEqual(len(F.gapped(frame, ("value",))), 4)

    def test_head_refuses_text_that_would_overflow_the_page(self) -> None:
        fig = plt.figure(figsize=(7.2, 4.))
        F.head(fig, "A short title", "A short highlight line")
        with self.assertRaises(ValueError):
            F.head(fig, "T" * (F.TITLE_CHARS + 1), "fine")
        with self.assertRaises(ValueError):
            F.head(fig, "fine", "ok\n" + "H" * (F.HIGHLIGHT_CHARS + 1))
        plt.close(fig)


class ReportTests(unittest.TestCase):
    def test_round_selects_its_periods_and_cases(self) -> None:
        self.assertEqual(R.periods(R.ROUND), ("2023", "2024", "all"))
        self.assertEqual(R.periods(R.FALLBACK), ("2023",))
        self.assertEqual(R.cases(R.ROUND), ("best_all", "best_all_bkt_background"))
        for case in R.cases(R.ROUND) + R.cases(R.FALLBACK):
            self.assertIn(case, R.VARIANT_LABELS)

    def test_every_template_token_has_a_label_or_is_produced(self) -> None:
        template = R.TEMPLATE.read_text()
        self.assertNotIn("—", template)
        tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template))
        self.assertTrue(tokens, "template carries tokens")
        self.assertTrue(all(name.startswith("C_") for name in tokens))

    def test_need_raises_with_the_claim(self) -> None:
        R.need(True, "a claim that holds")
        with self.assertRaises(ValueError) as caught:
            R.need(False, "a claim that does not")
        self.assertIn("a claim that does not", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
