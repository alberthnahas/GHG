#!/usr/bin/env python3
"""Scientific figures from the GFS/source evidence tables and unblurred fields."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, SymLogNorm
import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
from a43_bkt_source_analysis import OUT, TABLES, ROOT
from a38_bkt_footprint_report import apply_chart_style, haversine_and_bearing, BLUE, ORANGE
from bkt_footprint_spatial import basemap, boundary_lines, indonesia_boundaries, display_surface, cell_area_km2, detailed_neighbors

FIG = OUT / "figures"
EXTENT = [97.5, 113, -8.5, 4]
SECTOR_LABELS = {
    "AGRICULTURE": "Agriculture", "BUILDINGS": "Buildings",
    "FUEL_EXPLOITATION": "Fuel exploitation", "IND_COMBUSTION": "Industrial combustion",
    "IND_PROCESSES": "Industrial processes", "POWER_INDUSTRY": "Power industry",
    "TRANSPORT": "Transport", "WASTE": "Waste",
}


def export(fig, stem):
    from matplotlib.text import Text
    # Keep typography consistent at the report's final text-block width.
    fig.canvas.draw()
    scale=fig.get_figwidth()/7.2
    for artist in fig.findobj(match=Text):
        artist.set_fontsize(artist.get_fontsize()*scale)
    fig.savefig(FIG / f"{stem}.png", dpi=300, facecolor="white")
    fig.savefig(FIG / f"{stem}.pdf", dpi=300, facecolor="white")
    plt.close(fig)


def heading(fig, title, highlight, left=.10):
    fig.text(left,.97,title,fontsize=12,weight="bold",va="top")
    fig.text(left,.915,highlight,fontsize=9,color="#52616A",va="top")


def map_axis(fig, rect, provinces):
    ax=fig.add_axes(rect, projection=ccrs.PlateCarree())
    # Dense continuous fields are publication-resolution rasters; boundaries and labels stay vector.
    ax.set_rasterization_zorder(3)
    ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
    basemap(ax,provinces,detailed=True)
    boundary_lines(ax,provinces)
    ax.plot(100.318,-.202,"*",ms=10,color="#007A9D",markeredgecolor="white",zorder=8,transform=ccrs.PlateCarree())
    ax.text(100.52,.12,"BKT",fontsize=9,weight="bold",color="#005D7B",zorder=8,transform=ccrs.PlateCarree())
    g=ax.gridlines(draw_labels=True,linewidth=.35,alpha=.4,linestyle="--")
    from matplotlib.ticker import FixedLocator
    g.xlocator=FixedLocator([100,104,108,112])
    g.ylocator=FixedLocator([-8,-4,0,4])
    g.top_labels=g.right_labels=False
    g.xlabel_style=g.ylabel_style={"size":9*fig.get_figwidth()/7.2}
    return ax


def map_note(fig):
    fig.text(.10,.022,"Indonesia: provincial GeoJSON · neighbors: geoBoundaries / © OpenStreetMap contributors.\n"
             "WGS 84 · country-source credits in report · boundaries are not atmospheric barriers.",fontsize=8,color="#52616A")


def footprint_maps():
    provinces,boundary=indonesia_boundaries()
    _,neighbors=detailed_neighbors()
    (OUT / "cartographic_provenance.json").write_text(json.dumps(dict(indonesia=boundary,neighbors=neighbors),indent=2)+"\n")
    fields={}
    for driver in ("GFS","GDAS"):
        with xr.open_dataset(OUT / f"{driver}_ensemble.nc") as ds:
            fields[driver]=ds.footprint_sensitivity.sum("time").load()
    sigma=float(pd.read_csv(TABLES/"driver_comparison.csv").gaussian_sigma_cells.iloc[0])
    limits=(1e-7,3e-2)
    fig=plt.figure(figsize=(9,7.1))
    ax=map_axis(fig,[.10,.20,.82,.64],provinces)
    f=fields["GFS"]
    y,x,d=display_surface(f.values,f.lat.values,f.lon.values,sigma)
    mesh=ax.contourf(x,y,np.ma.masked_less_equal(d,0),levels=np.geomspace(*limits,100),
                     norm=LogNorm(*limits),cmap="YlOrRd",extend="max",transform=ccrs.PlateCarree(),zorder=2)
    cb=fig.colorbar(mesh,cax=fig.add_axes([.20,.15,.62,.022]),orientation="horizontal",ticks=[1e-7,1e-5,1e-3,1e-2])
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²] · log scale",fontsize=9)
    heading(fig,"Surface-flux sensitivity upstream of Bukit Kototabang",
            "72 h ending 26 September 2019 01:00 UTC · GFS 0.25° meteorology\n"
            f"Three seeded runs; 0.1° output · linear display interpolation; Gaussian σ = {sigma:g} cells")
    map_note(fig)
    export(fig,"figure_03_footprint")
    area=cell_area_km2(y,x)
    inside=(y[:,None]>=EXTENT[2])&(y[:,None]<=EXTENT[3])&(x[None,:]>=EXTENT[0])&(x[None,:]<=EXTENT[1])
    pd.DataFrame([dict(raw_sum=float(f.sum()),display_integral=float((d*area).sum()),
         below_color_scale_percent=float(100*(d*area)[d<limits[0]].sum()/float(f.sum())),
         outside_frame_percent=float(100*(d*area)[~inside].sum()/float(f.sum()))) ]).to_csv(TABLES/"display_integrity.csv",index=False)
    fig=plt.figure(figsize=(10,6.8))
    for k,driver in enumerate(("GDAS","GFS")):
        ax=map_axis(fig,[.065+k*.49,.26,.43,.52],provinces)
        f=fields[driver]
        y,x,d=display_surface(f.values,f.lat.values,f.lon.values,0)
        mesh=ax.contourf(x,y,np.ma.masked_less_equal(d,0),levels=np.geomspace(*limits,80),norm=LogNorm(*limits),cmap="YlOrRd",extend="max",transform=ccrs.PlateCarree(),zorder=2)
        ax.set_title(f"({'ab'[k]}) {driver} {'1°' if driver=='GDAS' else '0.25°'}",fontsize=10)
    cb=fig.colorbar(mesh,cax=fig.add_axes([.23,.16,.54,.025]),orientation="horizontal",ticks=[1e-7,1e-5,1e-3,1e-2])
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²] · log scale",fontsize=9)
    heading(fig,"Meteorological drivers produce different transport estimates",
            "Same receptor, release height, particle ensemble and output grid; identical map scales.\n"
            "The comparison changes meteorological model and vertical representation as well as grid spacing.",left=.065)
    map_note(fig)
    export(fig,"figure_04_driver_maps")


def transport_charts():
    lag=pd.read_csv(TABLES/"lag_by_driver.csv")
    summary=pd.read_csv(TABLES/"transport_summary.csv").set_index("run")
    fig,axes=plt.subplots(1,2,figsize=(8,4.8))
    fig.subplots_adjust(left=.10,right=.98,bottom=.18,top=.76,wspace=.34)
    for driver,color,style in (("GFS",BLUE,"-"),("GDAS",ORANGE,"--")):
        sub=lag[lag.driver.eq(driver)].sort_values("lag_hours")
        axes[0].plot(sub.lag_hours,sub.share_percent.cumsum(),color=color,ls=style,label=driver)
        with xr.open_dataset(OUT/f"{driver}_ensemble.nc") as ds:
            f=ds.footprint_sensitivity.sum("time").load()
        lat,lon=np.meshgrid(f.lat.values,f.lon.values,indexing="ij")
        distance,_=haversine_and_bearing(lat,lon,-.202,100.318)
        order=np.argsort(distance.ravel())
        axes[1].plot(distance.ravel()[order],100*np.cumsum(f.values.ravel()[order])/float(f.sum()),color=color,ls=style,label=driver)
    for ax in axes:
        ax.set(ylim=(0,101),ylabel="Cumulative sensitivity (%)")
        ax.axhline(50,color=".6",ls=":",lw=.8); ax.grid(axis="y",alpha=.2)
    axes[0].set(xlabel="Backward lag (h)",xlim=(0,72));axes[1].set(xlabel="Distance from BKT (km)",xlim=(0,1000))
    axes[0].legend(frameon=False)
    heading(fig,"Transport age and distance depend on the meteorological driver",
            "Cumulative shares use unsmoothed ensemble coefficients, not the rendered map.\n"
            "The 72-hour integration omits older source influence.")
    export(fig,"figure_05_lag_distance")
    fig,axes=plt.subplots(1,2,figsize=(8,4.8));fig.subplots_adjust(left=.12,right=.97,bottom=.18,top=.76,wspace=.40)
    for j,metric in enumerate(("sensitivity_sum","se_beyond25_share_percent")):
        for i,driver in enumerate(("GDAS","GFS")):
            seeds=summary[(summary.driver==driver)&summary.member.isin(("n10000_s0","n10000_sm10","n10000_sm20"))][metric]
            height=summary.loc[f"{driver}_n10000_height60",metric]
            axes[j].scatter(i+np.linspace(-.18,-.04,3),seeds,c=BLUE,s=30,label="30 m: three seeds" if i==0 else None)
            axes[j].scatter(i+.16,height,c=ORANGE,marker="D",s=32,label="60 m scenario" if i==0 else None)
        axes[j].set_xticks([0,1],["GDAS 1°","GFS 0.25°"])
        axes[j].set_ylim(0,1.12*summary[metric].max())
        axes[j].grid(axis="y",alpha=.2)
    axes[0].set_ylabel("Integrated sensitivity\n[ppm / (µmol m⁻² s⁻¹)]")
    axes[1].set_ylabel("Southeast beyond 25 km\n(% of total sensitivity)")
    axes[1].legend(frameon=False,fontsize=8)
    heading(fig,"Seed spread and release height test different uncertainties",
            "Seed points describe finite-particle variability; the 60 m release is a sensitivity scenario.\n"
            "Neither is an atmospheric confidence interval or a second measured inlet.")
    export(fig,"figure_06_robustness")


def meteorology_chart():
    table=pd.read_csv(TABLES/"meteorological_context.csv",parse_dates=["time_utc"])
    fig,axes=plt.subplots(3,1,figsize=(8,6.4),sharex=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.12,top=.79,hspace=.30)
    for driver,color,style in (("GFS",BLUE,"-"),("GDAS",ORANGE,"--")):
        sub=table[table.driver.eq(driver)]
        for ax,var,label in zip(axes,("PBLH","U10M","V10M"),("Native PBL height\n(m)","Eastward wind\n(m s⁻¹)","Northward wind\n(m s⁻¹)")):
            ax.plot(sub.time_utc,sub[var],color=color,ls=style,label=driver)
            ax.set_ylabel(label);ax.grid(axis="y",alpha=.2)
    axes[0].set_ylim(bottom=0);axes[0].legend(frameon=False,ncol=2)
    for ax in axes[1:]:ax.axhline(0,color=".6",lw=.7)
    axes[-1].set_xlabel("UTC date, September 2019")
    heading(fig,"Meteorological inputs differ in mixing and near-surface wind",
            "Nearest native grid point to BKT · three-hourly meteorological output.\n"
            "Native PBL height is context; STILT diagnoses its own mixing depth.")
    export(fig,"figure_01_meteorology")


def fire_charts():
    with xr.open_dataset(OUT/"GFED_convolution.nc") as source:data=source.load()
    provinces,_=indonesia_boundaries()
    fig=plt.figure(figsize=(10,6.8))
    for i,gas in enumerate(("CO2","CH4")):
        f=data.enhancement.sel(gas=gas)*(1 if gas=="CO2" else 1000)
        y,x,d=display_surface(f.values,f.lat.values,f.lon.values,0)
        vmax=10**np.ceil(np.log10(d.max()));vmin=vmax/1e6
        ax=map_axis(fig,[.065+i*.49,.29,.43,.48],provinces)
        mesh=ax.contourf(x,y,np.ma.masked_less_equal(d,0),levels=np.geomspace(vmin,vmax,80),norm=LogNorm(vmin,vmax),cmap="YlOrRd",transform=ccrs.PlateCarree(),zorder=2)
        ax.set_title(f"({'ab'[i]}) "+("CO₂" if gas=="CO2" else "CH₄"),fontsize=10)
        cb=fig.colorbar(mesh,cax=fig.add_axes([.11+i*.49,.20,.33,.02]),orientation="horizontal",ticks=np.geomspace(vmin,vmax,4))
        cb.set_label(("ppm CO₂" if gas=="CO2" else "ppb CH₄")+" km⁻² · log scale",fontsize=9)
    heading(fig,"Daily fire emissions intersect the modeled BKT footprint",
            "GFED5.1 daily emissions × GFS transport, 23–26 September 2019.\n"
            "Surface-release scenario with uniform emissions within each day; gas-specific color scales.",left=.065)
    map_note(fig);export(fig,"figure_11_fire_map")
    lag=pd.read_csv(TABLES/"fire_lags.csv",parse_dates=["source_time_utc"])
    lag["day"]=lag.source_time_utc.dt.strftime("%d Sep")
    daily=lag.groupby(["gas","day"]).enhancement.sum().reset_index()
    daily.to_csv(TABLES/"fire_daily_contribution.csv",index=False)
    fig,axes=plt.subplots(1,3,figsize=(9,4.6));fig.subplots_adjust(left=.085,right=.98,bottom=.18,top=.77,wspace=.55)
    for ax,gas in zip(axes,("CO2","CH4","CO")):
        sub=daily[daily.gas.eq(gas)]
        ax.bar(sub.day,sub.enhancement,color=ORANGE,width=.68)
        ax.set_ylabel("Fire contribution ("+("ppm" if gas=="CO2" else "ppb")+")")
        ax.set_title({"CO2":"CO₂","CH4":"CH₄","CO":"CO"}[gas],fontsize=10)
        ax.tick_params(axis="x",rotation=35);ax.grid(axis="y",alpha=.2)
    heading(fig,"Fire influence reflects both daily emissions and transport age",
            "Contributions are grouped by source date, not arrival date.\n"
            "Only one hour on 26 September lies in the 72-hour source window.",left=.085)
    export(fig,"figure_12_fire_timing")


def source_charts():
    table=pd.read_csv(TABLES/"source_contributions.csv")
    selected=table[table.run.str.startswith("GFS_")&~table.run.str.contains("height")]
    summary=selected.groupby(["gas","sector"]).enhancement.agg(["mean","min","max"]).reset_index()
    summary.to_csv(TABLES/"source_seed_summary.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(9,5.0));fig.subplots_adjust(left=.24,right=.97,bottom=.16,top=.75,wspace=.74)
    for ax,gas in zip(axes,("CO2","CH4")):
        sub=summary[summary.gas.eq(gas)].sort_values("mean")
        y=np.arange(len(sub))
        ax.barh(y,sub["mean"],color=BLUE,height=.65)
        ax.errorbar(sub["mean"],y,xerr=np.vstack((sub["mean"]-sub["min"],sub["max"]-sub["mean"])),fmt="none",color="black",capsize=2,lw=.8)
        ax.set_yticks(y,[SECTOR_LABELS[s] for s in sub.sector],fontsize=8.5)
        ax.set_xlabel("Modeled enhancement\n("+("ppm CO₂" if gas=="CO2" else "ppb CH₄")+")")
        ax.set_xlim(left=0);ax.grid(axis="x",alpha=.2)
    heading(fig,"Sector contributions follow both emissions and transport",
            "EDGAR v8.0 September 2019 mean fluxes × GFS footprints, assuming surface release.\n"
            "Whiskers show the three-seed range only; inventory and structural errors are not included.",left=.08)
    export(fig,"figure_07_sectors")
    with xr.open_dataset(OUT/"EDGAR_convolution.nc") as ds: data=ds.load()
    source_maps(data)
    province_chart()


def source_maps(data, variables=("surface_flux","enhancement")):
    provinces,_=indonesia_boundaries()
    for variable,stem,title in (("surface_flux","figure_08_inventory","Anthropogenic surface-flux inventories around Sumatra"),
                                ("enhancement","figure_09_source_influence","Inventory-weighted source influence on BKT")):
        if variable not in variables:continue
        fig=plt.figure(figsize=(10,6.4))
        for i,gas in enumerate(("CO2","CH4")):
            field=data[variable].sel(source=[s for s in data.source.values if s.startswith(gas+"_")]).sum("source")
            if variable=="enhancement":
                field=field*(1 if gas=="CO2" else 1000)
                y,x,z=display_surface(field.values,field.lat.values,field.lon.values,0)
                unit=("ppm CO₂" if gas=="CO2" else "ppb CH₄")+" km⁻²"
            else:
                y,x,z=field.lat.values,field.lon.values,field.values
                unit="µmol "+("CO₂" if gas=="CO2" else "CH₄")+" m⁻² s⁻¹"
            positive=z[z>0]
            vmax=10**np.ceil(np.log10(positive.max()));vmin=vmax/1e6
            ax=map_axis(fig,[.065+i*.49,.29,.43,.48],provinces)
            mesh=ax.contourf(x,y,np.ma.masked_less_equal(z,0),levels=np.geomspace(vmin,vmax,80),norm=LogNorm(vmin,vmax),cmap="YlOrRd",transform=ccrs.PlateCarree(),zorder=2)
            ax.set_title(f"({'ab'[i]}) "+("CO₂" if gas=="CO2" else "CH₄"),fontsize=10)
            cb=fig.colorbar(mesh,cax=fig.add_axes([.11+i*.49,.20,.33,.02]),orientation="horizontal",ticks=np.geomspace(vmin,vmax,4))
            cb.set_label(unit+" · log scale",fontsize=9)
        heading(fig,title,"EDGAR v8.0 · September 2019 monthly mean · all eight reported sectors\n"
                "Surface-release approximation; gas-specific color scales.",left=.065)
        map_note(fig);export(fig,stem)


def province_chart():
    p=pd.read_csv(TABLES/"province_contributions.csv")
    fig,axes=plt.subplots(1,2,figsize=(9,5.8));fig.subplots_adjust(left=.23,right=.97,bottom=.14,top=.77,wspace=.68)
    for ax,gas in zip(axes,("CO2","CH4")):
        sub=p[p.gas.eq(gas)].nlargest(8,"enhancement").sort_values("enhancement")
        names=[str(p).title().replace("Kepulauan Bangka Belitung","Kepulauan Bangka\nBelitung") for p in sub.province]
        ax.barh(names,sub.enhancement,color=BLUE)
        from matplotlib.ticker import MaxNLocator
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.set_xlabel("Modeled enhancement\n("+("ppm CO₂" if gas=="CO2" else "ppb CH₄")+")")
        ax.set_xlim(left=0);ax.tick_params(axis="y",labelsize=8.5);ax.grid(axis="x",alpha=.2)
    heading(fig,"Provincial summaries locate modeled anthropogenic influence",
            "Top eight Indonesian provinces by EDGAR-weighted GFS sensitivity.\n"
            "Fractional cell–boundary overlap in equal-area coordinates; no facility-level attribution.",left=.08)
    export(fig,"figure_10_provinces")


if __name__=="__main__":
    apply_chart_style()
    footprint_maps();transport_charts();meteorology_chart();source_charts();fire_charts()
