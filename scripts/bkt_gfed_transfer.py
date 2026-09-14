#!/usr/bin/env python3
"""Read public GFED SFTP credentials in memory; never persist or log them."""
import argparse
from pathlib import Path
import re
import subprocess
import urllib.request
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bkt_sources/gfed51"


def transfer(remote: str, output: Path | None = None, fast: bool = False, subset: bool = False,
             day_start: int = 23, day_end: int = 26, bounds=(84,-11,117,11), gases=("CO2","CH4","CO")):
    DATA.mkdir(parents=True, exist_ok=True)
    url = "https://www.globalfiredata.org/ancill/GFED5_SFTP_info.txt"
    with urllib.request.urlopen(url, timeout=30) as r:
        text = r.read().decode()
    values = {k.lower(): v.strip() for k, v in re.findall(
        r"^(Server|Port|Username|PW):\s*(.+)$", text, re.M)}
    known = DATA / "known_hosts"
    if not known.exists():
        keys = subprocess.run(["ssh-keyscan", "-p", values["port"], values["server"]],
                              capture_output=True, text=True, check=True)
        # Public host key pinned on first access, then strict matching thereafter.
        known.write_text(keys.stdout)
    if fast or subset:
        import paramiko
        if output is None: raise ValueError("Fast transfer requires an output path")
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(str(known))
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        ssh.connect(values["server"], port=int(values["port"]), username=values["username"],
                    password=values["pw"], look_for_keys=False, allow_agent=False, timeout=30)
        try:
            with ssh.open_sftp() as sftp:
                expected = sftp.stat(remote).st_size
                if subset:
                    import h5py
                    import numpy as np
                    with sftp.open(remote, "rb") as handle, h5py.File(handle, "r") as source:
                        lat,lon,time = source["lat"][:], source["lon"][:],source["time"][:]
                        west,south,east,north=bounds
                        yi=np.flatnonzero((lat>=south)&(lat<=north));xi=np.flatnonzero((lon>=west)&(lon<=east))
                        if not 1 <= day_start <= day_end <= len(time): raise ValueError("Invalid daily subset")
                        days=slice(day_start-1,day_end)
                        values_out={"lat":lat[yi],"lon":lon[xi],"time":time[days]}
                        attrs={k: str(v.decode() if isinstance(v,bytes) else v) for k,v in source.attrs.items()}
                        units={}
                        for gas in gases:
                            # Select only requested days and region from global compressed chunks.
                            values_out[gas]=source[gas][days,yi[0]:yi[-1]+1,xi[0]:xi[-1]+1]
                            units[gas]=source[gas].attrs["units"].decode()
                            print(f"Read regional GFED {gas}, days {day_start}–{day_end}",flush=True)
                    np.savez_compressed(output,**values_out)
                    metadata=dict(dataset="GFED5.1 monthly regional subset" if "/Monthly/" in remote else "GFED5.1 daily regional subset", source="https://www.globalfiredata.org/data.html",
                                  remote_path=remote, remote_bytes=expected, source_attributes=attrs, units=units,
                                  time_units="hours since 1800-01-01", source_interval_indices=list(range(day_start-1,day_end)), bounds=list(bounds),
                                  sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                                  retrieved_at_utc=datetime.now(timezone.utc).isoformat())
                    output.with_suffix(output.suffix+".json").write_text(json.dumps(metadata,indent=2)+"\n")
                    return
                temporary = output.with_suffix(output.suffix + ".download")
                sftp.get(remote, str(temporary), max_concurrent_prefetch_requests=16)
                if temporary.stat().st_size != expected: raise ValueError("GFED incomplete transfer")
                temporary.replace(output)
        finally:
            ssh.close()
        metadata = dict(dataset="GFED5.1 daily", source="https://www.globalfiredata.org/data.html",
                        remote_path=remote, bytes=expected,
                        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                        host_verification="SSH host keys pinned on first access; strict subsequent matching")
        output.with_suffix(output.suffix+".json").write_text(json.dumps(metadata, indent=2)+"\n")
        print(f"Acquired {output.name}: {expected:,} bytes", flush=True)
        return
    cfg = (f'url = "sftp://{values["server"]}:{values["port"]}/{remote.lstrip("/")}"\n'
           f'user = "{values["username"]}:{values["pw"]}"\n'
           f'knownhosts = "{known}"\n')
    command = ["curl", "--config", "-", "--silent", "--show-error", "--max-time", "1800"]
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        command += ["--output", str(output), "--continue-at", "-"]
    result = subprocess.run(command, input=cfg, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"GFED transfer failed (curl status {result.returncode})")
    print(result.stdout if output is None else f"Acquired {output.name}", flush=True)


def inspect_public(remote: str):
    """Inspect GFED directory or NetCDF schema without disclosing access values."""
    import paramiko
    import h5py
    with urllib.request.urlopen("https://www.globalfiredata.org/ancill/GFED5_SFTP_info.txt",timeout=30) as response:
        text=response.read().decode()
    credentials={k.lower():v.strip() for k,v in re.findall(r"^(Server|Port|Username|PW):\s*(.+)$",text,re.M)}
    ssh=paramiko.SSHClient();ssh.load_host_keys(str(DATA/"known_hosts"))
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
    ssh.connect(credentials["server"],port=int(credentials["port"]),username=credentials["username"],password=credentials["pw"],look_for_keys=False,allow_agent=False,timeout=30)
    try:
        with ssh.open_sftp() as sftp:
            if remote.endswith(".nc"):
                with sftp.open(remote,"rb") as handle,h5py.File(handle,"r") as source:
                    def show(name,item):
                        if isinstance(item,h5py.Dataset): print(name,item.shape,dict(item.attrs))
                    source.visititems(show)
            else:
                for item in sftp.listdir_attr(remote): print(item.filename,item.st_size)
    finally: ssh.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("remote", nargs="?", default="")
    p.add_argument("--output", type=Path)
    p.add_argument("--fast", action="store_true", help="Use existing system Paramiko for bounded SFTP prefetch")
    p.add_argument("--subset", action="store_true", help="Acquire only CO2/CH4/CO, four days and regional grid")
    p.add_argument("--day-start",type=int,default=23)
    p.add_argument("--day-end",type=int,default=26)
    p.add_argument("--bounds",type=float,nargs=4,default=(84,-11,117,11))
    p.add_argument("--gases",nargs="+",choices=["CO2","CH4","CO"],default=("CO2","CH4","CO"))
    p.add_argument("--inspect",action="store_true")
    p.add_argument("--interface",default=None,help="pin the SFTP session to one network device (for example wlp0s20f3)")
    a = p.parse_args()
    if a.interface:
        # Same device pinning as a76.bind_interface; inlined because this script runs under the system Python.
        import socket
        _connect = socket.socket.connect
        def _pinned(self, address, _dev=a.interface.encode()):
            if self.family == socket.AF_INET and self.type == socket.SOCK_STREAM:
                self.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, _dev)
            return _connect(self, address)
        socket.socket.connect = _pinned
        print(f"TCP connections bound to {a.interface}", flush=True)
    if a.inspect: inspect_public(a.remote)
    else: transfer(a.remote, a.output, a.fast, a.subset,a.day_start,a.day_end,a.bounds,a.gases)
