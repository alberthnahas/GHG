"""Populate the integrated BARRA feasibility appendix from audited CSVs."""
from pathlib import Path
import re
import pandas as pd
from a40_bkt_refinement_report import markdown_table

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/hysplit/barra/quality"


def build_barra_sections():
    quality=pd.read_csv(OUT/"field_quality.csv").set_index("variable")
    scope=pd.read_csv(OUT/"scope.csv").iloc[0]
    profile=pd.read_csv(OUT/"bkt_profile.csv")
    native=pd.read_csv(OUT/"native_confirmation.csv")
    if len(native)!=3 or not native.confirmed.all():raise ValueError("Native gap checks incomplete")
    rows=[]
    for level in (925,850):
        q=quality.loc[f"wa{level}"]
        for family in ("ua","va","wa","ta","hus","zg"):
            other=quality.loc[f"{family}{level}"]
            for key in ("aboveground_n_margin1hpa","aboveground_missing_margin1hpa","aboveground_missing_margin10hpa"):
                if other[key]!=q[key]:raise ValueError("Field-specific gap counts need separate reporting")
        rows.append([str(level),f"{int(q.aboveground_n_margin1hpa):,}",
                     f"{int(q.aboveground_missing_margin1hpa):,}",
                     f"{q.aboveground_missing_percent_margin1hpa:.2f}",
                     f"{int(q.aboveground_missing_margin10hpa):,}"])
    z=profile[profile.variable.eq("zg850")].value-scope.bkt_terrain_m
    example=native[native.variable.eq("wa925")].iloc[0]
    v={"B_GRID":f"{scope.grid_spacing_deg:.2f}","B_WEST":f"{scope.west:.2f}","B_EAST":f"{scope.east:.2f}",
       "B_SOUTH":f"{abs(scope.south):.2f}","B_NORTH":f"{scope.north:.2f}",
       "B_DATE":pd.Timestamp(scope.start_utc).strftime("%-d %B %Y"),
       "B_START":pd.Timestamp(scope.start_utc).strftime("%H:%M"),"B_END":pd.Timestamp(scope.end_utc).strftime("%H:%M"),
       "B_TIMES":str(int(scope.time_count)),"B_NLAT":str(int(scope.lat_count)),"B_NLON":str(int(scope.lon_count)),
       "B_LAT":f"{abs(scope.bkt_grid_lat):.2f}","B_LON":f"{scope.bkt_grid_lon:.2f}",
       "B_TERRAIN":f"{scope.bkt_terrain_m:,.0f}","B_PS_MIN":f"{scope.bkt_ps_min_hpa:.1f}",
       "B_PS_MAX":f"{scope.bkt_ps_max_hpa:.1f}","B_AGL_MIN":f"{z.min():.0f}","B_AGL_MAX":f"{z.max():.0f}",
       "B_NATIVE_N":str(len(native)),"B_EXAMPLE_LEVEL":f"{example.pressure_level_hpa:.0f}",
       "B_EXAMPLE_PS":f"{example.surface_pressure_hpa:.2f}","B_LOWER_LEVEL":"925","B_UPPER_LEVEL":"850",
       "B_GAP_TABLE":markdown_table(["Level (hPa)","Above-ground pairs","Missing pairs","Missing (%)","Gaps: 10 hPa margin"],rows)}
    text=(ROOT/"docs/BKT_BARRA_Report_appendix.md").read_text()
    text=re.sub(r"\{\{([A-Z0-9_]+)\}\}",lambda m:v[m[1]],text)
    v["BARRA_APPENDIX"]=text
    return v
