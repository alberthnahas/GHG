"""Read the verified GFSQ latitude–longitude ARL records without regridding."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


class GFSReader:
    """Bounded ARL metadata and record reader for this native hybrid archive."""
    records_per_time = 349

    def __init__(self, path: Path):
        self.path = Path(path)
        with self.path.open("rb") as stream:
            header = stream.read(50).decode("ascii")
            index = stream.read(108).decode("ascii")
        if header[14:18] != "INDX" or index[:4] != "GFSQ":
            raise ValueError("Expected native GFSQ ARL index")
        self.nx, self.ny, self.nz = [int(index[93+i*3:96+i*3]) for i in range(3)]
        grid = [float(index[9+i*7:16+i*7]) for i in range(12)]
        if self.nz != 56 or int(index[102:104]) != 4 or grid[2:4] != [.25,.25]:
            raise ValueError("Unsupported GFSQ grid or vertical definition")
        self.lat = grid[9] + np.arange(self.ny)*.25
        self.lon = grid[10] + np.arange(self.nx)*.25
        if not np.isclose(self.lat[-1],grid[0]) or not np.isclose(self.lon[-1],grid[1]):
            raise ValueError("GFSQ coordinate endpoints do not reconcile")
        self.record_size = self.nx*self.ny+50
        if self.path.stat().st_size != self.record_size*self.records_per_time*8:
            raise ValueError("Incomplete or unexpected daily GFSQ ARL file")
        self.records: dict[tuple[pd.Timestamp,str,int],tuple[int,str]] = {}
        with self.path.open("rb") as stream:
            for r in range(self.records_per_time*8):
                offset = r*self.record_size
                stream.seek(offset)
                raw = stream.read(50).decode("ascii")
                stamp = pd.Timestamp(year=2000+int(raw[:2]),month=int(raw[2:4]),
                    day=int(raw[4:6]),hour=int(raw[6:8]))
                key = (stamp,raw[14:18],int(raw[10:12]))
                if key in self.records:
                    raise ValueError("Duplicate ARL time-variable-level key")
                self.records[key] = (offset,raw)
        times = sorted({k[0] for k in self.records})
        expected = list(pd.date_range(pd.Timestamp(self.path.name[:8]),periods=8,freq="3h"))
        if times != expected:
            raise ValueError("Incomplete or mismatched ARL day")
        self.times = times
        for stamp in times:
            for var in ("TEMP","UWND","VWND","WWND","RELH","PRES"):
                if {k[2] for k in self.records if k[:2] == (stamp,var)} != set(range(1,56)):
                    raise ValueError(f"Missing GFSQ vertical records for {var}")

    def field(self, stamp: pd.Timestamp, variable: str, level: int=0) -> np.ndarray:
        offset, header = self.records[(pd.Timestamp(stamp),variable,level)]
        with self.path.open("rb") as stream:
            stream.seek(offset+50)
            values = np.frombuffer(stream.read(self.nx*self.ny),dtype=np.uint8)
        return unpack(values.reshape(self.ny,self.nx), int(header[18:22]),float(header[36:50]))

    def point(self, stamp: pd.Timestamp, variable: str, level: int,
              lat: float, lon: float, method: str="bilinear") -> float:
        if not self.lat[0] <= lat <= self.lat[-1] or not self.lon[0] <= lon <= self.lon[-1]:
            raise ValueError("Requested point outside meteorological domain")
        field = self.field(stamp,variable,level)
        y,x = (lat-self.lat[0])/.25, (lon-self.lon[0])/.25
        if method == "nearest":
            return float(field[int(np.floor(y+.5)),int(np.floor(x+.5))])
        if method != "bilinear":
            raise ValueError("Unknown spatial sampling method")
        j,i = min(int(y),self.ny-2),min(int(x),self.nx-2)
        fy,fx = y-j,x-i
        return float((1-fy)*((1-fx)*field[j,i]+fx*field[j,i+1])+
                     fy*((1-fx)*field[j+1,i]+fx*field[j+1,i+1]))

    def profile(self, stamp: pd.Timestamp, lat: float, lon: float,
                method: str="bilinear") -> pd.DataFrame:
        rows = [{"level":level, **{v:self.point(stamp,v,level,lat,lon,method)
                 for v in ("PRES","TEMP","UWND","VWND","RELH")}} for level in range(1,56)]
        result = pd.DataFrame(rows)
        if not np.isfinite(result.to_numpy()).all() or not (np.diff(result.PRES)<0).all():
            raise ValueError("Nonfinite or nonmonotonic GFS pressure profile")
        # Archive pressure is hPa, temperature K, winds m/s, relative humidity %.
        if not result.PRES.between(0,1100).all() or not result.TEMP.between(130,340).all():
            raise ValueError("Unexpected pressure or temperature units/range")
        return result


def unpack(packed: np.ndarray, exponent: int, first: float) -> np.ndarray:
    """NOAA S141 difference packing; each row begins from prior row's first."""
    delta = (packed.astype(float)-127)*2.**(exponent-7)
    starts = np.r_[first,first+np.cumsum(delta[:-1,0])]
    return np.cumsum(delta,axis=1)+starts[:,None]


def pressure_interpolate(profile: pd.DataFrame, pressure_hpa: float, variable: str) -> float:
    """Interpolate linearly in log pressure; never extrapolate below/above data."""
    p = profile.PRES.to_numpy()
    if not p.min() <= pressure_hpa <= p.max():
        return float("nan")
    return float(np.interp(np.log(pressure_hpa),np.log(p[::-1]),profile[variable].to_numpy()[::-1]))


class ARLReader:
    """Generic reader for one ARL file on a lat-lon grid (GFS, ERA5 or other).

    The index record's level table gives the record count per time period and
    the variable names per level, so no model-specific constants are needed.
    Only whole-hour timestamps and level 0 (surface) or numbered levels are
    addressed; values decode with the same S141 unpacking as ``GFSReader``.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        with self.path.open("rb") as stream:
            label = stream.read(50).decode("ascii")
            index = stream.read(108).decode("ascii")
            if label[14:18] != "INDX":
                raise ValueError("Expected an ARL index record")
            self.model = index[:4]
            self.nx, self.ny, self.nz = [int(index[93 + i * 3:96 + i * 3]) for i in range(3)]
            grid = [float(index[9 + i * 7:16 + i * 7]) for i in range(12)]
            self.dlat, self.dlon = grid[3], grid[2]
            self.lat = grid[9] + np.arange(self.ny) * self.dlat
            self.lon = grid[10] + np.arange(self.nx) * self.dlon
            table = stream.read(self.nz * (8 + 8 * 40)).decode("ascii", "replace")
        self.levels: list[tuple[float, list[str]]] = []
        pos = 0
        for _ in range(self.nz):
            level = float(table[pos:pos + 6]); count = int(table[pos + 6:pos + 8]); pos += 8
            names = [table[pos + 8 * k:pos + 8 * k + 4] for k in range(count)]; pos += 8 * count
            self.levels.append((level, names))
        self.records_per_time = 1 + sum(len(n) for _, n in self.levels)
        self.record_size = self.nx * self.ny + 50
        if self.path.stat().st_size % (self.record_size * self.records_per_time):
            raise ValueError("ARL file size is not a whole number of time periods")
        self.records: dict[tuple[pd.Timestamp, str, int], tuple[int, str]] = {}
        with self.path.open("rb") as stream:
            for r in range(self.path.stat().st_size // self.record_size):
                offset = r * self.record_size
                stream.seek(offset)
                raw = stream.read(50).decode("ascii", "replace")
                if raw[14:18] == "INDX":
                    continue
                stamp = pd.Timestamp(year=2000 + int(raw[:2]), month=int(raw[2:4]), day=int(raw[4:6]),
                                     hour=int(raw[6:8]))
                self.records[(stamp, raw[14:18], int(raw[10:12]))] = (offset, raw)
        self.times = sorted({k[0] for k in self.records})

    def field(self, stamp: pd.Timestamp, variable: str, level: int = 0) -> np.ndarray:
        offset, header = self.records[(pd.Timestamp(stamp), variable, level)]
        with self.path.open("rb") as stream:
            stream.seek(offset + 50)
            values = np.frombuffer(stream.read(self.nx * self.ny), dtype=np.uint8)
        return unpack(values.reshape(self.ny, self.nx), int(header[18:22]), float(header[36:50]))

    def point(self, stamp: pd.Timestamp, variable: str, level: int, lat: float, lon: float,
              method: str = "bilinear") -> float:
        if not self.lat[0] <= lat <= self.lat[-1] or not self.lon[0] <= lon <= self.lon[-1]:
            raise ValueError("Requested point outside meteorological domain")
        field = self.field(stamp, variable, level)
        y, x = (lat - self.lat[0]) / self.dlat, (lon - self.lon[0]) / self.dlon
        if method == "nearest":
            return float(field[int(np.floor(y + .5)), int(np.floor(x + .5))])
        j, i = min(int(y), self.ny - 2), min(int(x), self.nx - 2)
        fy, fx = y - j, x - i
        return float((1 - fy) * ((1 - fx) * field[j, i] + fx * field[j, i + 1])
                     + fy * ((1 - fx) * field[j + 1, i] + fx * field[j + 1, i + 1]))
