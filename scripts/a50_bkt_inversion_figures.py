"""Scientific charts and maps from verified methane inversion evidence tables."""
from __future__ import annotations
import argparse
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
from matplotlib.colors import LogNorm,TwoSlopeNorm
from matplotlib.ticker import LogFormatterMathtext,NullFormatter
import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
from pyproj import Geod
from functools import lru_cache
from shapely.geometry import box
from a46_bkt_inversion_transport import OUT
from a38_bkt_footprint_report import apply_chart_style,BLUE,ORANGE
from bkt_footprint_spatial import indonesia_boundaries,detailed_neighbors,display_surface,cell_area_km2,sensitivity_support_mask
import ghg_common as G

TABLES=OUT/"tables";FIG=OUT/"figures"
NAMES=["Anthropogenic ≤500 km","Anthropogenic >500 km","Wetlands","Non-crop fires"]
COLORS=[BLUE,"#56B4E9","#009E73",ORANGE]
COUNTRIES=("MYS","SGP","THA","BRN","VNM","KHM","MMR","PHL","IND","BGD","LKA","TLS","AUS")


def head(fig,title,highlight):
    fig.text(.105,.97,title,fontsize=12,weight="bold",va="top")
    fig.text(.105,.915,highlight,fontsize=9,color="#52616A",va="top")


def export(fig,number,stem):
    FIG.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIG/f"figure_{number:02d}_{stem}.png",dpi=300,facecolor="white")
    fig.savefig(FIG/f"figure_{number:02d}_{stem}.pdf",dpi=300,facecolor="white")
    plt.close(fig)


def footer(fig,text):fig.text(.105,.025,text,fontsize=8,color="#52616A")
def time_axis(ax):
    ax.set_xlim(pd.Timestamp("2019-09-09"),pd.Timestamp("2019-10-06T23:00"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))


def scheduled_series(frame):
    """Insert unavailable receptor slots so lines and envelopes cannot bridge gaps."""
    grid=pd.date_range("2019-09-09T06:00","2019-10-06T18:00",freq="12h",name="time_utc")
    return frame.set_index("time_utc").reindex(grid).reset_index()


def coverage():
    selected=pd.read_csv(OUT/"receptor_selection.csv",parse_dates=["time_utc"])
    obs=G.apply_flags(G.load_station("BKT")).set_index("time_utc").reindex(pd.date_range("2019-09-09","2019-10-06T23:00",freq="h"))
    pairs=pd.read_csv(TABLES/"inversion_flask_pairs.csv",parse_dates=["time_utc"])
    selected["transport_usable"]=True
    operator_path=TABLES/"operator_base.csv"
    if operator_path.exists():
        operator=pd.read_csv(operator_path,parse_dates=["time_utc"])
        if len(operator)==int(selected.retained.sum()):
            selected["transport_usable"]=selected.time_utc.map(operator.set_index("time_utc").transport_usable).eq(True)
    fig=plt.figure(figsize=(7.2,5.8));ax=fig.add_axes([.105,.44,.85,.33]);bottom=fig.add_axes([.105,.14,.85,.21])
    ax.plot(obs.index,obs.ch4,color="#89969C",lw=.8,label="Available hourly record")
    for held,label,color,marker in ((False,"Fit",BLUE,"o"),(True,"Withheld",ORANGE,"s")):
        d=selected[selected.retained&selected.transport_usable&selected.holdout.eq(held)]
        ax.scatter(d.time_utc,d.ch4,s=22,facecolors="none" if held else color,edgecolors=color,marker=marker,label=f"{label}: {len(d)} h",zorder=4)
    excluded=selected[selected.retained&~selected.transport_usable]
    if len(excluded):ax.scatter(excluded.time_utc,excluded.ch4,marker="x",s=25,color="#A44D5E",label=f"Transport excluded: {len(excluded)} h")
    ax.set_ylabel("CH₄ (ppb)");ax.legend(ncol=2 if len(excluded) else 3,fontsize=8,loc="lower left",bbox_to_anchor=(0,1.01),borderaxespad=0);time_axis(ax)
    bottom.axhline(0,color="#555",lw=.8)
    bottom.scatter(pairs.time_utc,pairs["diff"],s=35,color=BLUE)
    bottom.set_ylabel("Flask − in situ\nCH₄ (ppb)");bottom.set_ylim(-4,4);bottom.set_yticks([-4,-2,0,2,4]);time_axis(bottom)
    bottom.set_xlabel("2019 · UTC");bottom.set_xlim(ax.get_xlim())
    head(fig,"BKT observations support a multi-week methane experiment",
        "Fixed twice-daily receptor schedule; missing hours are retained as gaps.\nFour co-located NOAA flask comparisons check consistency at sampled hours.")
    footer(fig,"Sources: BMKG hourly dry-air mole fractions; NOAA GML flask CH₄ on X2004A.")
    export(fig,13,"inversion_observations")


@lru_cache(maxsize=1)
def map_geometry():
    provinces,imeta=indonesia_boundaries();neighbors,nmeta=detailed_neighbors(COUNTRIES)
    return provinces,imeta,neighbors,nmeta


def map_axis(fig,rect,extent=(94,115,-9,9)):
    provinces,imeta,neighbors,nmeta=map_geometry()
    ax=fig.add_axes(rect,projection=ccrs.PlateCarree());ax.set_extent(extent)
    ax.set_facecolor("#EAF3F7");ax.set_rasterization_zorder(3)
    clip=box(extent[0]-.5,extent[2]-.5,extent[1]+.5,extent[3]+.5)
    for geometries,face in ((neighbors,"#E5E5E1"),(provinces.geometry,"#F8F7F2")):
        visible=[g.intersection(clip) for g in geometries if g.intersects(clip)]
        ax.add_geometries(visible,ccrs.PlateCarree(),facecolor=face,edgecolor="none",zorder=0)
        ax.add_geometries(visible,ccrs.PlateCarree(),facecolor="none",edgecolor="#697276",lw=.35,zorder=4)
    ax.plot(100.318,-.202,"*",ms=9,color="#005D7B",markeredgecolor="white",zorder=8)
    g=ax.gridlines(draw_labels=True,linewidth=.3,linestyle="--",alpha=.35)
    g.top_labels=g.right_labels=False;g.xlabel_style=g.ylabel_style={"size":8}
    az=np.linspace(0,360,361);lon,lat,_=Geod(ellps="WGS84").fwd(np.full(361,100.318),np.full(361,-.202),az,np.full(361,500000))
    circle=ax.plot(lon,lat,ls="--",color="#333",lw=.7,zorder=5)[0]
    circle.set_path_effects([path_effects.withStroke(linewidth=1.6,foreground="white")])
    if not (OUT/"inversion_cartographic_provenance.json").exists():
        (OUT/"inversion_cartographic_provenance.json").write_text(json.dumps(dict(indonesia=imeta,neighbors=nmeta),indent=2)+"\n")
    return ax


def support_maps():
    with xr.open_dataset(OUT/"spatial_operator_base.nc") as d:spatial=d.load()
    operator=pd.read_csv(TABLES/"operator_base.csv",parse_dates=["time_utc"])
    spatial=spatial.sel(receptor=operator.loc[operator.transport_usable,"time_utc"].values)
    with xr.open_dataset(OUT/"monthly_prior_fluxes.nc") as d:monthly=d.load()
    fig=plt.figure(figsize=(7.2,5.6))
    ax1=map_axis(fig,[.09,.28,.39,.5]);ax2=map_axis(fig,[.59,.28,.39,.5])
    anth=(monthly.flux.sel(source=[s for s in monthly.source.values if s.startswith("CH4_")]).sum("source")*xr.DataArray([22/28,6/28],dims="month")).sum("month")
    flux_cmap=plt.get_cmap("magma").copy();flux_cmap.set_under("#F1EFEA")
    mesh=ax1.pcolormesh(anth.lon,anth.lat,np.ma.masked_less_equal(anth,0),cmap=flux_cmap,norm=LogNorm(1e-5,.1),shading="auto",zorder=2)
    f=spatial.footprint.mean("receptor")
    y,x,den=display_surface(f.values,f.lat.values,f.lon.values,1,4)
    display_mass=den*cell_area_km2(y,x)
    inside=(y[:,None]>=-9)&(y[:,None]<=9)&(x[None,:]>=94)&(x[None,:]<=115)
    pd.DataFrame([dict(raw_integral=float(f.sum()),display_integral=display_mass.sum(),
        below_scale_percent=100*display_mass[den<1e-7].sum()/display_mass.sum(),
        outside_frame_percent=100*display_mass[~inside].sum()/display_mass.sum(),
        emission_flux_maximum=float(anth.max()),receptors=spatial.sizes["receptor"])]).to_csv(TABLES/"inversion_display_integrity.csv",index=False)
    mesh2=ax2.contourf(x,y,np.ma.masked_less_equal(den,0),levels=np.geomspace(1e-7,.01,80),norm=LogNorm(1e-7,.01),cmap="YlOrRd",extend="max" if den.max()>.01 else "neither",zorder=2)
    ax1.set_title("(a) Anthropogenic prior",fontsize=10);ax2.set_title("(b) Mean receptor sensitivity",fontsize=10)
    for artist,left,label in ((mesh,.12,"CH₄ flux (µmol m⁻² s⁻¹)"),(mesh2,.62,"Sensitivity density¹")):
        options={"extend":"both"} if artist is mesh else {}
        cb=fig.colorbar(artist,cax=fig.add_axes([left,.19,.31,.02]),orientation="horizontal",**options)
        cb.set_ticks(np.logspace(-5,-1,5) if artist is mesh else np.logspace(-7,-2,6))
        cb.formatter=LogFormatterMathtext();cb.update_ticks();cb.set_label(label,fontsize=8);cb.ax.tick_params(labelsize=8)
    head(fig,"Emission intensity and receptor sensitivity are distinct fields",
        "Dashed circle: 500 km regional partition; star: BKT.\nThe inversion uses unsmoothed coefficients, not the displayed sensitivity surface.")
    footer(fig,"¹ ppm / (µmol m⁻² s⁻¹) / km² · logarithmic scales\nEDGAR v8.0; GFS/HYSPLIT-STILT · Indonesia: provincial GeoJSON; neighbors: geoBoundaries.")
    export(fig,14,"inversion_support")


def components():
    d=pd.read_csv(TABLES/"inversion_predictions.csv",parse_dates=["time_utc"])
    series=scheduled_series(d)
    fig=plt.figure(figsize=(7.2,6));top=fig.add_axes([.105,.53,.85,.27]);bottom=fig.add_axes([.105,.15,.85,.23])
    top.plot(series.time_utc,series.ch4,"o-",ms=3,lw=.7,color="#222",label="Observed")
    top.plot(series.time_utc,series.background_ppb,".-",ms=3,lw=1.2,color=BLUE,label="Endpoint background")
    top.plot(series.time_utc,series.prior_inventory_ppb,".-",ms=3,lw=1,color=ORANGE,label="Background + prior exchange")
    top.set_ylabel("CH₄ (ppb)");top.legend(ncol=3,fontsize=8,loc="lower left",bbox_to_anchor=(0,1.02),borderaxespad=0);time_axis(top)
    values=d[["anthro_near_ppb","anthro_far_ppb","wetlands_ppb","fire_ppb"]].to_numpy().T
    cumulative=np.zeros(len(d))
    for value,color,name in zip(values,COLORS,NAMES):
        bottom.bar(d.time_utc,value,bottom=cumulative,width=.3,color=color,label=name,alpha=.85)
        cumulative+=value
    bottom.plot(d.time_utc,-d.soil_uptake_ppb,"_",color="#555",ms=5,label="Soil uptake")
    bottom.set_ylabel("Prior increment (ppb)");time_axis(bottom);bottom.set_xlabel("2019 · UTC")
    bottom.legend(ncol=3,fontsize=7.5,loc="lower left",bbox_to_anchor=(0,1.02),borderaxespad=0)
    head(fig,"Boundary methane and surface exchange both affect the budget",
        "Source increments use EDGAR, wetland and non-crop fire priors.\nBackground is sampled at particle endpoints; it is not a local concentration minimum.")
    footer(fig,"CT-CH₄-2025 background is conditional on assimilated observations, including BKT.")
    export(fig,15,"inversion_components")


def information():
    c=pd.read_csv(TABLES/"source_response_correlation.csv",index_col=0)
    m=pd.read_csv(TABLES/"inversion_information_modes.csv")
    fig=plt.figure(figsize=(7.2,5.4));ax=fig.add_axes([.19,.28,.39,.47]);right=fig.add_axes([.73,.28,.22,.47])
    im=ax.imshow(c.values,vmin=-1,vmax=1,cmap="RdBu_r")
    labels=["Near anthro.","Far anthro.","Wetland","Fire"]
    ax.set_xticks(range(4),labels,rotation=35,ha="right");ax.set_yticks(range(4),labels)
    for i in range(4):
        for j in range(4):ax.text(j,i,f"{c.iloc[i,j]:.2f}",ha="center",va="center",fontsize=9,color="white" if abs(c.iloc[i,j])>.65 else "#222")
    cb=fig.colorbar(im,cax=fig.add_axes([.20,.13,.36,.022]),orientation="horizontal");cb.set_label("Response correlation (r)",fontsize=9)
    right.barh(m["mode"],m.information_fraction,color=BLUE);right.set_xlim(0,1);right.invert_yaxis();right.set_yticks(m["mode"])
    right.set_xlabel("Information\nfraction");right.set_ylabel("Whitened mode")
    head(fig,"Transport-response similarity limits emission separation",
        "Correlations use fit-period source responses; no significance test is implied.\nInformation modes describe the six-parameter state, not independent map pixels.")
    footer(fig,"Source: GFS/HYSPLIT-STILT response matrix and local prior-whitened posterior curvature.")
    export(fig,16,"inversion_information")


def posterior():
    d=pd.read_csv(TABLES/"posterior_parameters.csv")
    fig=plt.figure(figsize=(7.2,5.5));ax=fig.add_axes([.34,.40,.60,.38]);lower=fig.add_axes([.34,.13,.60,.16])
    for i,row in d.iloc[:4].iterrows():
        ax.plot([row.prior_q025,row.prior_q975],[i+.10,i+.10],color="#B9C1C5",lw=5,label="Prior 95%" if i==0 else None)
        ax.plot([row.q025,row.q975],[i-.07,i-.07],color=BLUE,lw=2,label="Posterior 95%" if i==0 else None)
        ax.plot(row["median"],i-.07,"o",color=BLUE,ms=5)
    ax.axvline(1,color="#555",ls="--",lw=.8);ax.set_xscale("log");ax.set_yticks(range(4),NAMES);ax.invert_yaxis()
    ax.set_xticks([.2,.5,1,2,4],["0.2","0.5","1","2","4"]);ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Emission multiplier (dimensionless, log scale)");ax.legend(loc="upper left",fontsize=8,ncol=2,bbox_to_anchor=(-.02,1.18))
    for i,row in enumerate(d.iloc[4:].itertuples()):
        lower.plot([row.q025,row.q975],[i,i],lw=2,color=ORANGE);lower.plot(row.median,i,"o",color=ORANGE)
    lower.axvline(0,color="#777",lw=.7);lower.set_yticks([0,1],["Offset (ppb)","Trend (ppb / 28 d)"]);lower.set_ylim(1.5,-.5)
    lower.set_xlabel("Background adjustment")
    head(fig,"Methane observations update a small, positive-emission state",
        "Dots: posterior medians; intervals: 95% credible ranges from sampled chains.\nWeakly updated components remain prior-dependent rather than independently resolved.")
    footer(fig,"Conditional on GFS transport, fixed within-region source patterns and the stated error model.")
    export(fig,17,"inversion_posterior")


def predictions():
    d=pd.read_csv(TABLES/"inversion_predictions.csv",parse_dates=["time_utc"])
    series=scheduled_series(d)
    metrics=pd.read_csv(TABLES/"inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    fig=plt.figure(figsize=(7.2,6));ax=fig.add_axes([.105,.47,.85,.32]);scatter=fig.add_axes([.12,.13,.33,.23]);bar=fig.add_axes([.65,.13,.30,.23])
    ax.fill_between(series.time_utc,series.predictive_q025_ppb,series.predictive_q975_ppb,color="#DEE8ED",label="95% mismatch envelope")
    ax.fill_between(series.time_utc,series.posterior_q025_ppb,series.posterior_q975_ppb,color=BLUE,alpha=.22,label="95% model mean")
    ax.plot(series.time_utc,series.posterior_median_ppb,".-",ms=3,color=BLUE,lw=1.2)
    ax.plot(d.time_utc,d.ch4,".",color="#222",ms=4,label="Observed")
    held=d[d.holdout];ax.scatter(held.time_utc,held.ch4,facecolors="none",edgecolors=ORANGE,marker="s",s=28,label="Withheld",zorder=6)
    ax.set_ylabel("CH₄ (ppb)");ax.legend(ncol=4,fontsize=7.5,loc="upper left");time_axis(ax)
    for col,color,label in (("prior_inventory_ppb","#929A9F","Inventory"),("posterior_median_ppb",BLUE,"Posterior")):
        scatter.scatter(held.ch4,held[col],s=17,color=color,label=label)
    limits=[min(held.ch4.min(),held.posterior_median_ppb.min(),held.prior_inventory_ppb.min())-10,
            max(held.ch4.max(),held.posterior_median_ppb.max(),held.prior_inventory_ppb.max())+10]
    scatter.plot(limits,limits,ls="--",lw=.7,color="#777");scatter.set_xlim(limits);scatter.set_ylim(limits)
    scatter.set_xlabel("Observed CH₄ (ppb)");scatter.set_ylabel("Predicted CH₄ (ppb)");scatter.legend(fontsize=8)
    names=["inventory","background_only","background_adjusted_inventory","posterior"]
    bar.barh(range(4),metrics.loc[names,"rmse_ppb"],color=["#ADB6BB","#88979F","#56B4E9",BLUE])
    bar.set_yticks(range(4),["Inventory","Background only","Adjusted inventory","Posterior"],fontsize=8);bar.invert_yaxis();bar.set_xlabel("Withheld RMSE (ppb)")
    head(fig,"Background-only predictions have lower withheld error",
        f"Withheld RMSE: inversion {metrics.loc['posterior','rmse_ppb']:.1f} ppb; background only {metrics.loc['background_only','rmse_ppb']:.1f} ppb; adjusted inventory {metrics.loc['background_adjusted_inventory','rmse_ppb']:.1f} ppb.\nThis evaluates conditional concentration predictions, not independent emission truth.")
    footer(fig,"Envelope adds marginal mismatch; model-mean intervals contain parameter uncertainty only.")
    export(fig,18,"inversion_predictions")


def residuals():
    d=pd.read_csv(TABLES/"inversion_predictions.csv",parse_dates=["time_utc"])
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.8));fig.subplots_adjust(left=.12,right=.95,bottom=.15,top=.78,hspace=.5,wspace=.40)
    a,b,c,e=axes.ravel();res=d.posterior_residual_ppb
    series=scheduled_series(d)
    a.plot(series.time_utc,series.posterior_residual_ppb,"o-",color=BLUE,ms=3,lw=.7);a.axhline(0,color="#777",ls="--",lw=.8);time_axis(a);a.set_ylabel("Observed − predicted (ppb)")
    bins=np.linspace(min(res.min(),-1),max(res.max(),1),14)
    b.hist(res[~d.holdout],bins=bins,histtype="step",color=BLUE,label="Fit");b.hist(res[d.holdout],bins=bins,histtype="step",color=ORANGE,label="Withheld")
    b.set_xlabel("Residual CH₄ (ppb)");b.set_ylabel("Receptor hours");b.legend(fontsize=8)
    for hour,label,color in ((6,"13 WIB",BLUE),(18,"01 WIB",ORANGE)):
        use=d.time_utc.dt.hour.eq(hour)&d.PBLH.ge(0);c.scatter(d.PBLH[use],res[use],s=18,color=color,label=label)
    c.axhline(0,color="#777",ls="--",lw=.8);c.set_xlabel("Native GFS PBL height (m)");c.set_ylabel("Residual CH₄ (ppb)");c.legend(fontsize=8)
    for held,color,label in ((False,BLUE,"Fit"),(True,ORANGE,"Withheld")):
        use=d.holdout.eq(held);e.scatter(d.background_ppb[use],res[use],color=color,s=20,label=label)
    e.legend(fontsize=8);e.axhline(0,color="#777",ls="--",lw=.8)
    e.set_xlabel("Endpoint background (ppb)");e.set_ylabel("Residual CH₄ (ppb)")
    head(fig,"Residual structure tests the limits of the fitted explanation",
        "No observations were discarded because they disagreed with the model.\nNative GFS PBL height is context, not the STILT-computed mixing depth.")
    footer(fig,"9 September–6 October 2019 · residuals use the training-only posterior for all receptor hours.")
    export(fig,19,"inversion_residuals")


def sensitivity():
    d=pd.read_csv(TABLES/"inversion_sensitivity.csv");post=pd.read_csv(TABLES/"posterior_parameters.csv").set_index("parameter")
    cases=d.case.drop_duplicates().tolist()
    readable={"base":"Base","background_minus20":"Background −20 ppb","background_plus20":"Background +20 ppb",
        "background_prior10":"Background prior SD 10 ppb","background_prior40":"Background prior SD 40 ppb",
        "transport30percent":"Transport uncertainty 30%","transport80percent":"Transport uncertainty 80%",
        "correlation6h":"Error correlation 6 h","correlation72h":"Error correlation 72 h",
        "prior_factor1p5":"Emission prior factor 1.5","prior_factor3":"Emission prior factor 3",
        "auxiliary_half":"Auxiliary exchange ×0.5","auxiliary_double":"Auxiliary exchange ×2",
        "unscaled_geological_prior":"Unscaled geological prior","crop_overlap_retained":"Crop overlap retained",
        "representativeness_half":"Representativeness SD ×0.5","representativeness_double":"Representativeness SD ×2",
        "daytime_only":"Daytime only","shared_anthropogenic_scale":"Shared anthropogenic multiplier"}
    labels=[readable[s] for s in cases]
    fig=plt.figure(figsize=(7.2,6.5))
    for j,parameter in enumerate(["anthro_near","anthro_far"]):
        ax=fig.add_axes([.36+j*.33,.15,.27,.63]);sub=d[d.parameter.eq(parameter)].set_index("case").loc[cases]
        row=post.loc[parameter];ax.axvspan(row.q025,row.q975,color=BLUE,alpha=.12,label="Base 95% posterior")
        ax.plot(sub["map"],range(len(cases)),"o",ms=4,color=BLUE if j==0 else ORANGE)
        ax.axvline(1,ls="--",color="#777",lw=.7);ax.set_xscale("log");ax.set_ylim(len(cases)-.5,-.5)
        ax.set_xticks([.2,.5,1],["0.2","0.5","1"]);ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks(range(len(cases)),labels if j==0 else []);ax.tick_params(axis="y",labelsize=8)
        ax.set_xlabel("Emission multiplier");ax.set_title(["≤500 km",">500 km"][j],fontsize=10)
    head(fig,"Emission adjustments must be interpreted across assumptions",
        "Points: scenario posterior modes; shading: base-case 95% credible interval.\nScenario spread is structural sensitivity, not an additional probability interval.")
    footer(fig,"Cases vary background, transport error, prior width, auxiliary sources, crop overlap and sampling regime.")
    export(fig,20,"inversion_sensitivity")


def synthetic():
    d=pd.read_csv(TABLES/"synthetic_recovery_trials.csv");s=pd.read_csv(TABLES/"synthetic_recovery_summary.csv")
    fig=plt.figure(figsize=(7.2,5.6));ax=fig.add_axes([.11,.39,.85,.39]);bottom=fig.add_axes([.11,.15,.85,.14])
    components=["anthro_near","anthro_far","wetlands","fire"]
    for j,scenario in enumerate(d.scenario.unique()):
        scenario_color=[BLUE,ORANGE][j]
        positions=np.arange(4)+(j-.5)*.30
        series=[d[(d.scenario==scenario)&(d.parameter==name)].estimate for name in components]
        boxes=ax.boxplot(series,positions=positions,widths=.23,patch_artist=True,showfliers=False,
            medianprops={"color":"white"},whiskerprops={"color":scenario_color},capprops={"color":scenario_color})
        for patch in boxes["boxes"]:patch.set_facecolor(scenario_color)
        sub=s[s.scenario.eq(scenario)].set_index("parameter").loc[components]
        bottom.bar(positions,sub.local_interval_coverage_percent,width=.25,color=scenario_color,label=["Matched operator","Perturbed transport/background"][j])
    truth=d.groupby("parameter").truth.first().reindex(components)
    ax.scatter(range(4),truth,marker="D",color="#222",s=25,zorder=5,label="Synthetic truth")
    ax.set_yscale("log");ax.set_ylabel("Recovered multiplier (log scale)");ax.set_xticks(range(4),["Near anthro.","Far anthro.","Wetlands","Fires"]);ax.legend(fontsize=8)
    bottom.axhline(95,ls="--",lw=.7,color="#777");bottom.set_ylim(0,105);bottom.set_ylabel("Coverage (%)");bottom.set_xticks([]);bottom.legend(fontsize=8,ncol=2,loc="upper left",bbox_to_anchor=(0,-.20))
    head(fig,"Synthetic recovery separates numerical capability from robustness",
        "200 noise realizations per scenario; boxes show median and interquartile range.\nPerturbations add coherent source errors and an unmodeled nonlinear background signal.")
    footer(fig,"Coverage refers to local approximate 95% intervals; observed-data intervals use full posterior sampling.")
    export(fig,21,"inversion_recovery")


def geography():
    with xr.open_dataset(OUT/"spatial_operator_base.nc") as d:spatial=d.load()
    operator=pd.read_csv(TABLES/"operator_base.csv",parse_dates=["time_utc"])
    usable=operator.loc[operator.transport_usable,"time_utc"]
    spatial=spatial.sel(receptor=usable.values)
    p=pd.read_csv(TABLES/"posterior_parameters.csv").set_index("parameter")
    endpoints=pd.read_csv(OUT/"endpoints_base.csv.gz",parse_dates=["receptor_utc"])
    endpoints=endpoints[endpoints.receptor_utc.isin(usable)]
    fig=plt.figure(figsize=(7.2,6.3));ax=map_axis(fig,[.10,.29,.39,.48]);right=map_axis(fig,[.58,.29,.39,.48],extent=(76,124,-18,18))
    mult=np.where(spatial.distance_km<=500,p.loc["anthro_near","median"],p.loc["anthro_far","median"])
    support=spatial.footprint.mean("receptor").values
    masked=np.ma.masked_where(~sensitivity_support_mask(support),mult)
    limit=max(1.05,float(np.max(mult)));norm=TwoSlopeNorm(vmin=0,vcenter=1,vmax=max(2,limit))
    mesh=ax.pcolormesh(spatial.lon,spatial.lat,masked,cmap="RdBu_r",norm=norm,shading="auto",zorder=2)
    ax.set_title("(a) Two-region median adjustment",fontsize=9)
    # Deterministic thinning is display-only; all endpoints are used in background analysis.
    sample=endpoints.iloc[::max(1,len(endpoints)//4000)]
    dots=right.scatter(sample.longitude,sample.latitude,c=sample.height_m_msl/1000,s=2,cmap="viridis",vmin=0,vmax=10,alpha=.6,zorder=2)
    right.set_title("(b) Backward endpoint locations",fontsize=9)
    cb=fig.colorbar(mesh,cax=fig.add_axes([.14,.20,.31,.022]),orientation="horizontal");cb.set_label("Anthropogenic multiplier",fontsize=8)
    cb2=fig.colorbar(dots,cax=fig.add_axes([.62,.20,.31,.022]),orientation="horizontal",extend="max" if sample.height_m_msl.max()>10000 else "neither");cb2.set_label("Endpoint height (km MSL)",fontsize=8)
    head(fig,"Regional adjustment maps do not resolve individual sources",
        "Adjustment colors are shown only over cells containing 90% of aggregate sensitivity.\nUncolored areas are weakly sampled, not zero-emission regions; star: BKT.")
    footer(fig,"120-hour backward endpoints · 500 km partition · WGS 84\nIndonesia: provincial GeoJSON; neighboring boundaries: geoBoundaries, with provider-specific attribution.")
    export(fig,22,"inversion_geography")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("stage",choices=["coverage","all"])
    args=p.parse_args();apply_chart_style()
    plt.rcParams.update({"font.size":9,"axes.labelsize":9,"xtick.labelsize":8,"ytick.labelsize":8})
    if args.stage=="coverage":coverage()
    else:
        for function in (coverage,support_maps,components,information,posterior,predictions,residuals,sensitivity,synthetic,geography):function()
