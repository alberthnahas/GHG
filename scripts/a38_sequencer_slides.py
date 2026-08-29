# -*- coding: utf-8 -*-
"""Bahasa Indonesia deck for the BKT 100-m tower valve sequencer specification.

Layouts are imported from ``a19_slides`` so this deck looks like the others:
white background, 16:9, the same rules and type scale.

The prose here is written in Indonesian directly rather than translated through
``i18n``.  ``set_lang("id")`` is still set, because ``_fig()`` uses
``i18n.suffix()`` to pick the ``_id`` version of each figure - so the figures
are Indonesian and the slide text is Indonesian, by two different routes.
Numbers are written with the decimal comma in the source, since a whole
sentence does not pass through the numeric-label path that would convert them.

Every number on these slides comes from `outputs/sq_*.csv` via
`BKT_Tower_Sequencer_Specification.md`.

Usage:  a38_sequencer_slides.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n
import ghg_common as G
import a19_slides as S

ROOT = G.ROOT
OUT = ROOT / "outputs" / "BKT_Tower_Sequencer_Slides_id.pptx"


def build():
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = S.W, S.H

    n = [0]

    def page():
        n[0] += 1
        return n[0]

    # ---------------------------------------------------------------- judul --
    s = S._blank(prs)
    S._rule(s, Inches(2.05), S.M, S.BODY, S.BLUE, Pt(2.5))
    tf = S._tb(s, S.M, Inches(2.3), S.BODY, Inches(1.75))
    S._para(tf, "Spesifikasi sekuenser katup untuk menara 100 m Bukit Kototabang",
            32, S.INK, bold=True, first=True, space_after=10)
    S._para(tf, "Menjadwalkan tiga ketinggian inlet pada satu Picarro G2401, "
                "dengan rancangan pencuplikan ditetapkan dari rekaman 30 m stasiun itu sendiri",
            16, S.MUTED)
    S._rule(s, Inches(4.35), S.M, S.BODY)
    tf = S._tb(s, S.M, Inches(4.65), S.BODY, Inches(1.2))
    S._para(tf, "30 m · 70 m · 100 m — GAW Global, Sumatera Barat", 14, S.INK,
            first=True, space_after=8)
    S._para(tf, "59.231 jam CO₂ · 65.013 jam CH₄ · 42.740 jam CO menjadi dasar rancangan ini",
            13, S.MUTED)
    S._footer(s, "Rancangan untuk ditinjau · 23 Agustus 2026", page())

    # --------------------------------------------------------------- konteks --
    S.slide_section(prs, "BAGIAN 1",
                    "Apa yang berubah, dan apa yang harus diputuskan",
                    "Dari satu inlet 30 m menjadi tiga ketinggian pada satu penganalisis",
                    page())

    S.slide_pair(
        prs, "KONTEKS", "Empat hal harus ditetapkan sebelum sekuenser diprogram",
        [("Yang ada sekarang",
          ["Satu inlet pada 30 m, dipilih agar rekaman in-situ dapat dibandingkan "
           "langsung dengan program labu (flask) di lokasi yang sama.",
           "Rekaman 30 m itu terdaftar di WDCGG. Kesinambungannya wajib dijaga."]),
         ("Yang akan datang",
          ["Menara 100 m dengan intake pada 30 m, 70 m dan 100 m.",
           "Satu Picarro G2401 dibagi ke tiga saluran oleh katup multi-posisi.",
           "Prioritas ilmiah: 100 m mendapat sebagian besar waktu pengukuran."]),
         ("Empat pertanyaan",
          ["1. Berapa lama menunggu setelah katup berpindah?",
           "2. Berapa lama tiap level dicuplik?",
           "3. Seberapa sering tiap level dikunjungi?",
           "4. Dalam urutan apa level dikunjungi?"])],
        ["Pertanyaan 2–4 dijawab dari rekaman 30 m stasiun ini sendiri; pertanyaan 1 "
         "adalah geometri saluran, bukan pengukuran.",
         "Pertanyaan 4 ternyata lebih menentukan daripada yang diduga."],
        page())

    S.slide_table(
        prs, "KENDALA", "Enam kendala rancangan, dan dua yang saling tarik-menarik",
        ["#", "Kendala", "Asal"],
        [["C1", "*100 m membawa mayoritas waktu pengukuran", "prioritas ilmiah stasiun"],
         ["C2", "*30 m melanjutkan seri WDCGG tanpa perubahan statistik pencuplikan",
          "kesinambungan arsip data"],
         ["C3", "Semua level dicuplik setiap jam setiap hari", "menghindari aliasing siklus diurnal"],
         ["C4", "*Level dibandingkan pada waktu yang sedekat mungkin",
          "gradien vertikal adalah tujuan menara"],
         ["C5", "Waktu pembilasan yang dibuang ditekan sekecil mungkin", "murni kerugian"],
         ["C6", "Kerangka identik di setiap jam", "mesin-keadaan dan QC paling sederhana"]],
        ["C2 dan C4 menarik paling kuat, dan ke arah yang berbeda.",
         "C2 menggugurkan jadwal “3-jaman untuk level bawah”; C4 menggugurkan urutan "
         "“dari bawah ke atas”."],
        page(), widths=[0.06, 0.56, 0.38])

    # ------------------------------------------------------------- manifold --
    S.slide_section(prs, "BAGIAN 2",
                    "Manifold menentukan segalanya",
                    "Tanpa pompa bypass, tidak ada jadwal di sini yang berjalan",
                    page())

    S.slide_figure_wide(
        prs, "PEMBILASAN", "Pompa bypass adalah perbedaan antara 15 % dan 48 % waktu terbuang",
        "sq3_frame_and_flush.png",
        "Gambar SQ3. (a) Kerangka per jam yang dipakai. (b) Peluruhan sisa pada saluran 100 m "
        "untuk tiap laju aliran. (c) Waktu menuju sisa 1 % menurut panjang saluran.",
        ["Saluran 100 m berisi 1,26 L. Pada 0,4 slpm — aliran G2401 sendiri — perlu 14,5 menit "
         "untuk bersih sampai 1 %.",
         "Pada 5 slpm perlu 1,16 menit. Jendela pembilasan 3 menit memberi 11,9 volume saluran "
         "terhadap 4,6 yang dibutuhkan.",
         "Tanpa bypass, tiga pembilasan memakan 28,9 menit — 48 % dari setiap jam. Dengan bypass: "
         "9 menit, 15 %."],
        ["Volume dari diameter dalam 4,0 mm dan panjang lintasan; peluruhan exp(−t/τ), τ = V/Q.",
         "Anggapan tercampur-baik bersifat konservatif. Sumber: outputs/sq_flush.csv."],
        page())

    S.slide_table(
        prs, "PEMBILASAN", "Volume saluran dan waktu menuju sisa 1 %",
        ["Inlet", "Volume (L)", "0,4 slpm", "2 slpm", "5 slpm", "10 slpm"],
        [["30 m", "0,377", "4,34", "0,87", "0,35", "0,17"],
         ["70 m", "0,880", "10,13", "2,03", "0,81", "0,41"],
         ["*100 m", "*1,257", "*14,47", "*2,89", "*1,16", "*0,58"]],
        ["Waktu dalam menit. Sumber: outputs/sq_flush.csv.",
         "Spesifikasi: semua saluran disapu terus-menerus pada ≥ 5 slpm oleh pompa diafragma "
         "bersama; katup hanya mengambil sebagian aliran.",
         "Jendela pembilasan 3 menit juga menutupi manifold bersama dan rongga penganalisis, "
         "yang tidak termasuk dalam tabel ini."],
        page(), widths=[0.16, 0.18, 0.165, 0.165, 0.165, 0.165])

    # -------------------------------------------------------------- diurnal --
    S.slide_section(prs, "BAGIAN 3",
                    "Apa yang dituntut oleh rekaman stasiun",
                    "Siklus diurnal, aliasing, panjang cuplikan, dan urutan",
                    page())

    S.slide_figure_wide(
        prs, "SIKLUS DIURNAL", "Informasi vertikal berada di malam hari, di setiap musim",
        "sq1_diurnal_demand.png",
        "Gambar SQ1. (a) Komposit anomali CO₂ dengan selubung interkuartil dan pemisahan "
        "DJF/JJA. (b) CH₄ dan CO. (c) Sebaran per jam, dinormalkan ke rerata 24 jamnya.",
        ["Rentang CO₂ mencapai 22,9 ppm antara maksimum pukul 06.00 dan minimum pukul 14.00 "
         "waktu setempat.",
         "Bentuknya sama di DJF dan JJA — jadwal tidak perlu mode musiman.",
         "Keragaman memuncak pada transisi pagi (06.00–07.00), bukan pada puncak diurnal. "
         "Di sanalah cuplikan pendek paling tidak mewakili."],
        ["Anomali terhadap rerata harian tiap hari, agar tren dan musim tidak merembes.",
         "Hanya hari dengan ≥ 18 jam data. Sumber: outputs/sq_diurnal.csv."],
        page())

    S.slide_figure_wide(
        prs, "TEMUAN", "Pencuplikan 3-jaman tidak sejalan dengan rekaman WDCGG",
        "sq2_design_evidence.png",
        "Gambar SQ2. (a) Fungsi struktur, terukur (garis penuh) dan ekstrapolasi (titik-titik). "
        "(b) Biaya pencuplikan 3-jaman. (c) Gradien semu dari dua urutan yang diuji.",
        ["CO₂ hampir tidak terpengaruh: galat RMS 0,18 ppm, amplitudo diurnal berkurang 2 %.",
         "CH₄ dan CO punya puncak pagi yang tajam yang terpangkas sistematis — 12 % dan 16 % "
         "amplitudo, ke arah yang sama pada setiap offset.",
         "Galat CH₄ bulan terburuk 5,05 ppb — sebanding dengan satu tahun pertumbuhan CH₄ global."],
        ["Rerata bulanan disusun ulang dari subcuplik 3-jaman pada tiap offset, lalu dibandingkan "
         "dengan rekaman penuh.",
         "Sumber: outputs/sq_subsample.csv, outputs/sq_diurnal_bias.csv."],
        page())

    S.slide_table(
        prs, "TEMUAN", "Biaya pencuplikan 3-jaman, diukur pada rekaman BKT",
        ["Spesies", "Bulan", "Galat RMS rerata bulanan", "Bulan terburuk", "Amplitudo diurnal hilang"],
        [["CO₂ (ppm)", "81", "0,18", "0,66", "2,0 %"],
         ["*CH₄ (ppb)", "*91", "*0,84", "*5,05", "*12,0 %"],
         ["*CO (ppb)", "*61", "*0,55", "*2,45", "*16,3 %"]],
        ["Keberatan kedua tidak terlihat di tabel: seri WDCGG dibangun dari rerata jam yang "
         "hampir sinambung. Beralih ke 8 rerata jam per hari mengubah statistik pencuplikannya, "
         "bukan sekadar kerapatannya — dan pada tanggal yang sama dengan pemindahan inlet fisik.",
         "*Keputusan: setiap level dicuplik pada setiap jam. C1 dipenuhi dengan membagi jam, "
         "bukan membagi hari.*"],
        page(), widths=[0.18, 0.12, 0.28, 0.18, 0.24])

    S.slide_pair(
        prs, "PANJANG CUPLIKAN", "Lima menit memadai, dan itu bukan batas yang mengikat",
        [("Presisi — bukan pengikatnya",
          ["Derau mentah G2401 jauh di bawah keragaman atmosferik di lokasi ini.",
           "Merata-ratakan 5 menit data 1 Hz menurunkannya satu orde lagi.",
           "Tidak ada bagian jadwal ini yang dibatasi presisi."]),
         ("Keterwakilan — pengikatnya",
          ["Fungsi struktur D(τ) dipasang pada jeda 1–6 jam sebagai D = A·τ^(2H).",
           "CO₂: A = 26,25, H = 0,590, r² = 0,99998.",
           "Perubahan RMS 5 menit hasil ekstrapolasi: 1,18 ppm CO₂ — kecil terhadap rentang "
           "diurnal 22,9 ppm."]),
         ("Batas yang jujur",
          ["Ini ekstrapolasi 12 kali lipat di bawah jeda terpendek yang dapat diselesaikan data.",
           "Hukum pangkat hampir pasti tidak berlaku sampai ke bawah — skala turbulen akan "
           "mematahkannya.",
           "Dipakai hanya untuk menunjukkan 5 menit tidak marginal; tidak dikutip sebagai angka "
           "dalam produk apa pun."])],
        ["Arsip bersifat per jam, sehingga tidak dapat langsung menyelesaikan apa pun di dalam "
         "satu jam — justru skala waktu tempat cuplikan 5 menit hidup.",
         "§12.2 spesifikasi menggantikan ekstrapolasi ini dengan pengukuran. "
         "Sumber: outputs/sq_structure_fit.csv."],
        page())

    S.slide_table(
        prs, "TEMUAN", "Urutan di dalam jam lebih menentukan daripada panjang cuplikan",
        ["Urutan", "Pasangan", "Selisih waktu (menit)", "CO₂ (ppm)", "CH₄ (ppb)", "CO (ppb)"],
        [["Berurutan", "30 m vs 100 m", "34,0", "3,66", "18,70", "13,76"],
         ["Berurutan", "70 m vs 100 m", "26,0", "3,13", "16,91", "11,93"],
         ["*Terkurung", "*30 m vs 100 m", "*6,2", "*1,34", "*9,89", "*5,57"],
         ["*Terkurung", "*70 m vs 100 m", "*1,8", "*0,65", "*6,24", "*2,89"]],
        ["Dua level yang dicuplik berselang Δt berbeda karena perubahan atmosfer itu sendiri "
         "selama Δt, bukan hanya karena gradien nyata. Besarnya: √(A(Δt/60)^(2H)).",
         "*Pengurungan tidak memakan biaya apa pun dan memangkas artefak CO₂ 30–100 m sebesar "
         "2,7 kali, dan 70–100 m sebesar 4,8 kali.*",
         "Kedua urutan memakai 41 menit sahih pada 100 m, 5 menit pada tiap level bawah, dan "
         "9 menit pembilasan. Sumber: outputs/sq_offset.csv."],
        page(), widths=[0.16, 0.22, 0.20, 0.14, 0.14, 0.14])

    # ---------------------------------------------------------- spesifikasi --
    S.slide_section(prs, "BAGIAN 4",
                    "Spesifikasi",
                    "Kerangka katup, anggaran waktu, kalibrasi dan produk data",
                    page())

    S.slide_table(
        prs, "SPESIFIKASI", "Kerangka waktu katup — identik di setiap jam setiap hari",
        ["Menit", "Katup", "Keadaan", "Durasi", "Catatan"],
        [["00.00–00.19", "*100 m", "sahih", "19 menit", "tanpa perpindahan di batas jam"],
         ["00.19–00.22", "30 m", "pembilasan", "3 menit", "dibuang"],
         ["00.22–00.27", "*30 m", "sahih", "5 menit", "cuplikan kesinambungan WDCGG"],
         ["00.27–00.30", "70 m", "pembilasan", "3 menit", "dibuang"],
         ["00.30–00.35", "*70 m", "sahih", "5 menit", ""],
         ["00.35–00.38", "100 m", "pembilasan", "3 menit", "dibuang"],
         ["00.38–01.00", "*100 m", "sahih", "22 menit", "berlanjut ke jam berikutnya"]],
        ["Jam dibuka dan ditutup pada 100 m, sehingga tidak diperlukan pembilasan di batas jam — "
         "katup tidak bergerak di sana. Tiga perpindahan per jam, 9 menit pembilasan, "
         "51 menit diarsipkan.",
         "Disinkronkan ke UTC dan disinkronkan ulang setiap awal jam, bukan pewaktu bebas. "
         "Sumber: outputs/sq_frame.csv."],
        page(), widths=[0.20, 0.13, 0.17, 0.15, 0.35])

    S.slide_table(
        prs, "SPESIFIKASI", "Anggaran waktu yang dihasilkan — dan setiap kendala terpenuhi",
        ["Level", "Menit sahih/jam", "Porsi data sahih", "Jam sahih/hari", "Rerata jam/hari"],
        [["*100 m", "*41", "*80,4 %", "*16,4", "*24"],
         ["70 m", "5", "9,8 %", "2,0", "24"],
         ["30 m", "5", "9,8 %", "2,0", "24"]],
        ["C1: 100 m mengambil 80 % waktu pengukuran. C2 dan C3: ketiga level menghasilkan "
         "24 rerata jam per hari tanpa aliasing.",
         "C4: sentroid tiap level bawah berada dalam 6,2 menit dari sentroid 100 m. "
         "C5: pembilasan 15 % dari jam, bukan 48 %. C6: siklus tujuh keadaan yang tetap.",
         "Sumber: outputs/sq_budget.csv."],
        page(), widths=[0.16, 0.21, 0.21, 0.21, 0.21])

    S.slide_pair(
        prs, "SPESIFIKASI", "Syarat sekuenser, kalibrasi, dan produk data",
        [("Sekuenser",
          ["Waktu perpindahan adalah menit UTC absolut, diturunkan ulang setiap jam — bukan "
           "rantai pewaktu bebas.",
           "Posisi katup adalah kolom data pada laju 1 Hz, dalam berkas yang sama dengan rasio "
           "campuran. Jangan berkas terpisah.",
           "Menit pembilasan ditandai, bukan dihapus.",
           "Durasi pembilasan adalah parameter konfigurasi."]),
         ("Kalibrasi",
          ["Tabung target: 20 menit harian, menggantikan blok 100 m 00.38–01.00 pada satu jam "
           "saja (disarankan 00 UTC).",
           "Biaya: 20 dari 984 menit sahih 100 m per hari — 2,0 %.",
           "Rangkaian kalibrasi penuh: mingguan, pada jam pemeliharaan terjadwal.",
           "Jam kalibrasi selalu sama, sehingga efeknya pada komposit diurnal adalah rumpang "
           "1-dari-24 yang diketahui."]),
         ("Produk data",
          ["Rerata jam per level, dengan simpangan baku, cacah sampel dan waktu sentroid "
           "cuplikan.",
           "Gradien per jam: 100 m dikurangi level bawah, dengan 100 m diinterpolasi linear ke "
           "sentroid level bawah.",
           "Arsipkan simpangan baku dalam-cuplikan — itu satu-satunya informasi pengguna hilir "
           "tentang keterwakilan cuplikan 5 menit."])],
        ["Karena blok 100 m dibelah mengelilingi level bawah, nilai 100 m dapat diinterpolasi "
         "melintasi rumpang, yang menghapus bagian linear dari laju perubahan secara eksak.",
         "Sisa setelah interpolasi bersifat orde-dua dan jauh di bawah 1,34 ppm pada Tabel 5."],
        page())

    # ------------------------------------------------------- yang belum pasti --
    S.slide_quote(
        prs, "BATAS",
        "Tiga angka di sini disimpulkan, bukan diukur pada sistem terpasang",
        ["12.1 Waktu pembilasan — pindahkan 100 m → 30 m berulang kali pada jam menjelang "
         "fajar, saat gradien terbesar, dengan rekaman 1 Hz penuh. Jika melampaui 3 menit, "
         "aliran bypass terlalu rendah atau ada volume mati: perbaiki manifold, jangan "
         "memperpanjang pembilasan.",
         "12.2 Keterwakilan cuplikan 5 menit — jalankan 100 m terus-menerus selama satu minggu "
         "pada 1 Hz, lalu hitung selisih tiap jendela 5 menit terhadap rerata jamnya, sebagai "
         "fungsi jam. Ini menggantikan ekstrapolasi §6 dengan pengukuran.",
         "12.3 Loncatan inlet 30 m — jalankan inlet 30 m lama dan inlet 30 m menara baru secara "
         "paralel minimal satu bulan. Ini satu-satunya cara memisahkan loncatan akibat "
         "pemindahan inlet dari perubahan atmosferik nyata, dan tidak dapat dilakukan surut."],
        page())

    S.slide_pair(
        prs, "OPSIONAL", "Penguatan malam hari — ditawarkan, bukan dispesifikasikan",
        [("Usulannya",
          ["20.00–07.00 waktu setempat: 8 menit sahih pada 30 m dan 70 m.",
           "100 m turun ke 35 menit sahih — 69 % data sahih.",
           "07.00–20.00: kerangka baku Tabel 6."]),
         ("Mengapa mungkin bermanfaat",
          ["Informasi gradien terpusat antara 20.00 dan 07.00.",
           "Tidak ada kendala yang dilanggar: setiap jam tetap memuat setiap level, sehingga "
           "aliasing tetap mustahil."]),
         ("Mengapa belum dispesifikasikan",
          ["Menambah kerumitan sekuenser dan QC untuk keuntungan yang nyata tetapi belum "
           "terkuantifikasi.",
           "Saran: jalankan kerangka seragam Tabel 6 selama satu tahun, lalu putuskan dari "
           "gradien yang terukur."])],
        ["Bentuk diurnal sama di DJF dan JJA, sehingga penguatan ini adalah pilihan tetap "
         "berdasarkan jam, bukan mode musiman."],
        page())

    S.slide_table(
        prs, "RINGKASAN", "Spesifikasi dalam satu halaman",
        ["Butir", "Nilai"],
        [["Siklus", "*1 jam, identik setiap jam, disinkronkan UTC"],
         ["Urutan", "*100 m, 30 m, 70 m, 100 m (terkurung)"],
         ["Pembilasan tiap perpindahan", "3 menit, diarsipkan dan ditandai"],
         ["Cuplikan sahih, 30 m dan 70 m", "5 menit; menit 22–27 dan 30–35"],
         ["Cuplikan sahih, 100 m", "*41 menit, menit 00–19 dan 38–60"],
         ["Aliran bypass, semua saluran", "*≥ 5 slpm, terus-menerus"],
         ["Gas target", "20 menit harian, dari blok 100 m pukul 00 UTC"],
         ["Rerata jam per level per hari", "*24"]],
        ["Semua angka dapat direproduksi dari berkas mentah.",
         "scripts/a36_sequencer.py → outputs/sq_*.csv · scripts/a37_sequencer_figs.py "
         "→ figures/sq1–sq3."],
        page(), widths=[0.42, 0.58])

    return prs


def main():
    i18n.set_lang("id")           # picks the _id figures through a19._fig()
    prs = build()
    prs.save(str(OUT))
    n = len(prs.slides._sldIdLst)
    print(f"wrote {OUT.relative_to(ROOT)}  ({n} slides)")


if __name__ == "__main__":
    main()
