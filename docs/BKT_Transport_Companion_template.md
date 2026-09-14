# Transport technical companion for the Bukit Kototabang source studies

## Purpose and scope

This companion documents the numerical and meteorological basis of the two Bukit Kototabang (BKT) source studies: the 26 September 2019 forward source-influence case and the September–October 2019 methane inversion. It records what the HYSPLIT-STILT transport operator does and does not resolve, how its numerical completeness was established, how two meteorological drivers compare, and which configuration tests were run. Nothing here attributes methane or carbon dioxide to a source; the scientific results are in the two reports.

The companion has five parts. Section 1 describes the 2026 simulation revision that supplies the transport ensembles used by both reports. Section 2 documents the ERA5 driver and its comparison with GFS. Sections 3 and 4 retain the gas-independent transport benchmark and the full-ensemble domain correction that motivated the revision. Section 5 records the screen of a finer regional reanalysis that did not pass conversion.

## 1. Simulation revision campaign

The revision replaced the single-seed, 540-particle, regional-domain transport ensemble of the original inversion with the configuration in Table 1. Every run uses HYSPLIT 5.4.2 in STILT mode with the settings of the original studies: modified Richardson-number mixing depth with a 250 m minimum, Hanna turbulence, a variable Lagrangian timescale, a 30 m release above model ground unless stated, and hourly output on a 0.25° accumulation grid. Coefficients are normalized to the actual emitted count. Every run also records a fixed 1,000 m concentration layer above the STILT surface layer; the surface layer is bit-identical with and without it.

{{C_CAMPAIGN_TABLE}}

All {{C_RUNS}} runs completed and every run retained 100% of its particles at 120 h. The seed coefficient of variation of integrated sensitivity across the 52 inversion receptors has median {{C_SEED_CV_MED}}% and maximum {{C_SEED_CV_MAX}}% (Figure 1a). On the original domain, {{C_OLD_FAILS}} of the 52 hours had lost more than 5% of their particles; on the widened domain none does (Figure 1b).

![Numerical spread and particle retention.]({{RFIGURES}}/figure_R01_numerics_retention.png)

**Figure 1.** Seed coefficient of variation of integrated surface sensitivity for each of the 52 inversion receptor hours (a), and particle retention at 120 h on the original and widened meteorological domains (b).

{{C_SEED_TABLE}}

The 80 m release places the inlet at its true altitude above the nearest GFS grid-cell terrain of 816 m. At the four benchmark anchors it changes integrated sensitivity by a median factor of {{C_H80_MEDIAN}} (range {{C_H80_MIN}}–{{C_H80_MAX}}) with a cell-level spatial difference of {{C_H80_SPATIAL}}%, comparable to the seed-to-seed spatial difference of the benchmark controls (Figure 2a, Table 3). Release height is a few-percent effect at this station and does not need to be carried as a separate uncertainty term.

{{C_TERRAIN_TABLE}}

The afternoon runs at 05, 07 and 08 UTC combine with the 06 UTC ensemble mean into a 12:00–15:00 WIB window mean for each day (Figure 2b). Members of the window differ by a median {{C_WINDOW_CV}}% in integrated sensitivity over {{C_WINDOW_DAYS}} days, small against the day-to-day range, so a window mean is a stable receptor for a daytime-only inversion design.

![Release height and the afternoon window.]({{RFIGURES}}/figure_R02_release_height_afternoon_window.png)

**Figure 2.** Sensitivity ratio of the 80 m release to the 30 m release at the four anchors, three seeds each (a), and integrated sensitivity of the 05, 06, 07 and 08 UTC footprints with their 12:00–15:00 WIB window mean for each day of the study period (b).

Convective redistribution is not part of any run. HYSPLIT's Grell option requires convective mass-flux fields that neither the GFS nor the ERA5 archive carries, and the model reports convective mixing inactive in every log; the CAPE-threshold alternative in the benchmark produced no response for the same reason. All footprints in both reports therefore assume no parameterized convective venting, which is a material limitation in equatorial Sumatra.

## 2. Meteorological drivers

### GFS

The principal driver is NOAA's quarter-degree GFS archive in ARL format: three-hourly fields on 55 hybrid levels, concatenated from successive analysis and three-hour forecast cycles, cropped server-side to 50°–160° E, 40° S–30° N [3]. It is a pseudo-analysis rather than a homogeneous reanalysis.

### ERA5

ECMWF ERA5 [20] was obtained from the Copernicus Climate Data Store as hourly GRIB on 16 pressure levels from 1000 to 100 hPa with the surface analysis and accumulated-flux fields that HYSPLIT's converter expects, over 70°–140° E, 25° S–20° N, and converted with NOAA's `era52arl` utility. Two properties of the conversion matter scientifically. First, the pressure-level product gives the lowest layers at 925, 900 and 850 hPa above an 865 m station, coarser near the surface than the hybrid GFS levels. Second, ECMWF's accumulated sensible and latent heat fluxes are positive downward, whereas HYSPLIT's stability calculation takes them positive upward; the converter's stock field map only rescales them, and the sign was corrected in the map used here. With the stock map HYSPLIT received a strongly negative daytime heat flux, treated the daytime boundary layer as stable, and produced 1.3 to 3.8 times the GFS surface sensitivity; that artefact is documented so that it is not repeated, and no result in either report uses those files. The ERA5 footprint grid is 40° by 60°, inside the meteorological box; at the receptors compared below the GFS runs place no sensitivity outside it.

### Driver comparison at matched receptors

{{C_DRIVER_TABLE}}

At the four inversion anchors and the forward case, with seeds, particle counts, release height and STILT settings matched, ERA5 gives {{C_ERA5_RATIO_MIN}} to {{C_ERA5_RATIO_MAX}} times the GFS integrated surface sensitivity, with seed spread below 2% under both drivers. The cell-level absolute difference is {{C_ERA5_SPATIAL_MIN}} to {{C_ERA5_SPATIAL_MAX}}% of the GFS total: the two drivers place the footprint in largely different quarter-degree cells even where their regional shares agree. On 9 September 2019 the ERA5 boundary-layer height at BKT peaks at {{C_ERA5_PBLH}} m against {{C_GFS_PBLH}} m in GFS, and ERA5's model terrain at the station is {{C_ERA5_SHGT}} m against 816 m; a shallower mixed layer concentrates the same residence time into more surface sensitivity. The comparison quantifies transport uncertainty; it does not establish which driver is closer to the atmosphere, and the profile check in Section 3 applies to GFS only.

{{TRANSPORT_APPENDIX}}

{{BARRA_APPENDIX}}

<!-- pdf-pagebreak -->

## References

1. NOAA Air Resources Laboratory. *Configuring STILT options in HYSPLIT*. [Official model guidance](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html).
2. Lin, J. C., et al. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: The Stochastic Time-Inverted Lagrangian Transport (STILT) model. *Journal of Geophysical Research: Atmospheres*, 108(D16), 4493. [doi:10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161).
3. NOAA Air Resources Laboratory. *GFS quarter-degree meteorological archive: data and hybrid-level definitions*. [Archive documentation](https://www.ready.noaa.gov/data/archives/gfs0p25/readme_gfs0p25_info.txt).
4. European Commission Joint Research Centre. *EDGAR v8.0 greenhouse-gas emissions, monthly sectoral fluxes*. [Dataset and methodological documentation](https://edgar.jrc.ec.europa.eu/dataset_ghg80).
5. van der Werf, G. R., et al. (2025). Landscape fire emissions from the 5th version of the Global Fire Emissions Database (GFED5). *Scientific Data*, 12, 1870. [doi:10.1038/s41597-025-06127-w](https://www.nature.com/articles/s41597-025-06127-w). Daily GFED5.1 data and license: [GFED data portal](https://www.globalfiredata.org/data.html).
6. geoBoundaries. *gbOpen boundary data and API*. [Data access, source and license metadata](https://www.geoboundaries.org/api.html). Country polygons retain their individual source licenses; Indonesian boundaries use the established provincial geometry independently of this product.
7. NOAA Air Resources Laboratory. *Turbulence, stability and mixed-layer depth configuration*. [HYSPLIT user guide](https://www.ready.noaa.gov/hysplitusersguide/S625.htm).
8. Lin, J. C., and Gerbig, C. (2005). Accounting for the effect of transport errors on tracer inversions. *Geophysical Research Letters*, 32, L01802. [doi:10.1029/2004GL021127](https://doi.org/10.1029/2004GL021127).

{{INVERSION_REFERENCES}}

14. Bureau of Meteorology (2023). *Bureau of Meteorology Atmospheric high-resolution Regional Reanalysis for Australia, version 2 (BARRA2)*, model realization v1. [Dataset, doi:10.25914/1x6g-2v48](https://doi.org/10.25914/1x6g-2v48); [provider README and citation details](https://bom-opendata-climate.s3.amazonaws.com/BARRA2/README.txt). System description: Su, C.-H., et al. (2025), *The Australian regional atmospheric reanalysis system, version 2 - BARRA2*, Journal of Southern Hemisphere Earth Systems Science, 75, ES25032, [doi:10.1071/ES25032](https://doi.org/10.1071/ES25032). Bibliographic details are supplied by the dataset provider; no unverified paper-specific findings are used here.
15. NCI and Bureau of Meteorology. *Known Issues - BOM BARRA2 (ob53)*. [Provider-maintained data-quality notices](https://opus.nci.org.au/spaces/NDP/pages/264241304/Known+Issues+-+BOM+BARRA2+ob53), accessed 6 September 2026.
16. NOAA Air Resources Laboratory. *Meteorology: ARL data format*. [Required fields, packing and vertical-resolution guidance](https://www.ready.noaa.gov/hysplitusersguide/S141.htm), accessed 6 September 2026.
17. NOAA Air Resources Laboratory. *Variables not set in the graphical interface*. [CAPE, convection, random-seed and near-surface input configuration](https://www.ready.noaa.gov/hysplitusersguide/S640.htm), accessed 6 September 2026.
18. NOAA National Centers for Environmental Information. *Integrated Global Radiosonde Archive, version 2.2*. [Dataset scope, quality control and limitations](https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive), accessed 6 September 2026.
19. NOAA National Centers for Environmental Information (2023). *IGRA v2.2 sounding-data format description*. [Time fields, units, quality flags and station-location conventions](https://www.ncei.noaa.gov/pub/data/igra/data/igra2-data-format.txt), dated 19 January 2023, accessed 6 September 2026.

Boundary attribution: Malaysia, Cambodia and Thailand derive from © OpenStreetMap contributors and Wambacher (ODbL 1.0); Myanmar from OpenStreetMap (CC BY-SA 2.0 as stated by the provider); Singapore from the Urban Redevelopment Authority, derived from subnational boundaries (ODbL 1.0); Vietnam from geoBoundaries/Wikipedia (CC BY 4.0); the Philippines from OCHA Philippines and the National Mapping and Resource Information Authority (CC BY 3.0 IGO); Brunei from Wikimedia Commons (public domain). These are provider-reported source licenses, not a claim of uniform official status.
20. Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146, 1999–2049. [doi:10.1002/qj.3803](https://doi.org/10.1002/qj.3803).
21. Stein, A. F., et al. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. *Bulletin of the American Meteorological Society*, 96, 2059–2077. [doi:10.1175/BAMS-D-14-00110.1](https://doi.org/10.1175/BAMS-D-14-00110.1).
