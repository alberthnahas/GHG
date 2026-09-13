import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/run/media/workstation-llm/HDD2/GHG_Analysis";
const TMP = `${ROOT}/ggmt_poster`;
const OUT = `${ROOT}/GGMT_2026_A0_GHG_Monitoring_Poster_v11.pptx`;
const INVERSION_FIGURE = `${ROOT}/outputs/poster/poster_inversion_revision_tuned.png`;

async function bytes(path) {
  return new Uint8Array(await fs.readFile(path));
}

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, name, value, x, y, w, h, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontFamily: "Arial",
    fontSize: 32,
    color: "#26363C",
    verticalAlignment: "top",
    ...style,
  };
  return shape;
}

function addRule(slide, name, x, y, w, color = "#147783", height = 4) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width: w, height },
    fill: color,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addSection(slide, name, title, x, y, w) {
  addText(slide, `${name}-title`, title, x, y, w, 58, {
    fontSize: 44,
    bold: true,
    color: "#0B4F5C",
    verticalAlignment: "middle",
  });
  return y + 80;
}

function addCard(slide, name, x, y, w, h, fill = "#F3F7F8") {
  return slide.shapes.add({
    geometry: "roundRect",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
    borderRadius: 22,
  });
}

function addBadge(slide, name, label, x, y, size = 62, fill = "#B64B2A") {
  slide.shapes.add({
    geometry: "ellipse",
    name: `${name}-circle`,
    position: { left: x, top: y, width: size, height: size },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(slide, `${name}-label`, label, x, y, size, size, {
    fontSize: 32,
    bold: true,
    color: "#FFFFFF",
    alignment: "center",
    verticalAlignment: "middle",
  });
}

function addCaption(slide, name, value, x, y, w) {
  addText(slide, name, value, x, y, w, 36, {
    fontSize: 20,
    italic: true,
    color: "#52676C",
  });
}

async function addImage(slide, name, path, alt, x, y, w, h) {
  slide.images.add({
    blob: await bytes(path),
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left: x, top: y, width: w, height: h },
  });
}

async function main() {
  await fs.mkdir(`${TMP}/render-v11`, { recursive: true });
  const deck = Presentation.create({ slideSize: { width: 3179, height: 4494 } });
  const slide = deck.slides.add();
  slide.background.fill = "#FFFFFF";

  const margin = 150;
  const gap = 72;
  const colW = 911;
  const x1 = margin;
  const x2 = margin + colW + gap;
  const x3 = margin + 2 * (colW + gap);
  const fullW = 2879;

  slide.shapes.add({ geometry: "rect", name: "header-band", position: { left: 0, top: 0, width: 3179, height: 440 },
    fill: "#0B4F5C", line: { style: "solid", fill: "none", width: 0 } });
  addCard(slide, "logo-tile", 150, 80, 280, 280, "#FFFFFF");
  await addImage(slide, "bmkg-logo", `${TMP}/assets/bmkg-logo.png`, "Official BMKG logo", 168, 98, 244, 244);
  addText(slide, "title", "Strengthening Greenhouse-Gas Monitoring in the Maritime Continent Through Lessons from Five Indonesian Observation Sites", 490, 40, 2540, 200, {
    fontSize: 66,
    bold: true,
    color: "#FFFFFF",
    verticalAlignment: "middle",
  });
  addText(slide, "authors", "Alberth Nahas¹ · Ardhasena Sopaheluwakan¹ · Sugeng Nugroho² · Darmadi³ · Asep Firman Ilahi⁴ · Budi Satria⁵", 490, 248, 2540, 48, {
    fontSize: 30,
    bold: true,
    color: "#FFFFFF",
  });
  addText(slide, "affiliation", "¹Department of Climatology, BMKG, Jakarta · ²Stasiun Pemantau Atmosfer Global Bukit Kototabang, West Sumatra · ³Stasiun Klimatologi Jambi, Jambi · ⁴Stasiun Pemantau Atmosfer Global Lore Lindu Bariri, Central Sulawesi · ⁵Stasiun Pemantau Atmosfer Global Puncak Vihara Klademak Sorong, Southwest Papua", 490, 300, 2000, 84, {
    fontSize: 21,
    color: "#D6E9ED",
  });
  addText(slide, "contact", "Contact: alberth.nahas@bmkg.go.id", 490, 386, 1200, 40, {
    fontSize: 22,
    bold: true,
    color: "#FFFFFF",
  });
  addText(slide, "conference", "GGMT 2026\nStellenbosch, South Africa\n21 to 24 September 2026", 2530, 300, 500, 130, {
    fontSize: 22,
    color: "#D6E9ED",
    alignment: "right",
  });

  let y = addSection(slide, "introduction", "Introduction", x1, 470, colW * 2 + gap);
  addText(slide, "introduction-text", "The Maritime Continent is a major tropical interface between land, ocean, and atmosphere. Strong monsoon circulation connects the Northern and Southern Hemispheres, while tropical forests, peatlands, biomass burning, rapidly growing cities, and surrounding seas generate greenhouse-gas signals over a wide range of spatial and temporal scales. Measurements made in Indonesia are therefore important for understanding both regional sources and sinks and the transport of globally mixed air.\n\nLong-term observations remain sparse compared with those at northern mid-latitudes. This limits direct evaluation of tropical background concentrations, seasonal exchange, fire episodes, urban enhancement, and changes in interhemispheric gradients. It also increases the risk that measurements from contrasting environments are interpreted as though they represented the same atmospheric population.\n\nBMKG observations from five sites provide complementary perspectives: a long-running remote mountain station, a lowland peat environment, a megacity core, a montane rainforest, and a coastal city. Continuous CO₂, CH₄, and CO measurements are evaluated together with co-located NOAA flasks and global reference stations. This study asks what the combined record reveals about background structure, surface influence, fire, and long-term change, and how far a single station can be taken from concentrations toward sources when transport is modeled explicitly. The answers define what a robust Maritime Continent monitoring network can and cannot yet deliver.", x1, y, colW * 2 + gap, 470, {
    fontSize: 25,
  });

  y = addSection(slide, "methods", "Methods", x3, 470, colW);
  addText(slide, "methods-text", "Data. Quality-controlled hourly CO₂, CH₄, and CO from five BMKG sites, NOAA flasks at Bukit Kototabang, and global reference stations.\n\nDiurnal and nocturnal analysis. Local-time medians, amplitudes, and morning decay characterized boundary-layer influence; nocturnal CO₂ slopes used stratified nights and 100 to 400 m stable layers.\n\nValidation, fire, and trends. Same-hour flask comparisons; CO enhancement, CH₄:CO ratios, and plume clearance; seasonal adjustment and Theil-Sen slopes.\n\nTransport and inversion. Five-day HYSPLIT-STILT footprints on GFS 0.25° meteorology, EDGAR, GFED, and wetland priors, CarbonTracker-CH₄ boundary values, and a positive-emission Bayesian fit of four regional multipliers with a chi-square-consistent error model, evaluated on withheld hours.", x3, y, colW, 470, {
    fontSize: 25,
  });

  y = addSection(slide, "coverage", "Network coverage and observational context", x1, 1040, colW * 2 + gap);
  await addImage(slide, "coverage-figure", `${ROOT}/figures/f1_coverage_timebase.png`, "Station coverage and local-time alignment", x1, y, colW, 305);
  addCaption(slide, "coverage-caption", "Figure 1. Observation coverage and local-time alignment across the five BMKG sites.", x1, y + 307, colW);
  addText(slide, "coverage-text", "Record length varies substantially across the network. Bukit Kototabang supplies the 24-year observational anchor, while Jambi and Kemayoran begin in late 2023. Bariri and Sorong provide intermediate-length records beginning in 2021. This unequal temporal support means that site comparisons must distinguish short process studies from climatological or trend evidence.\n\nThe lower panels illustrate why local-time alignment is essential. Before correction, the archived daily minima occur at inconsistent hours. After conversion, all five stations place the CO₂ minimum within the expected afternoon mixed-layer period. The agreement provides an internal physical check that complements external flask validation.", x2, y + 4, colW, 360, {
    fontSize: 25,
  });

  y = addSection(slide, "sites", "Five observation sites", x3, 1040, colW);
  await addImage(slide, "site-map", `${TMP}/assets/five_site_map.png`, "Map of the five Indonesian greenhouse-gas observation sites", x3, y, colW, 325);
  addCaption(slide, "site-map-caption", "Figure 2. Locations and environmental profiles of the five observation sites.", x3, y + 327, colW);
  addText(slide, "results-heading", "Results", margin, 1490, fullW, 70, {
    fontSize: 50,
    bold: true,
    color: "#0B4F5C",
  });

  const panels = [
    { title: "1. Independent flasks validate the record", figure: `${ROOT}/outputs/poster/poster_f2_flask_validation.png`, alt: "Independent flask validation", caption: "Figure 3. Co-located flasks validate the continuous CO₂ and CH₄ record.",
      text: "Correcting the time base changes flask-minus-in-situ CO₂ from −8.50 ppm at r = 0.28 to +0.31 ppm at r = 0.77. CH₄ correlation increases from 0.74 to 0.98. The agreement demonstrates that an independent co-located reference can anchor the continuous observations to a traceable measurement scale.\n\nAgreement across both CO₂ and CH₄ provides confidence that differences subsequently observed among Indonesian and global sites represent atmospheric structure rather than an uncontrolled instrumental offset. The flask comparison therefore establishes the foundation for interpreting background gradients, seasonal cycles, and long-term changes across the network." },
    { title: "2. Diurnal cycles show distinct site functions", figure: `${ROOT}/outputs/poster/poster_f6_diurnal.png`, alt: "Diurnal greenhouse-gas cycles across five sites", caption: "Figure 4. Median diurnal cycles and amplitudes reveal contrasting site functions.",
      text: "All sites show a daytime reduction as the boundary layer deepens, but the magnitude and tracer composition differ sharply. Kemayoran has the strongest CH₄ and CO amplitudes, Jambi has the largest CO₂ amplitude, and Bukit Kototabang has a smaller regional-background cycle. These contrasts show that site setting controls the processes represented by each record.\n\nMorning boundary-layer erosion occurs with a similar 1.9 to 2.4 hour timescale at all five sites. The common timing reflects shared atmospheric physics, while the differing amplitudes retain information about local sources and sinks." },
    { title: "3. Nocturnal build-up constrains surface flux", figure: `${ROOT}/outputs/poster/poster_f12_nocturnal_flux.png`, alt: "Nocturnal carbon dioxide accumulation and implied flux", caption: "Figure 5. Nocturnal CO₂ accumulation and flux ranges for assumed stable-layer depths.",
      text: "On well-stratified nights, median CO₂ accumulation ranges from about 1.6 to 4.1 ppm h⁻¹ across the five sites. Jambi has the largest increase, while the coastal and montane sites have smaller rates. This common analysis converts each station into a natural chamber for comparing near-surface carbon influence under stable conditions.\n\nThe inferred absolute flux depends on the assumed stable-layer depth, but the relative contrast is robust. Jambi's respiration signal is about 1.9 times the forest reference and strengthens during the dry season, consistent with disturbed peatland behavior. Bariri remains much more seasonally stable, indicating a different ecosystem response despite similar tropical forcing." },
    { title: "4. Fire influence is episodic and complex", figure: `${ROOT}/outputs/poster/poster_f16_growth_fire.png`, alt: "Growth anomalies, fire fingerprints, and plume clearance", caption: "Figure 6. CO growth, fire-season composition, and plume-clearance behavior.",
      text: "Bukit Kototabang records intense CO enhancements during major burning seasons, including an October 2015 monthly median of 1,493 ppb. Interannual CO₂ growth anomalies do not retain a consistent fire signal, so the clearest evidence is found in short-lived combustion tracers and their ratios rather than in annual CO₂ growth.\n\nCH₄ to CO enhancement ratios distinguish burning-season composition, while plume anomalies return toward background within 12 to 44 days. The 2015 event is exceptional in duration, whereas 2014 ranks higher by peak intensity. Fire influence is therefore multidimensional. Concentration, duration, composition, and clearance time describe different properties of an event and should not be treated as interchangeable severity measures." },
    { title: "5. A single station constrains methane sources", figure: INVERSION_FIGURE, alt: "Methane footprint, posterior emission multipliers, and withheld-hour evaluation", caption: "Figure 7. Mean footprint, prior and posterior methane multipliers, and withheld-hour error.",
      text: "Five-day HYSPLIT-STILT footprints on a widened domain link all 52 twice-daily BKT hours in September to October 2019 to regional methane sources, three 2,000-particle seeds per hour. Inventory plus modeled background over-predicts the observations by about 76 ppb. With the transport-error covariance tuned to a unit reduced chi-square, the positive-emission fit scales anthropogenic emissions to 0.37 within 500 km and 0.24 beyond, wetlands to 0.43 and fires to 0.68; only the fire interval reaches the inventory value, at 1.00. Withheld hours are predicted to 25 ppb RMSE against 29 ppb for a background-only baseline.\n\nThe constraint is conditional: quarter-degree GFS meteorology without resolved convection, CarbonTracker boundaries that assimilate BKT, and a near field of a few inventory cells whose own multiplier, 0.52 (0.18 to 1.18), includes unity. Within those limits, EDGAR and wetland-model priors over-predict methane here by a factor of two to four." },
    { title: "6. Long records resolve gradients and growth", figure: `${ROOT}/outputs/poster/poster_f24_trends_gradients.png`, alt: "Growth acceleration, hemispheric gradients, and carbon monoxide cycling", caption: "Figure 8. Long-term acceleration, hemispheric gradients, and regional CO cycling.",
      text: "Across 2015 to 2025, Bukit Kototabang flasks average 408.5 ppm CO₂, 5.5 ppm below Mauna Loa and 1.4 ppm below the South Pole: a regional background minimum seen in independent flasks, not an in-situ offset. The long record also resolves acceleration in several long-lived gases. CO behaves differently: its clean background is approximately stable, while roughly half of its seasonal cycle is generated regionally during two burning periods.\n\nThe post-2014 methane increase is strongly expressed in the tropical record, and N₂O acceleration is nearly synchronous across latitudes. SF₆ rises steadily and lags Barrow by 6.7 months while leading the South Pole by 9.0 months, a 15.9-month pole-to-pole progression that makes it the transport reference for the other species." },
  ];
  const columns = [x1, x2, x3];
  const pad = 26;
  for (const [i, p] of panels.entries()) {
    const x = columns[i % 3] + pad;
    const inner = colW - 2 * pad;
    const top = i < 3 ? 1590 : 2500;
    const textH = i < 3 ? 400 : 450;
    const cardH = i < 3 ? 890 : 940;
    addCard(slide, `r${i + 1}-card`, columns[i % 3], top - 22, colW, cardH);
    addBadge(slide, `r${i + 1}-badge`, String(i + 1), x, top + 6);
    addText(slide, `r${i + 1}-title`, p.title.replace(/^\d+\. /, ""), x + 80, top, inner - 80, 78, {
      fontSize: 32, bold: true, color: "#B64B2A", verticalAlignment: "middle",
    });
    await addImage(slide, `r${i + 1}-figure`, p.figure, p.alt, x, top + 84, inner, 320);
    addCaption(slide, `r${i + 1}-caption`, p.caption, x, top + 408, inner);
    addText(slide, `r${i + 1}-text`, p.text, x, top + 450, inner, textH, { fontSize: 25 });
  }

  y = addSection(slide, "discussion", "Discussion", x1, 3470, colW);
  addText(slide, "discussion-text", "The five stations form a network because their atmospheric roles are complementary, not because they measure identical air. Bukit Kototabang provides the longest record, external flask comparison, and sensitivity to interhemispheric transport. Jambi and Bariri contrast disturbed peatland with montane rainforest. Kemayoran resolves urban combustion and methane influence, while Sorong samples a coastal marine setting.\n\nThree principles follow. Calibration and scale propagation require independent standards. Metadata errors can alter physical interpretation as strongly as instrument bias. Continuous multi-species observations are necessary to distinguish transport, ecosystem exchange, combustion, and sampling effects.\n\nThe analysis also demonstrates the importance of preserving negative and conditional results. Fire years do not produce a consistent CO₂ growth anomaly, and absolute nocturnal flux remains sensitive to unmeasured boundary-layer depth. These findings do not reduce the network's value. They define which questions the observations can answer reliably and which require additional measurements. Regional interpretation is strongest when tracer behavior, atmospheric timing, and site context agree.\n\nThe methane inversion shows how far concentrations can be pushed toward sources today. Explicit transport turns a single station into a quantitative inventory test, and with a consistent error model the fit outperforms a fitted background on withheld hours. The answer remains conditional on meteorology, boundary values, and near-field inventory allocation. Representativeness matters in the same way: afternoon statistics, full-day means, and nocturnal accumulation describe different atmospheric states and are not interchangeable.", x1, y, colW, 920, {
    fontSize: 25,
  });

  addCard(slide, "conclusions-card", x2 - 26, 3458, colW + 52, 962, "#E6F0F2");
  y = addSection(slide, "conclusions", "Conclusions", x2, 3470, colW);
  addText(slide, "conclusions-text", "This assessment shows that Indonesia already has the foundations of a scientifically valuable Maritime Continent greenhouse-gas network. Its strongest evidence comes from the combination of continuous observations, independent flask measurements, and physically interpretable differences among sites.\n\nThe network can quantify background gradients, transport timing, urban and ecosystem influence, and episodic fire signatures. It can test and, under a stated error model, scale regional inventories through transport modeling, but it cannot support national emissions claims without independent boundary conditions, boundary-layer observations, and longer records at the newer sites. Preserving explicit metadata and site-specific roles is therefore central to future network development.\n\nBukit Kototabang should remain the long-term traceability and transport anchor. The newer ecosystem, urban, and coastal sites extend the network into processes that a single background station cannot resolve. Their value will increase as records lengthen and as common calibration, metadata, and comparison procedures are maintained. The principal lesson is that network resilience depends on both measurement continuity and transparent interpretation of what each site represents.\n\nFuture evaluation should continue to separate observation, inference, and attribution. A measured concentration difference can test inventory or model consistency, but converting it into an emission rate requires transport and boundary-layer information. Maintaining this distinction will allow the network to support research and operational services without overstating what the observations alone demonstrate.", x2, y, colW, 920, {
    fontSize: 25,
  });

  y = addSection(slide, "references", "References", x3, 3470, colW);
  addText(slide, "references-text", "1. Conway, T. J., et al. (1994). Evidence for interannual variability of the carbon cycle from the NOAA/CMDL global air sampling network. J. Geophys. Res. 99, 22831–22855.\n\n2. Nisbet, E. G., et al. (2019). Very strong atmospheric methane growth in the 4 years 2014–2017: implications for the Paris Agreement. Global Biogeochem. Cycles 33, 318–342.\n\n3. Field, R. D., et al. (2016). Indonesian fire activity and smoke pollution in 2015 show persistent nonlinear sensitivity to El Niño-induced drought. Proc. Natl. Acad. Sci. USA 113, 9204–9209.\n\n4. Huijnen, V., et al. (2016). Fire carbon emissions over maritime southeast Asia in 2015 largest since 1997. Sci. Rep. 6, 26886.\n\n5. Lin, J. C., et al. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: the STILT model. J. Geophys. Res. 108, 4493.\n\n6. Stein, A. F., et al. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. Bull. Amer. Meteor. Soc. 96, 2059–2077.\n\n7. Crippa, M., et al. (2020). High resolution temporal profiles in the Emissions Database for Global Atmospheric Research. Sci. Data 7, 121.\n\n8. van der Werf, G. R., et al. (2025). Landscape fire emissions from the fifth version of the Global Fire Emissions Database (GFED5). Sci. Data 12, 1870.\n\nAcknowledgements. We thank NOAA, Empa, and NIES for measurement and operational support, and WMO for travel support to attend GGMT-2026.", x3, y, colW, 960, {
    fontSize: 24,
  });

  slide.shapes.add({ geometry: "rect", name: "footer-band", position: { left: 0, top: 4440, width: 3179, height: 54 },
    fill: "#0B4F5C", line: { style: "solid", fill: "none", width: 0 } });

  slide.speakerNotes.textFrame.setText([
    "[Sources]",
    "Scientific claims, site metadata, and figures: GHG_Analysis_Report.md, GHG_Analysis_Methods.md, outputs/station_summary.csv, outputs/station_hours.csv, and generated result CSV files; analysis date 18 August 2026.",
    "Figure sources: poster variants of figures/f2_flask_validation.png, f6_diurnal.png, f12_nocturnal_flux.png, f16_growth_fire.png and f24_trends_gradients.png built by scripts/a78_poster_figure_variants.py (report suptitle removed, poster headline added; plots unchanged); outputs/poster/poster_inversion_revision_tuned.png (scripts/a77_poster_inversion_figure.py from outputs/hysplit/revision/inversion tables), figures/f24_trends_gradients.png.",
    "Result 5 numbers come from the revised inversion (outputs/hysplit/revision/inversion/tables, 12 September 2026), tuned-covariance variant: scripts/a77_poster_inversion_figure.py --source revision --variant tuned; values in outputs/poster/poster_inversion_revision_tuned.csv.",
    "BMKG logo and identity: https://www.bmkg.go.id/Profil, accessed 3 September 2026.",
    "Conference details: https://www.ggmt2026.com/, accessed 3 September 2026.",
  ]);

  const preview = await deck.export({ slide, format: "png", scale: 0.5 });
  await writeBlob(`${TMP}/render-v11/poster-preview.png`, preview);
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(`${TMP}/render-v11/poster.layout.json`, await layout.text());
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
