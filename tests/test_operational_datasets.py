from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a106_dataset_registry as R  # noqa: E402
import a99_operational_inversion as V  # noqa: E402
import a89_bkt_jmb_co2 as C  # noqa: E402


class RegistryTests(unittest.TestCase):
    def test_every_dataset_declares_what_it_is_for(self) -> None:
        for dataset in R.REGISTRY:
            self.assertTrue(dataset.name and dataset.role)
            self.assertIn(dataset.kind, {"stations", "grid", "count", "table", "raster", "geometry"})

    def test_required_datasets_cover_both_gases_and_the_transport(self) -> None:
        roles = " ".join(d.role for d in R.REGISTRY if d.required)
        for needed in ("observations", "meteorology", "anthropogenic CH4", "fossil CO2", "boundary"):
            self.assertIn(needed.split()[-1], roles, f"no required dataset covers {needed}")

    def test_a_json_file_counts_as_its_own_provenance(self) -> None:
        """The meteorology records are json; they do not need a json sidecar."""
        met = [d for d in R.REGISTRY if d.pattern.endswith("_gfs0p25.json")]
        self.assertTrue(met)
        for dataset in met:
            result = R.check_one(dataset)
            if result["files"]:
                self.assertEqual(result["provenance"], result["files"])

    def test_the_verdict_blocks_when_a_required_dataset_fails(self) -> None:
        broken = R.Dataset("invented", "test", "data/does/not/exist/*.nc", True, "count")
        self.assertEqual(R.check_one(broken)["status"], "missing")


class SamplerTests(unittest.TestCase):
    """The reported fit is sampled; the approximation is only allowed where the mode is enough."""

    def setUp(self) -> None:
        V.LOCAL_INVENTORY = "primap"
        self.frame = V.aggregate(V.ch4_frame(), V.CH4, "daily")
        self.kappa = V.calibrate(self.frame, V.CH4)

    def tearDown(self) -> None:
        V.LOCAL_INVENTORY = ""

    def test_the_sampled_fit_reports_its_convergence(self) -> None:
        fit = V.solve(self.frame, V.CH4, self.kappa, sample=True)
        self.assertLessEqual(fit["convergence"]["rhat"], 1.01)
        self.assertGreaterEqual(fit["convergence"]["ess"], 1000)
        self.assertGreater(fit["convergence"]["draws"], 1000)

    def test_the_approximation_agrees_on_the_mode_but_not_the_tail(self) -> None:
        """Why the reported fit is sampled: the medians match, the upper bounds do not."""
        fast = V.solve(self.frame, V.CH4, self.kappa, sample=False)
        sampled = V.solve(self.frame, V.CH4, self.kappa, sample=True)
        ns = fast["nsource"]
        for j in range(ns):
            self.assertLess(abs(np.exp(fast["theta"][j]) - np.exp(sampled["theta"][j]))
                            / np.exp(sampled["theta"][j]), 0.25, "modes disagree")
        widest = max(np.exp(fast["quantiles"][1][j]) / np.exp(sampled["quantiles"][1][j]) for j in range(ns))
        self.assertGreater(widest, 1.1, "the approximation no longer overstates the upper bound; revisit the choice")

    def test_cross_validation_uses_the_mode_only(self) -> None:
        """Skill must not depend on the sampler, or the two paths would disagree."""
        predictions = V.cross_validate(self.frame, V.CH4, self.kappa)
        self.assertGreater(len(predictions), 0)
        self.assertTrue(np.isfinite(predictions.posterior).all())
