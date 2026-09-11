<!-- pdf-pagebreak -->

## Appendix. Full-ensemble domain correction and prior methane-budget convergence

{{D_DECISION}}

The extension reruns all 52 available twice-daily receptors from 9 September to 6 October 2019 with a 50°–160° E, 40° S–30° N meteorological crop and a 60° by 100° footprint grid [3]. It preserves the original five-day transport physics and actual-emitted-particle normalization. This is a matched correction configuration, not a pure domain perturbation: the larger meteorological extraction is repacked, so small shared-field differences accompany the removal of boundary truncation. No gas value selected a rerun, and no inversion was refitted.

![Full-ensemble particle retention and surface-flux sensitivity under the original and widened domains.]({{D_FIGURES}}/domain_ensemble.png)

**Figure 26.** Original and widened-domain diagnostics for 52 BKT receptors, 9 September–6 October 2019. Panel (a) shows the active fraction of the actual emitted particles; the horizontal line is the pre-existing 95% eligibility screen. Panel (b) compares integrated surface-flux sensitivity for the same receptor hour. Color denotes whether the original run passed that screen. Values are forward-model diagnostics, not measures of atmospheric accuracy.

The paired and sample-composition terms answer different questions. For a metric $X$, the reported total change is decomposed exactly as

$$
\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{original,retained}}
=\left(\overline{X}_{\mathrm{wide,retained}}-\overline{X}_{\mathrm{original,retained}}\right)
+\left(\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{wide,retained}}\right).
$$

The first term is a same-hour paired configuration change. The second is the composition change from recovering hours that the original domain excluded. Pointwise 95% intervals use 5,000 circular three-day block resamples of receptor dates; they describe short-record sampling variability and are not atmospheric-model uncertainty.

**Table 21. Original-to-wide decomposition across the 52-hour BKT ensemble.**

{{D_DECOMPOSITION_TABLE}}

### Selection pattern in the observed gases

{{D_SELECTION_INTERPRETATION}}

![Observed BKT gas concentrations in hours retained and excluded by the original transport-domain screen.]({{D_FIGURES}}/selection_concentrations.png)

**Figure 27.** Quality-controlled BKT CO₂, CH₄ and CO for hours retained by the original 95% particle screen and hours recovered by widening the transport domain. Points are observed concentrations; boxes show medians and interquartile ranges. The grouping is determined by modeled particle retention, not concentration. Differences therefore diagnose sample composition and do not imply that widening a domain changes an observation or that transport loss causes the concentration contrast.

**Table 22. Observed concentration difference between recovered and originally retained hours.**

{{D_OBSERVED_TABLE}}

Calendar-month, WIB clock-period and GFS 10 m wind strata are reported as short-record diagnostics rather than seasonal or observational meteorology. {{D_STRATA_INTERPRETATION}}

### Surface contribution and endpoint-background convergence

{{D_CONVERGENCE_INTERPRETATION}}

![Representative methane surface, endpoint-background and combined prior-budget responses by domain and duration.]({{D_FIGURES}}/budget_convergence.png)

**Figure 28.** Prior methane-budget components for five pre-declared BKT receptor hours at 72, 120 and 168 hours backward. Thin lines are individual receptors and thick lines are cross-case medians; blue denotes the original domain and orange the widened domain. Surface contribution combines prior anthropogenic, wetland, termite, geological and non-crop-fire methane, less the positive soil-uptake magnitude [4, 5]. Background is the equal-particle mean CarbonTracker-CH4 value at active trajectory endpoints [9]. The sum can appear stable when its components offset, so the three panels must be read together. These representative cases were selected by clock period, model wind quadrant and original retention—not gas residual—and are not a random or seasonally representative sample.

**Table 23. Absolute duration increments across the five representative methane-budget cases.**

{{D_CONVERGENCE_TABLE}}

CarbonTracker-CH4 assimilates BKT observations, so its endpoint mean is a physically informed boundary estimate rather than an independent test of the BKT record. The source fields are prior inventories or models, and the small convergence matrix tests numerical sensitivity only. Accordingly, this extension can identify domain truncation, selection effects and component instability; it cannot validate atmospheric accuracy, attribute measured methane to a source, or support a revised emissions inversion.
