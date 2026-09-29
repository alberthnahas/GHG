from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a103_sector_matching as M  # noqa: E402
import a100_local_inventory as L  # noqa: E402


class RuleTests(unittest.TestCase):
    def test_realistic_indonesian_labels_resolve_without_any_model(self) -> None:
        cases = {"Pembangkitan Listrik": "1A1", "Industri Pengolahan": "1A2", "Transportasi Darat": "1A3",
                 "Rumah Tangga": "1A4", "Emisi Fugitif Migas": "1B", "Proses Industri": "2",
                 "Peternakan Sapi Perah": "3A", "Budidaya Padi Sawah": "3C",
                 "Lahan Gambut Terdrainase": "3B1", "Kebakaran Hutan dan Lahan": "3B2",
                 "Pengelolaan Limbah Padat Domestik": "4"}
        table = M.match(list(cases), use_jev=False).set_index("sector_name")
        for name, code in cases.items():
            self.assertEqual(table.loc[name, "ipcc_code"], code, f"{name} mapped to {table.loc[name, 'ipcc_code']}")
            self.assertEqual(table.loc[name, "method"], "rule")

    def test_case_and_spacing_do_not_matter(self) -> None:
        for spelling in ("PEMBANGKITAN LISTRIK", "pembangkitan   listrik", " Pembangkitan Listrik "):
            self.assertEqual(M.match_by_rule(spelling)[0], "1A1")

    def test_an_unrecognised_name_is_reported_not_guessed(self) -> None:
        table = M.match(["Sesuatu yang tidak jelas"], use_jev=False)
        self.assertEqual(table.method.iloc[0], "unresolved")
        self.assertEqual(table.ipcc_code.iloc[0], "")
        self.assertEqual(table.confidence.iloc[0], 0.0)

    def test_every_rule_targets_a_category_the_crosswalk_knows(self) -> None:
        """A mapping to a code the engine cannot use would fail later, not here."""
        for _, code, _ in M.RULES:
            self.assertIn(code, L.CROSSWALK, f"rule maps to {code}, which the crosswalk does not define")

    def test_land_use_rules_reach_the_folu_categories(self) -> None:
        for code in ("3B", "3B1", "3B2"):
            self.assertIn(code, L.FOLU_PROXY, f"{code} must be carried by the FOLU proxy")

    def test_the_model_is_never_consulted_when_rules_suffice(self) -> None:
        calls = []
        original = M.match_by_jev
        M.match_by_jev = lambda names: calls.append(names) or {}
        try:
            M.match(["Pembangkitan Listrik", "Transportasi Darat"], use_jev=True)
        finally:
            M.match_by_jev = original
        self.assertEqual(calls, [[]], "the judgment was offered names the rules had already resolved")

    def test_a_low_confidence_judgment_is_not_applied(self) -> None:
        original = M.match_by_jev
        M.match_by_jev = lambda names: {}                 # below threshold judgments are dropped upstream
        try:
            table = M.match(["Tidak dikenal"], use_jev=True)
        finally:
            M.match_by_jev = original
        self.assertEqual(table.method.iloc[0], "unresolved")

    def test_the_threshold_is_stated_and_strict(self) -> None:
        self.assertGreaterEqual(M.JEV_THRESHOLD, 0.6)
