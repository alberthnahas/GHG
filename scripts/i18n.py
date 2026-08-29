"""Figure localisation.

The figure scripts are not touched at all.  ``install(lang)`` monkey-patches the
handful of matplotlib entry points that accept human-readable text - titles,
axis labels, tick labels, annotations, and the ``label=`` kwarg that feeds
legends - so every string drawn on a figure passes through ``t()`` on its way to
the canvas.  ``Figure.savefig`` is patched too, so a non-default language writes
to ``<name>_<lang>.png`` and never overwrites the English figures.

The English figures remain the default: nothing changes unless ``--lang`` is
passed.

Adding a language means adding one dict to ``TABLES``.  Strings with no entry
fall through untranslated and are recorded in ``MISSING``; run
``python3 scripts/i18n.py --audit`` to list them.
"""
import re
import sys

LANGS = ("en", "id")
_lang = "en"
MISSING = set()

# Bahasa Indonesia.  Keys are the exact English strings the figure scripts draw.
# Chemical formulae keep their mathtext markup; station names are proper nouns
# and are deliberately left alone.
ID = {
    # ---- units and axis labels ----
    "ppm": "ppm",
    "ppb": "ppb",
    "hour of day (local time)": "jam (waktu setempat)",
    "hour (local time)": "jam (waktu setempat)",
    "local hour": "jam setempat",
    "month": "bulan",
    "year": "tahun",
    "station latitude (°N)": "lintang stasiun (°LU)",
    "day of week": "hari dalam minggu",
    "CO$_2$ (ppm)": "CO$_2$ (ppm)",
    "CH$_4$ (ppb)": "CH$_4$ (ppb)",
    "CO (ppb)": "CO (ppb)",
    "CO$_2$ growth (ppm yr$^{-1}$)": "laju pertumbuhan CO$_2$ (ppm thn$^{-1}$)",
    "CO$_2$ accumulation rate (ppm h$^{-1}$)": "laju akumulasi CO$_2$ (ppm jam$^{-1}$)",
    "implied surface flux (µmol m$^{-2}$ s$^{-1}$)": "fluks permukaan tersirat (µmol m$^{-2}$ s$^{-1}$)",
    "nocturnal CO$_2$ build-up / annual mean": "akumulasi CO$_2$ malam / rerata tahunan",
    "afternoon median − global mean (ppm)": "median siang − rerata global (ppm)",
    "CO$_2$ seasonal amplitude (ppm)": "amplitudo musiman CO$_2$ (ppm)",
    "ΔCH$_4$/ΔCO (ppb ppb$^{-1}$)": "ΔCH$_4$/ΔCO (ppb ppb$^{-1}$)",
    "peak CO enhancement (ppb)": "puncak peningkatan CO (ppb)",
    "e-folding relaxation time (days)": "waktu peluruhan e-lipat (hari)",
    "Sunday − weekday  (ppm / ppb)": "Minggu − hari kerja  (ppm / ppb)",
    "normalised anomaly": "anomali ternormalisasi",
    "fraction of nights": "fraksi malam",
    "emission ratio": "rasio emisi",
    "flask − in-situ (ppm)": "labu − in-situ (ppm)",
    "flask − in-situ (ppb)": "labu − in-situ (ppb)",
    "SF$_6$ seasonal anomaly (ppt)": "anomali musiman SF$_6$ (ppt)",
    "CH$_4$ seasonal anomaly (ppb)": "anomali musiman CH$_4$ (ppb)",
    "seasonal amplitude (ppb)": "amplitudo musiman (ppb)",
    "CO (ppb, log scale)": "CO (ppb, skala log)",
    "Oceanic Niño Index": "Indeks Niño Oseanik",

    # ---- figure titles and panel headings ----
    "a  Hourly data availability by station and species":
        "a  Ketersediaan data per jam menurut stasiun dan spesies",
    "b  As archived — the daily minimum is scattered across ten hours":
        "b  Sesuai arsip — minimum harian tersebar sepanjang sepuluh jam",
    "c  Converted to local time — every minimum falls in the well-mixed afternoon":
        "c  Setelah dikonversi ke waktu setempat — semua minimum jatuh pada siang yang tercampur baik",
    "Median diurnal composite: shape (top) and magnitude (bottom) shown separately":
        "Komposit diurnal median: bentuk (atas) dan magnitudo (bawah) ditampilkan terpisah",
    "Amplitude — Jakarta's CH$_4$ and CO swings are 30–75× those of the cleanest site":
        "Amplitudo — ayunan CH$_4$ dan CO Jakarta 30–75× lipat stasiun terbersih",
    "a  Nightly emission ratio — one point per tightly-coupled night":
        "a  Rasio emisi malam — satu titik per malam yang terkopel erat",
    "b  How often the species are co-emitted":
        "b  Seberapa sering spesies teremisi bersama",
    "a  Carbon monoxide at Bukit Kototabang, 2001–2024 (log scale)":
        "a  Karbon monoksida di Bukit Kototabang, 2001–2024 (skala log)",
    "b  El Niño (red) / La Niña (blue) state of the burning season":
        "b  Status El Niño (merah) / La Niña (biru) pada musim kebakaran",
    "Detrended seasonal cycle of the regional background (afternoon 20th percentile)":
        "Siklus musiman latar regional setelah tren dihilangkan (persentil ke-20 siang hari)",
    "a  CO: traffic has a weekly cycle": "a  CO: lalu lintas punya siklus mingguan",
    "a  Sumatra peat-fire haze reaching Bukit Kototabang, 2019":
        "a  Asap kebakaran gambut Sumatra mencapai Bukit Kototabang, 2019",
    "b  Plume emission ratio": "b  Rasio emisi gumpalan asap",
    "a  Sunday − weekday, all 15 tests": "a  Minggu − hari kerja, seluruh 15 uji",
    "a  Nocturnal build-up on well-stratified nights":
        "a  Akumulasi malam pada malam berstratifikasi baik",
    "b  Flux it implies for a 100–400 m stable layer":
        "b  Fluks tersirat untuk lapisan stabil 100–400 m",
    "a  Interannual CO$_2$ growth anomaly": "a  Anomali pertumbuhan CO$_2$ antartahun",
    "b  Fire season vs normal, in one ratio":
        "b  Musim kebakaran vs normal, dalam satu rasio",
    "c  Plumes clear before OH can act":
        "c  Gumpalan asap hilang sebelum OH sempat bekerja",
    "a  Dec 2025 CO$_2$ vs the global monthly mean":
        "a  CO$_2$ Des 2025 vs rerata bulanan global",
    "b  Respiration phase, normalised": "b  Fase respirasi, ternormalisasi",
    "c  Amplitude vs Mauna Loa and the pole":
        "c  Amplitudo vs Mauna Loa dan kutub",
    "a  Flask vs in-situ CO$_2$, matched hour": "a  CO$_2$ labu vs in-situ, jam yang sama",
    "b  The same comparison for CO": "b  Perbandingan yang sama untuk CO",
    "c  CH$_4$ tracks an inert tracer": "c  CH$_4$ mengikuti perunut inert",
    "a  Bukit Kototabang is a CO$_2$ minimum": "a  Bukit Kototabang adalah minimum CO$_2$",
    "b  SF$_6$ seasonal amplitude by site": "b  Amplitudo musiman SF$_6$ per lokasi",
    "c  Flask CO percentiles, 2004–2025": "c  Persentil CO labu, 2004–2025",

    # ---- suptitles ----
    "Figure 2  What an independent instrument says about the archive":
        "Gambar 2  Apa kata instrumen independen tentang arsip ini",
    "Figure 3  Bukit Kototabang inside the global flask network":
        "Gambar 3  Bukit Kototabang dalam jaringan labu global",
    "Figure 4  The diurnal rectifier, and a week when Jakarta stopped driving":
        "Gambar 4  Rektifier diurnal, dan sepekan saat Jakarta berhenti berkendara",
    "Figure 5  Flask reproducibility, interhemispheric transport lag, and vertical stratification":
        "Gambar 5  Reproduksibilitas labu, jeda transpor antarbebelahan bumi, dan stratifikasi vertikal",
    "Figure 7  Carbon source and sink: what the tracers separate, and what it is worth":
        "Gambar 7  Sumber dan rosot karbon: apa yang dipisahkan perunut, dan berapa nilainya",
    "Figure 10  The weekly-cycle detection limit, and the regional enhancement ladder":
        "Gambar 10  Batas deteksi siklus mingguan, dan tangga peningkatan regional",
    "Figure 11  Jakarta rush-hour fingerprint, equatorial H$_2$ seasonality, and global N$_2$O acceleration":
        "Gambar 11  Sidik jari jam sibuk Jakarta, musiman H$_2$ ekuator, dan akselerasi global N$_2$O",
    "Figure 12  The nocturnal boundary layer as a flux chamber":
        "Gambar 12  Lapisan batas malam sebagai ruang fluks",
    "Figure 13  Inter-station CO$_2$, respiration phase, and seasonal amplitude":
        "Gambar 13  CO$_2$ antarstasiun, fase respirasi, dan amplitudo musiman",
    "Figure 16  Growth anomalies, fire fingerprints and plume clearance at Bukit Kototabang":
        "Gambar 16  Anomali pertumbuhan, sidik jari kebakaran, dan peluruhan gumpalan di Bukit Kototabang",
    "Figure 17  Fire severity, the end of the burning season, and Jakarta hour by hour":
        "Gambar 17  Tingkat keparahan kebakaran, akhir musim bakar, dan Jakarta per jam",
    "Figure 19  Hovmöller dynamics: Global latitudinal wave propagation and trans-archipelago monsoon migration":
        "Gambar 19  Dinamika Hovmöller: Propagasi gelombang latitudinal global dan migrasi monsun lintas-kepulauan",
    "Figure 20  Transport timescale, vertical damping, and regional radiative forcing balance":
        "Gambar 20  Skala waktu transpor, redaman vertikal, dan neraca pemaksaan radiatif regional",
    "Figure 21  Regional structure: coherence, the marine comparison, and hydrogen":
        "Gambar 21  Struktur regional: koherensi, perbandingan maritim, dan hidrogen",
    "Figure 24  Twenty-two years: acceleration, hemispheric gradients, and what CO's cycle is made of":
        "Gambar 24  Dua puluh dua tahun: percepatan, gradien hemisfer, dan penyusun siklus CO",
    "Figure 25  ENSO in a warming ocean, and the warming this network implies":
        "Gambar 25  ENSO di samudra yang menghangat, dan pemanasan yang disiratkan jaringan ini",
    "Figure 26  What this network can and cannot detect":
        "Gambar 26  Apa yang dapat dan tidak dapat dideteksi jaringan ini",
    "Kemayoran, Jakarta — the weekly cycle separates traffic from waste":
        "Kemayoran, Jakarta — siklus mingguan memisahkan lalu lintas dari limbah",

    # ---- legend entries and in-plot annotations ----
    "regional biogenic CH$_4$": "CH$_4$ biogenik regional",
    "peat-fire plume": "gumpalan kebakaran gambut",
    "published Indonesian peat range 0.06–0.10":
        "rentang gambut Indonesia terpublikasi 0,06–0,10",
    "chemical lifetime of CO against OH": "umur kimiawi CO terhadap OH",
    "2023 El Niño": "El Niño 2023",
    "Sumatran dry season": "musim kemarau Sumatra",
    "published range for tropical\nforest ecosystem respiration":
        "rentang terpublikasi respirasi\nekosistem hutan tropis",
    "plausible SH tropical deficit": "defisit tropis BBS yang masuk akal",
    "Mauna Loa, 19 °N  ~15 ppm": "Mauna Loa, 19 °LU  ~15 ppm",
    "South Pole  ~3 ppm": "Kutub Selatan  ~3 ppm",
    "the one significant test\nin the whole network":
        "satu-satunya uji signifikan\ndi seluruh jaringan",
    "median": "median", "mean": "rerata",
    "background": "latar", "baseline": "garis dasar",
    "raw timestamps": "cap waktu mentah", "corrected": "terkoreksi",
    "as archived": "sesuai arsip", "flask": "labu", "in-situ": "in-situ",
    "excluded": "dikecualikan", "suspect period": "periode mencurigakan",
    "weekday": "hari kerja", "Sunday": "Minggu", "Saturday": "Sabtu",
    "El Niño": "El Niño", "La Niña": "La Niña",
    "CO$_2$": "CO$_2$", "CH$_4$": "CH$_4$", "CO": "CO",
    "N$_2$O": "N$_2$O", "SF$_6$": "SF$_6$", "H$_2$": "H$_2$",
    "fire years": "tahun kebakaran", "non-fire years": "tahun tanpa kebakaran",
    "Bukit Kototabang": "Bukit Kototabang", "Bariri, Lore Lindu": "Bariri, Lore Lindu",
    "Jambi": "Jambi", "Kemayoran": "Kemayoran", "Sorong": "Sorong",

    "b  As archived — sites 7–9 h out of phase": "b  Sesuai arsip — stasiun berbeda fase 7–9 jam",
    "c  Converted to local time — aligned": "c  Dikonversi ke waktu setempat — selaras",
    "b  CO": "b  CO",
    "c  CH$_4$": "c  CH$_4$",
    "d  CO$_2$": "d  CO$_2$",
    "b  ΔCO$_2$ vs Bariri": "b  ΔCO$_2$ vs Bariri",
    "c  ΔCH$_4$ vs Bariri": "c  ΔCH$_4$ vs Bariri",
    "d  ΔCO vs Bariri": "d  ΔCO vs Bariri",
    "hour (local time)": "jam (waktu setempat)",
    "hour of day  (as archived)": "jam  (sesuai arsip)",
    "hour of day  (local time)": "jam  (waktu setempat)",
    "in-situ CO$_2$ (ppm)": "CO$_2$ in-situ (ppm)",
    "flask CO$_2$ (ppm)": "CO$_2$ labu (ppm)",
    "mean CO$_2$ 2015–2025 (ppm)": "rerata CO$_2$ 2015–2025 (ppm)",
    "ΔCO/ΔCO$_2$  (ppb ppm$^{-1}$)": "ΔCO/ΔCO$_2$  (ppb ppm$^{-1}$)",
    "ΔCH₄/ΔCO": "ΔCH₄/ΔCO",
    "ΔCH₄/ΔCO₂": "ΔCH₄/ΔCO₂",
    "ΔCO/ΔCO₂": "ΔCO/ΔCO₂",
    "SF$_6$ seasonal amplitude (ppt)": "amplitudo musiman SF$_6$ (ppt)",

    "% of nights with $r^2 \\geq 0.7$": "% malam dengan $r^2 \\geq 0.7$",
    "10th pct (regional background)": "persentil ke-10 (latar regional)",
    "10th–95th percentile of hourly values": "persentil ke-10–95 nilai per jam",
    "CH$_4$  (ppb)": "CH$_4$  (ppb)",
    "CO  (ppb)": "CO  (ppb)",
    "CO$_2$  (ppm)": "CO$_2$  (ppm)",
    "CO enhancement (ppb)": "peningkatan CO (ppb)",
    "CO$_2$ anomaly (ppm)": "anomali CO$_2$ (ppm)",
    "CO$_2$ regional background  (afternoon 20th percentile)": "latar regional CO$_2$  (persentil ke-20 siang hari)",
    "CH$_4$ regional background  (afternoon 20th percentile)": "latar regional CH$_4$  (persentil ke-20 siang hari)",
    "CO regional background  (afternoon 20th percentile)": "latar regional CO  (persentil ke-20 siang hari)",
    "Mon–Fri": "Sen–Jum",
    "NW monsoon\nN-hemisphere air": "monsun barat laut\nudara belahan utara",
    "SE monsoon\nS-hemisphere air": "monsun tenggara\nudara belahan selatan",
    "ONI, Sep–Nov (°C)": "ONI, Sep–Nov (°C)",
    "Theil–Sen growth rate of the seasonally-adjusted background (95% CI)": "Laju pertumbuhan Theil–Sen latar terkoreksi musiman (SK 95%)",
    "mean CO$_2$ 2015–2025 (ppm)": "rerata CO$_2$ 2015–2025 (ppm)",

    "CO seasonal anomaly (ppb)": "anomali musiman CO (ppb)",
    "afternoon background − Bariri (ppm)": "latar siang hari − Bariri (ppm)",
    "change in the Barrow − South Pole difference": "perubahan selisih Barrow − Kutub Selatan",
    "growth rate / its 2004–2013 value": "laju pertumbuhan / nilainya 2004–2013",
    "a  Growth is accelerating, methane most": "a  Pertumbuhan makin cepat, metana paling cepat",
    "b  Only CO's hemispheric gap is closing": "b  Hanya selisih hemisfer CO yang menyempit",
    "c  Half the CO cycle is emitted nearby": "c  Separuh siklus CO teremisi di sekitar stasiun",
    "local emission": "emisi lokal",
    "transport (from SF$_6$)": "transpor (dari SF$_6$)",
    "observed": "teramati",
    "the two burning seasons": "dua musim kebakaran",

    "a  CO$_2$ removed beyond dilution": "a  CO$_2$ yang hilang melebihi pengenceran",
    "b  The nocturnal store, drawn down": "b  Simpanan malam, tersedot siang hari",
    "c  The same numbers as a carbon budget": "c  Angka yang sama sebagai neraca karbon",
    "extra CO$_2$ loss rate (h$^{-1}$)": "laju kehilangan CO$_2$ tambahan (jam$^{-1}$)",
    "ΔCO$_2$/ΔCH$_4$, relative to dawn": "ΔCO$_2$/ΔCH$_4$, relatif terhadap fajar",
    "net daytime sink": "rosot neto siang hari",
    "net daytime source": "sumber neto siang hari",
    "vs CH$_4$": "vs CH$_4$",
    "vs CO": "vs CO",
    "Pg C yr$^{-1}$": "Pg C thn$^{-1}$",

    "total emissions": "total emisi",
    "ocean sink": "rosot laut",
    "land sink": "rosot darat",
    "accumulation, this record": "akumulasi, rekaman ini",
    "2023 El Niño": "2023 El Niño",

    "a  Severity depends on how you measure it": "a  Keparahan bergantung pada cara mengukurnya",
    "b  El Niño delays the rains": "b  El Niño menunda datangnya hujan",
    "c  Jakarta's two ratios, in antiphase": "c  Dua rasio Jakarta, berlawanan fase",
    "a  Coherence follows site type, not distance": "a  Koherensi mengikuti jenis lokasi, bukan jarak",
    "b  A CO$_2$ sink region and a CO source region": "b  Wilayah rosot CO$_2$ sekaligus sumber CO",
    "c  Hydrogen tracks CO only in the burning months": "c  Hidrogen mengikuti CO hanya pada bulan kebakaran",
    "days above 1,000 ppb": "hari di atas 1.000 ppb",
    "peak daily CO (ppb)": "puncak CO harian (ppb)",
    "SON ONI (°C)": "ONI SON (°C)",
    "SON Oceanic Niño Index (°C)": "Indeks Niño Oseanik SON (°C)",
    "day of year the CO collapses": "hari ke- saat CO anjlok",
    "station separation (km)": "jarak antarstasiun (km)",
    "correlation of the monthly anomaly": "korelasi anomali bulanan",
    "both background sites": "keduanya stasiun latar",
    "at least one polluted": "minimal satu tercemar",
    "difference from Samoa": "selisih terhadap Samoa",
    "correlation of H$_2$ with CO": "korelasi H$_2$ dengan CO",
    "traffic peaks": "puncak lalu lintas",
    "ratio, relative to its own daily mean": "rasio, relatif terhadap reratanya sendiri",
    "ΔCO/ΔCO$_2$": "ΔCO/ΔCO$_2$",
    "ΔCH$_4$/ΔCO$_2$": "ΔCH$_4$/ΔCO$_2$",

    # ---- ENSO indices and the warming closure (f25) ----
    "decade": "dekade",
    "El Niño": "El Niño",
    "La Niña": "La Niña",
    "neutral": "netral",
    "tropical-mean SST anomaly (°C)": "anomali SPL rerata tropis (°C)",
    "peak daily-median CO at BKT (ppb)": "puncak median harian CO di BKT (ppb)",
    "a  What RONI subtracts is the warming":
        "a  Yang dikurangkan RONI: pemanasan",
    "b  Where they disagree, ONI matched the fires":
        "b  Saat berbeda, ONI cocok dengan kebakaran",
    "c  Two records, one rate":
        "c  Dua rekaman, satu laju",
    "2000–2025 SST trend, and the forcing accrual":
        "tren SPL 2000–2025, dan akumulasi pemaksaan",
    "observed\ntropical SST": "SPL tropis\nteramati",
    "implied by": "disiratkan oleh",
    "forcing accrual": "akumulasi pemaksaan",

    # ---- the rectifier, Idul Fitri, and detectability (f4, f26) ----
    "CO2": "CO2", "CH4": "CH4", "N2O": "N2O", "SF6": "SF6",
    "a  Afternoon sampling understates CO$_2$":
        "a  Pengambilan sampel siang meremehkan CO$_2$",
    "b  A negative rectifier flags bad data":
        "b  Rektifier negatif menandai data buruk",
    "c  The city empties; only CO notices":
        "c  Kota mengosong; hanya CO yang menyadarinya",
    "a  How long before a trend is real": "a  Berapa lama sebelum tren menjadi nyata",
    "b  What discrete sampling costs": "b  Biaya pengambilan sampel diskret",
    "c  How much of n is really there": "c  Berapa banyak dari n yang benar-benar ada",
    "24-hour mean − afternoon mean (ppm)": "rerata 24 jam − rerata siang (ppm)",
    "rectifier (ppm)": "rektifier (ppm)",
    "change during Idul Fitri (%)": "perubahan saat Idul Fitri (%)",
    "physically\nimpossible": "mustahil\nsecara fisika",
    "years of record needed": "tahun rekaman yang dibutuhkan",
    "error in the monthly mean (ppm)": "galat pada rerata bulanan (ppm)",
    "sample size (log scale)": "ukuran sampel (skala log)",
    "length of the\nflask record": "panjang rekaman\nlabu",
    "months or years used": "bulan atau tahun yang dipakai",
    "independent observations": "pengamatan independen",
    "rush 06-09": "jam sibuk 06-09",
    "all hours": "semua jam",
    "night 20-04": "malam 20-04",
    "weekly": "mingguan", "fortnightly": "dua mingguan", "monthly": "bulanan",
    "before 2023-06": "sebelum 2023-06", "from 2023-06": "sejak 2023-06",
    "co2 lag 0": "co2 jeda 0", "ch4 lag 12": "ch4 jeda 12", "co lag 0": "co jeda 0",
    "peak CO": "puncak CO", "days over 1000": "hari di atas 1000",
    "monsoon onset": "awal monsun",

    # ---- Figures 5 and 11 ----
    "a  Flask pair agreement at Bukit Kototabang":
        "a  Kesesuaian pasangan labu di Bukit Kototabang",
    "b  SF$_6$ as an interhemispheric clock":
        "b  SF$_6$ sebagai jam antarbebelahan bumi",
    "c  Free troposphere vs boundary layer (19.5°N)":
        "c  Troposfer bebas vs lapisan batas (19,5°LU)",
    "median |diff|": "median |selisih|",
    "95th percentile": "persentil ke-95",
    "pair difference (|flask 1 − flask 2|)": "selisih pasangan (|labu 1 − labu 2|)",
    "transport lag behind Arctic (months)": "keterlambatan transpor di belakang Arktik (bulan)",
    "standardized vertical difference (MLO − KUM)": "perbedaan vertikal terstandarisasi (MLO − KUM)",
    "mo": "bln",

    "a  Jakarta CO drops 24% on weekend mornings":
        "a  CO Jakarta turun 24% pada pagi akhir pekan",
    "b  Bimodal equatorial H$_2$ seasonal cycle":
        "b  Siklus musiman bimodal H$_2$ ekuator",
    "c  Global uniform N$_2$O acceleration (+0.23 ppb yr⁻¹)":
        "c  Akselerasi N$_2$O seragam global (+0,23 ppb thn⁻¹)",
    "weekday": "hari kerja",
    "weekend": "akhir pekan",
    "morning rush": "jam sibuk pagi",
    "local hour (WIB)": "jam lokal (WIB)",
    "median CO (ppb)": "median CO (ppb)",
    "H$_2$ mole fraction (ppb)": "fraksi mol H$_2$ (ppb)",
    "fire peak": "puncak kebakaran",
    "soil sink min": "min serapan tanah",
    "N$_2$O growth rate (ppb yr⁻¹)": "laju pertumbuhan N$_2$O (ppb thn⁻¹)",

    # ---- Figures 19 and 20 ----
    "a  Global CO$_2$ latitudinal propagation":
        "a  Propagasi latitudinal CO$_2$ global",
    "CO$_2$ mixing ratio (ppm)": "Rasio pencampuran CO$_2$ (ppm)",
    "b  Global CH$_4$ gradient & post-2014 surge":
        "b  Gradien CH$_4$ global & lonjakan pasca-2014",
    "CH$_4$ mixing ratio (ppb)": "Rasio pencampuran CH$_4$ (ppb)",
    "c  Maritime Continent CH$_4$ zonal wave":
        "c  Gelombang zonal CH$_4$ Benua Maritim",
    "CH$_4$ anomaly from median (ppb)": "Anomali CH$_4$ dari median (ppb)",
    "longitude (°E)": "bujur (°BT)",
    "month of year": "bulan dalam setahun",
    "latitude": "lintang",
    "+71°": "+71°", "+20°": "+20°", "-0°": "-0°", "-14°": "-14°", "-90°": "-90°",
    "BKT (100.3°E)": "BKT (100,3°BT)", "JMB (103.6°E)": "JMB (103,6°BT)",
    "KMY (106.8°E)": "KMY (106,8°BT)", "PLU (120.0°E)": "PLU (120,0°BT)",
    "SRG (131.3°E)": "SRG (131,3°BT)",

    "a  SF$_6$ interhemispheric mixing clock":
        "a  Jam pencampuran antarbebelahan bumi SF$_6$",
    "SF$_6$ mixing ratio (ppt)": "Rasio pencampuran SF$_6$ (ppt)",
    "Barrow (71°N)": "Barrow (71°LU)",
    "Bukit Kototabang (0°S)": "Bukit Kototabang (0°LS)",
    "South Pole (90°S)": "Kutub Selatan (90°LS)",
    "b  Vertical damping of seasonal cycle (19.5°N)":
        "b  Redaman vertikal siklus musiman (19,5°LU)",
    "KUM surface (3 m)": "Permukaan KUM (3 m)",
    "MLO free trop (3397 m)": "Troposfer bebas MLO (3.397 m)",
    "aloft": "di atas",
    "peak-to-peak seasonal amplitude": "amplitudo musiman puncak-ke-puncak",
    "c  Regional forcing anomaly over marine air":
        "c  Anomali pemaksaan regional di atas udara laut",
    "radiative forcing anomaly (mW m$^{-2}$)": "anomali pemaksaan radiatif (mW m$^{-2}$)",
    "CO$_2$ (ppm)": "CO$_2$ (ppm)", "CH$_4$ (ppb)": "CH$_4$ (ppb)", "CO (ppb)": "CO (ppb)",
    "−12.3% aloft": "−12,3% di atas", "−14.0% aloft": "−14,0% di atas", "−18.1% aloft": "−18,1% di atas",
    "+0.1 mW m$^{-2}$\n(+0.1 ppt)": "+0,1 mW m$^{-2}$\n(+0,1 ppt)",
    "+3.4 mW m$^{-2}$\n(+1.0 ppb)": "+3,4 mW m$^{-2}$\n(+1,0 ppb)",
    "+46.5 mW m$^{-2}$\n(+70.9 ppb)": "+46,5 mW m$^{-2}$\n(+70,9 ppb)",
    "-40.4 mW m$^{-2}$\n(-3.1 ppm)": "-40,4 mW m$^{-2}$\n(-3,1 ppm)",
    "Net: +9.72 mW m$^{-2}$": "Net: +9,72 mW m$^{-2}$",

    # ---- Part VI: the carbon economic value (f27, f28) ----
    "Figure 28  What a measured signal is worth, and where its uncertainty comes from":
        "Gambar 28  Berapa nilai sinyal terukur, dan dari mana ketidakpastiannya berasal",
    "Figure 27  What the network can verify, at two scales":
        "Gambar 27  Apa yang dapat diverifikasi jaringan ini, pada dua skala",
    "a  Jambi peat loss, priced": "a  Nilai kehilangan gambut Jambi",
    "b  Where the uncertainty is": "b  Di mana letak ketidakpastiannya",
    "c  Jakarta's methane vs assumed depth": "c  Metana Jakarta terhadap kedalaman asumsi",
    "a  Station scale: the cut a five-year record could verify":
        "a  Skala stasiun: penurunan yang dapat diverifikasi rekaman lima tahun",
    "b  National scale: the whole width of the 2035 NDC range":
        "b  Skala nasional: seluruh rentang target NDC 2035",
    "Carbon tax floor": "Batas bawah pajak karbon",
    "IDXCarbon average": "Rerata IDXCarbon",
    "IDXCarbon opening": "Harga pembukaan IDXCarbon",
    "EU ETS (contrast)": "EU ETS (pembanding)",
    "Nocturnal layer depth": "Kedalaman lapisan malam",
    "Peat store depth": "Kedalaman simpanan gambut",
    "Carbon price": "Harga karbon",
    "Accumulation rate": "Laju akumulasi",
    "IDR million per hectare per year (log scale)":
        "Rp juta per hektar per tahun (skala log)",
    "IDR billion per year": "Rp miliar per tahun",
    "multiplicative span, high case / low case":
        "rentang perkalian, kasus tinggi / kasus rendah",
    "assumed nocturnal layer depth (m)": "kedalaman lapisan malam yang diasumsikan (m)",
    "boundary-layer depth (m)": "kedalaman lapisan batas (m)",
    "ppm CO$_2$": "ppm CO$_2$",
    "ppm CO$_2$-equivalent": "ppm setara CO$_2$",
    "measured enhancement over Bariri": "peningkatan terukur di atas Bariri",
    "detectable step, 12 months": "perubahan terdeteksi, 12 bulan",
    "detectable step, 60 months": "perubahan terdeteksi, 60 bulan",
    "what the record can resolve (5 yr)": "yang dapat diurai rekaman ini (5 thn)",
    "assumed": "diasumsikan",
    "policy": "kebijakan",
    "measured": "terukur",
    "τ = 0.5 d": "τ = 0,5 hari",
    "τ = 1 d": "τ = 1 hari",
    "τ = 3 d": "τ = 3 hari",

    # ---- month and weekday abbreviations ----
    "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr", "May": "Mei",
    "Jun": "Jun", "Jul": "Jul", "Aug": "Agu", "Sep": "Sep", "Oct": "Okt",
    "Nov": "Nov", "Dec": "Des",
    "Mon": "Sen", "Tue": "Sel", "Wed": "Rab", "Thu": "Kam", "Fri": "Jum",
    "Sat": "Sab", "Sun": "Min",
    "HOW IT WAS MEASURED": "BAGAIMANA INI DIUKUR",
    # Surfaced once Container.get_label was translated: bar-chart legend labels
    # in a12/a18/a27 that had never reached t() at all.
    "2004\u20132013": "2004\u20132013",
    "2014\u20132024": "2014\u20132024",
    "2014\u20132025": "2014\u20132025",
    "colour = station": "warna = stasiun",
    # ---- sequencer specification figures (a37_sequencer_figs) ----
    "0.4 slpm": "0,4 slpm",
    "2 slpm": "2 slpm",
    "5 slpm": "5 slpm",
    "10 slpm": "10 slpm",
    "30 m": "30 m",
    "70 m": "70 m",
    "100 m": "100 m",
    "30 m vs 100 m": "30 m vs 100 m",
    "70 m vs 100 m": "70 m vs 100 m",
    "1 % residual": "sisa 1 %",
    "3-min purge": "pembilasan 3 menit",
    "adopted purge window": "jendela pembilasan yang dipakai",
    "valid, archived": "sahih, diarsipkan",
    "purge, discarded": "pembilasan, dibuang",
    "bypass flow": "aliran bypass",
    "sequential": "berurutan",
    "bracketed": "terkurung",
    "DJF": "DJF",
    "JJA": "JJA",
    "convective": "konvektif",
    "stable / drainage": "stabil / aliran turun",
    "extrapolated\n(no sub-hourly data)": "ekstrapolasi\n(tiada data sub-jam)",
    "CH$_4$ anomaly (ppb)": "anomali CH$_4$ (ppb)",
    "CO anomaly (ppb)": "anomali CO (ppb)",
    "CO$_2$ anomaly from daily mean (ppm)": "anomali CO$_2$ dari rerata harian (ppm)",
    "Hour of day (local time)": "Jam (waktu setempat)",
    "Spread / its 24-h mean": "Sebaran / rerata 24-jamnya",
    "Lag (hours)": "Jeda (jam)",
    "RMS change over the lag (ppm / ppb)": "Perubahan RMS sepanjang jeda (ppm / ppb)",
    "Monthly-mean RMS error": "Galat RMS rerata bulanan",
    "Monthly-mean RMS error (ppm / ppb)": "Galat RMS rerata bulanan (ppm / ppb)",
    "Diurnal amplitude lost (%)": "Amplitudo diurnal yang hilang (%)",
    "Spurious CO$_2$ gradient from timing alone (ppm)": "Gradien CO$_2$ semu akibat waktu saja (ppm)",
    "Minutes past the hour (UTC)": "Menit setelah awal jam (UTC)",
    "Time after valve switch (min)": "Waktu setelah pergantian katup (menit)",
    "Residual of the previous level (%)": "Sisa dari level sebelumnya (%)",
    "Inlet height (m)": "Tinggi inlet (m)",
    "Time to 1 % residual (min)": "Waktu menuju sisa 1 % (menit)",
    "a  The signal is nocturnal, in every season": "a  Sinyalnya nokturnal, di setiap musim",
    "b  CH$_4$ and CO peak in the same window": "b  CH$_4$ dan CO memuncak di jendela yang sama",
    "c  Variability peaks at the morning transition": "c  Keragaman memuncak saat transisi pagi",
    "a  How fast the air changes": "a  Secepat apa udara berubah",
    "b  What 3-hourly sampling costs": "b  Biaya pencuplikan 3-jaman",
    "c  Bracketing removes most of it": "c  Pengurungan menghapus sebagian besarnya",
    "a  The hourly frame, repeated every hour of every day":
        "a  Kerangka per jam, diulang setiap jam setiap hari",
    "b  A bypass pump makes 3 min work": "b  Pompa bypass: 3 menit cukup",
    "c  Purge scales with length": "c  Pembilasan ikut panjang saluran",
    "Figure SQ1  The diurnal cycle at Bukit Kototabang, 30-m inlet, and what it demands of a sampling schedule":
        "Gambar SQ1  Siklus diurnal di Bukit Kototabang, inlet 30 m, dan tuntutannya pada jadwal pencuplikan",
    "Figure SQ2  The three measurements that fix the schedule":
        "Gambar SQ2  Tiga pengukuran yang menetapkan jadwal",
    "Figure SQ3  The adopted frame and the flush constraint that sets its purge windows":
        "Gambar SQ3  Kerangka yang dipakai dan kendala pembilasan yang menetapkan jendelanya",
}

TABLES = {"en": {}, "id": ID}


def set_lang(lang):
    global _lang
    if lang not in LANGS:
        raise ValueError(f"unknown language {lang!r}; known: {LANGS}")
    _lang = lang


def suffix():
    """Filename suffix so a translated run never overwrites the English figures."""
    return "" if _lang == "en" else f"_{_lang}"


STATION_CODES = ("BKT", "JMB", "KMY", "PLU", "SRG",
                 "BRW", "MLO", "KUM", "SMO", "SPO")   # NOAA flask sites


def _internal(s):
    """Strings that carry no translatable content.

    matplotlib's own placeholder labels, single-character tick labels (month and
    weekday initials, which are handled by the tick dictionary when spelled out),
    and the five station codes, which are proper nouns.
    """
    # "2019 A" / "2019 F" are a year plus a season initial, identical in any language
    if re.fullmatch(r"\d{4} [AF]", s.strip()):
        return True
    return (s.startswith("_") or s in ("None", "<colorbar>") or len(s.strip()) <= 1
            or s.strip() in STATION_CODES
            or s.split("\n")[0].strip() in STATION_CODES
            or s.split()[0] in STATION_CODES
            or all(part in STATION_CODES for part in s.strip().split("-")))


# Indonesian swaps the two separators: 4,063 becomes 4.063 and 0.22 becomes
# 0,22.  Only separators *between digits* are touched, so the comma in
# "Mauna Loa, 19 °N" and the full stop ending a sentence are both left alone.
_SEP = re.compile(r"(?<=\d)([.,])(?=\d)")


def _id_numbers(s):
    return _SEP.sub(lambda m: "," if m.group(1) == "." else ".", s)


def t(s):
    if _lang == "en" or not isinstance(s, str) or not s.strip() or _internal(s):
        return s
    tab = TABLES[_lang]
    if s in tab:
        return tab[s]
    # Decimal comma is the Indonesian convention; apply it to bare numeric labels
    # (axis ticks and value annotations) even when there is no dictionary entry.
    if _lang == "id" and _is_numeric_label(s):
        return _id_numbers(s)
    out = _phrases(s)
    if out != s:
        return _id_numbers(out) if _lang == "id" else out
    MISSING.add(s)
    return s


# Applied in order to any string with no whole-string entry.  These cover the
# annotations the figure scripts build with f-strings, where the numbers vary
# but the surrounding words do not.
PHRASES = {
    "id": [
        (r"\bslope\b", "kemiringan"),
        (r"network NH−SH ratio", "rasio BBU−BBS jaringan"),
        (r"reported emission ratio for\nIndonesian peat", "rasio emisi terlapor untuk\ngambut Indonesia"),
        (r"\bmonthly median\b", "median bulanan"),
        (r"\bpre-fire background\b", "latar sebelum kebakaran"),
        (r"\binstrument change\b", "pergantian instrumen"),
        (r"efficient fossil combustion", "pembakaran fosil efisien"),
        (r"smouldering peat / biomass burning", "gambut membara / pembakaran biomassa"),
        (r"well-mixed\nafternoon", "siang yang\ntercampur baik"),
        (r"○ = daily minimum", "○ = minimum harian"),
        (r"diurnal peak-to-peak\namplitude", "amplitudo diurnal\npuncak-ke-puncak"),
        (r"normalised anomaly\n\(fraction of own amplitude\)",
         "anomali ternormalisasi\n(fraksi amplitudo sendiri)"),
        (r"red bands = periods\nexcluded as instrumentally\nsuspect",
         "pita merah = periode\ndikecualikan karena instrumen\nmencurigakan"),
        (r"\bTable (\d+)\b", r"Tabel \1"),
        (r"\bas archived\b", "sesuai arsip"),
        (r"\bsites 7–9 h out of phase\b", "stasiun berbeda fase 7–9 jam"),
        (r"Converted to local time — aligned", "Dikonversi ke waktu setempat — selaras"),
        (r"\bflask\b", "labu"),
        (r"\bmean\b", "rerata"),
        (r"\byr\b", "thn"),
        (r"\blog scale\b", "skala log"),
        (r"\bhour of day\b", "jam"),
        (r"\bhour\b", "jam"),
        (r"\blocal time\b", "waktu setempat"),
        (r"\bvs\b", "vs"),
        (r"\bmedian\b", "median"),
        (r"95th pct", "persentil ke-95"),
        (r"the record background", "latar rekaman"),
        (r"of the month above", "bulan di atas"),
        (r"\bSun\b", "Min"),
        (r"between the SON ONI", "antara ONI SON"),
        (r"and the annual 95th-percentile CO", "dan CO persentil ke-95 tahunan"),
        (r"\bfull\b", "penuh"),
        (r"days later per", "hari lebih lambat per"),
        (r"\bspans\b", "rentang"),
        (r"Mauna Loa, 19 °N", "Mauna Loa, 19 °LU"),
        (r"\bSouth Pole\b", "Kutub Selatan"),
        (r"\bNet:", "Neto:"),
        (r"\bdecade\b", "dekade"),
        (r"\bneutral\b", "netral"),
        (r"\bimplied by\b", "disiratkan oleh"),
        (r"\bforcing accrual\b", "akumulasi pemaksaan"),
        (r"\bmo\b", "bln"),
    ],
}


def _phrases(s):
    out = s
    for pat, rep in PHRASES.get(_lang, []):
        out = re.sub(pat, rep, out)
    return out


# Units that read the same in every language this module supports, so a label
# that is only a number and one of these needs no entry.
UNIVERSAL_UNITS = r"(?:ppm|ppb|ppt|mW m⁻²|W m⁻²|°C|K|ppm/yr|d|mo)"
# mathtext units as drawn by matplotlib, e.g. "mW m$^{-2}$"
MATHTEXT_UNITS = r"[munpk]?[A-Za-z]+ ?m\$\^\{-?\d\}\$"


def _is_numeric_label(s):
    """A value annotation: digits, punctuation, the 'n=' count, and bare units."""
    body = s.replace("n=", "").replace("\n", " ")
    body = re.sub(MATHTEXT_UNITS, " ", body)
    body = re.sub(rf"\b{UNIVERSAL_UNITS}\b", " ", body)
    return bool(s.strip()) and all(c in "0123456789.,+-−%eE ()×  " for c in body)


def _wrap1(fn):
    def inner(self, s=None, *a, **k):
        return fn(self, t(s), *a, **k)
    return inner


def _wrap_list(fn):
    def inner(self, labels, *a, **k):
        return fn(self, [t(x) if isinstance(x, str) else x for x in labels], *a, **k)
    return inner


def install(lang):
    """Route every figure-bound string through the translator.  Idempotent."""
    set_lang(lang)
    if lang == "en":
        return
    import matplotlib.axes as maxes
    import matplotlib.figure as mfig
    import matplotlib.artist as mart

    if getattr(install, "_done", False):
        return
    for cls, names in ((maxes.Axes, ("set_title", "set_xlabel", "set_ylabel")),
                       (mfig.Figure, ("suptitle",))):
        for n in names:
            setattr(cls, n, _wrap1(getattr(cls, n)))
    for n in ("set_xticklabels", "set_yticklabels"):
        setattr(maxes.Axes, n, _wrap_list(getattr(maxes.Axes, n)))

    _ann = maxes.Axes.annotate
    maxes.Axes.annotate = lambda self, text, *a, **k: _ann(self, t(text), *a, **k)
    _txt = maxes.Axes.text
    maxes.Axes.text = lambda self, x, y, s, *a, **k: _txt(self, x, y, t(s), *a, **k)
    # `label=` on any plotting call reaches the artist through set_label.
    _sl = mart.Artist.set_label
    mart.Artist.set_label = lambda self, s: _sl(self, t(s) if isinstance(s, str) else s)
    # ...except bar() and barh(), whose label lands on a BarContainer.
    # `Container.__init__` assigns `self._label` directly - there is no setter
    # to intercept - so translate on the way out instead.  Without this a bar
    # chart's legend silently stays English AND the audit reports zero, because
    # the string never reaches t() to be recorded.
    import matplotlib.container as mcont
    _cg = mcont.Container.get_label
    mcont.Container.get_label = lambda self: t(_cg(self))
    # A legend title is a plain kwarg and reaches no patched entry point.
    _leg = maxes.Axes.legend

    def legend(self, *a, **k):
        if isinstance(k.get("title"), str):
            k["title"] = t(k["title"])
        return _leg(self, *a, **k)
    maxes.Axes.legend = legend

    _save = mfig.Figure.savefig

    def savefig(self, fname, *a, **k):
        s = str(fname)
        if s.endswith(".png"):
            fname = s[:-4] + suffix() + ".png"
        return _save(self, fname, *a, **k)
    mfig.Figure.savefig = savefig
    install._done = True


def add_arg(parser):
    parser.add_argument("--lang", default="en", choices=LANGS,
                        help="figure language; the default English figures are always written")
    return parser


def from_argv(argv=None):
    """Minimal --lang parse, so the figure scripts need no argparse of their own."""
    argv = sys.argv if argv is None else argv
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--lang="):
            return a.split("=", 1)[1]
    return "en"


if __name__ == "__main__":
    if "--audit" in sys.argv:
        import importlib
        set_lang("id")
        install("id")
        for m in ("a3_figures", "a8_extra_figs", "a10_process_figs",
                  "a12_flask_figs", "a16_carbon_figs", "a18_extra2_figs",
                  "a23_roni_figs", "a25_extra3_figs", "a27_extra4_figs", "a29_extra5_figs",
                  "a32_nek_figs", "a37_sequencer_figs"):
            try:
                mod = importlib.import_module(m)
                import ghg_common as G
                G.style()
                for fn in ("main", "f1"):
                    if hasattr(mod, fn):
                        break
                mod_main = getattr(mod, "main", None)
                if mod_main:
                    mod_main()
            except Exception as e:                    # noqa: BLE001
                print(f"  [{m}] {type(e).__name__}: {e}")
        print(f"\n{len(MISSING)} untranslated strings:")
        for s in sorted(MISSING):
            print(f"    {s!r}")
