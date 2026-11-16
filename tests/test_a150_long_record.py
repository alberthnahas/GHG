"""Invariants of the a150 long-record receptor table and meteorology lists."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import a150_hysplit_long_record as L  # noqa: E402
import a127_hysplit_2025_2026 as H  # noqa: E402


def test_grid_is_the_a127_2025_grid():
    days = H.window_days("co2_25")
    assert L.on_grid(pd.Series(days)).all()
    assert not L.on_grid(pd.Series(days + pd.Timedelta(days=1))).any()


def test_explicit_met_list_equals_a37_default():
    import a37_bkt_footprint as m
    for s in pd.to_datetime(["2012-03-01T06:00", "2026-01-02T06:00", "2009-10-30T06:00"]):
        assert L.weeks_for(s) == m.required_met_names(s, H.HOURS_BACK)
    assert "gdas1.feb12.w5" in L.weeks_for(pd.Timestamp("2012-03-01T06:00"))


def test_receptor_table():
    t = L.receptors()
    assert not t.duplicated(["station", "time_utc"]).any()
    assert (t.time_utc.dt.hour == 6).all()
    assert (t.co2_hours.ge(2) | t.ch4_hours.ge(2)).all()
    assert L.on_grid(t.time_utc.dt.normalize()).all() or (~t.on_grid).any()
    for ph, spans in L.PHASES.items():
        x = t[t.phase == ph]
        inside = pd.Series(False, index=x.index)
        for st, a, b in spans:
            inside |= (x.station == st) & (x.time_utc >= a) & (x.time_utc <= pd.Timestamp(b) + pd.Timedelta(hours=23))
        assert inside.all()
    # no overlap with the a127 runs
    a127 = pd.read_csv(H.TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    assert not set(zip(t.station, t.time_utc)) & set(zip(a127.station, a127.time_utc))


def test_configuration_is_a127():
    from dataclasses import asdict
    for code in ("BKT", "JMB"):
        c = asdict(H.config(code))
        assert (c["particles"], c["hours_back"], c["seed"], c["receptor_height_m_agl"]) == (2000, 120, 0, 100.0)
        assert (c["grid_spacing_deg"], c["grid_span_lat_deg"], c["grid_span_lon_deg"]) == (0.25, 60, 100)
