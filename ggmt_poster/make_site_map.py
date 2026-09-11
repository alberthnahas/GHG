import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import geopandas as gpd


SOURCE = "/home/workstation-llm/.venv/lib/python3.14/site-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp"
INDONESIA = "/run/media/workstation-llm/HDD2/.assets/indonesia_38prov.geojson"
OUTPUT = "/run/media/workstation-llm/HDD2/GHG_Analysis/.codex_tmp/ggmt_poster/assets/five_site_map.png"

sites = [
    ("BKT", 100.318, -0.202, "Bukit Kototabang", "Remote mountain, GAW Global"),
    ("JMB", 103.649, -1.611, "Jambi", "Lowland peat and plantation"),
    ("KMY", 106.850, -6.155, "Kemayoran", "Jakarta megacity core"),
    ("BRI", 120.030, -1.200, "Bariri", "Montane rainforest"),
    ("SRG", 131.288, -0.862, "Sorong", "Coastal small city"),
]

world = gpd.read_file(SOURCE).to_crs("EPSG:4326")
region = world.cx[93:143, -13:9]
indonesia = gpd.read_file(INDONESIA).to_crs("EPSG:4326")
indonesia.geometry = indonesia.geometry.make_valid()

fig, ax = plt.subplots(figsize=(10.6, 4.15), dpi=300)
fig.patch.set_facecolor("white")
ax.set_facecolor("#EEF7F8")
region.plot(ax=ax, color="#D8DCDA", edgecolor="#96A4A7", linewidth=0.42, zorder=1)
indonesia.plot(ax=ax, color="#F7F7F5", edgecolor="#8A9A9D", linewidth=0.36, zorder=2)

offsets = {
    "BKT": (-0.6, 1.55),
    "JMB": (0.0, -2.1),
    "KMY": (0.3, -2.0),
    "BRI": (0.3, 1.55),
    "SRG": (-0.2, 1.55),
}
for code, lon, lat, name, profile in sites:
    ax.scatter(lon, lat, s=82, color="#D95F36", edgecolor="white", linewidth=1.2, zorder=4)
    dx, dy = offsets[code]
    label_x = lon + dx
    label_y = lat + dy
    ax.annotate(
        f"{code}  {name}",
        xy=(lon, lat),
        xytext=(label_x, label_y),
        fontsize=7.5,
        fontweight="bold",
        color="#173D46",
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="#64777B", linewidth=0.65),
        zorder=5,
    )
    ax.text(
        label_x,
        label_y - 0.62,
        profile,
        fontsize=6.6,
        color="#465D63",
        ha="left",
        va="center",
        zorder=5,
    )

ax.set_xlim(94, 142)
ax.set_ylim(-12, 7)
ax.set_xticks([100, 110, 120, 130, 140])
ax.set_yticks([-10, -5, 0, 5])
ax.set_xticklabels(["100°E", "110°E", "120°E", "130°E", "140°E"], fontsize=8, color="#52676C")
ax.set_yticklabels(["10°S", "5°S", "0°", "5°N"], fontsize=8, color="#52676C")
ax.grid(color="#CAD8DA", linewidth=0.45, linestyle="--", zorder=0)
for spine in ax.spines.values():
    spine.set_color("#8BA5A9")
    spine.set_linewidth(0.7)
ax.tick_params(length=0)
plt.subplots_adjust(left=0.055, right=0.995, top=0.99, bottom=0.08)
plt.savefig(OUTPUT, dpi=300, bbox_inches="tight", pad_inches=0.03)
plt.close(fig)
print(OUTPUT)
