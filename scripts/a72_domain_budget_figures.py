#!/usr/bin/env python3
"""Reproducible figures for the BKT domain and prior-budget extension."""
from __future__ import annotations
import json
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import i18n
from a71_domain_budget_extension import OUT, TABLES

BLUE="#0072B2"; ORANGE="#D55E00"; GREEN="#009E73"; INK="#333333"; GRAY="#777777"
FIGURES=OUT/"figures"


def theme() -> None:
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9.2,"axes.labelsize":9.2,
        "axes.titlesize":10,"xtick.labelsize":8.5,"ytick.labelsize":8.5,
        "text.color":INK,"axes.labelcolor":INK,"xtick.color":INK,"ytick.color":INK,
        "axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#AAAAAA",
        "axes.linewidth":.7,"pdf.fonttype":42,"savefig.facecolor":"white"})


def header(fig, title: str, highlight: str, left: float=.08, *, wrap_title: bool=False) -> None:
    title_text=i18n.t(title)
    if wrap_title:
        title_text=textwrap.fill(title_text,width=58,break_long_words=False)
    highlight_text=textwrap.fill(i18n.t(highlight).replace("\n"," "),width=92,break_long_words=False)
    fig.text(left,.975,title_text,ha="left",va="top",fontsize=11.5,fontweight="bold",linespacing=1.15)
    fig.text(left,.855 if wrap_title else .91,highlight_text,ha="left",va="top",fontsize=9,
        color="#555555",linespacing=1.35)


def source(fig, text: str, left: float=.08) -> None:
    fig.text(left,.012,i18n.t(text),ha="left",va="bottom",fontsize=7.2,color="#666666")


def save(fig, name: str) -> None:
    FIGURES.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIGURES/f"{name}{i18n.suffix()}.pdf")
    fig.savefig(FIGURES/f"{name}.png",dpi=300)
    plt.close(fig)


def domain_ensemble() -> None:
    data=pd.read_csv(TABLES/"full_receptor_budget.csv",parse_dates=["time_utc"])
    if len(data)!=52 or data.time_utc.duplicated().any(): raise ValueError("Incomplete ensemble figure input")
    retained=data.original_retained.astype(bool); wide_pass=data.wide_retention_fraction.ge(.95)
    fig,axes=plt.subplots(1,2,figsize=(7.4,5.0))
    fig.subplots_adjust(left=.10,right=.98,bottom=.17,top=.70,wspace=.38)
    header(fig,"Domain expansion changes completeness and sensitivity across the full ensemble",
        f"BKT, 9 September–6 October 2019; original screen retained {retained.sum()} of 52 hours.\n"
        f"wide runs retain at least 95% in {wide_pass.sum()} of 52.",wrap_title=True)
    x=np.arange(len(data))
    axes[0].plot(x,100*data.narrow_retention_fraction,color=GRAY,lw=1,label="Original")
    axes[0].plot(x,100*data.wide_retention_fraction,color=ORANGE,lw=1.3,label="Widened")
    axes[0].axhline(95,color="#999999",lw=.8,ls="--")
    axes[0].set(xlabel="Receptor hour (chronological order)",ylabel="Active particles (%)",ylim=(0,103),title="(a) Particle retention")
    axes[0].legend(frameon=False,loc="lower left")
    for keep,color,label in [(True,BLUE,"Originally retained"),(False,ORANGE,"Recovered")]:
        g=data[retained.eq(keep)]
        axes[1].scatter(g.narrow_sensitivity,g.wide_sensitivity,s=23,color=color,alpha=.8,label=label,edgecolors="white",linewidths=.35)
    limit=max(data.narrow_sensitivity.max(),data.wide_sensitivity.max())*1.04
    axes[1].plot([0,limit],[0,limit],color="#999999",lw=.8,ls="--")
    axes[1].set(xlabel="Original-domain sensitivity",ylabel="Widened-domain sensitivity",xlim=(0,limit),ylim=(0,limit),title="(b) Matched surface sensitivity")
    axes[1].legend(frameon=False,loc="upper left")
    for ax in axes: ax.grid(axis="y",color="#E7E7E7",lw=.6);ax.set_axisbelow(True)
    source(fig,"Data: NOAA GFS-driven HYSPLIT-STILT forward simulations; actual-emitted-particle normalization.")
    save(fig,"domain_ensemble")


def selection_concentrations() -> None:
    data=pd.read_csv(TABLES/"full_receptor_budget.csv")
    retained=data.original_retained.astype(bool)
    fig,axes=plt.subplots(1,3,figsize=(7.4,4.65))
    fig.subplots_adjust(left=.08,right=.98,bottom=.18,top=.68,wspace=.43)
    header(fig,"The original transport screen selected a different concentration sample",
        f"At BKT, 52 fixed observation hours include {retained.sum()} originally retained and {(~retained).sum()} recovered.\n"
        "Grouping uses modeled particle retention; it does not alter the observations.")
    rng=np.random.default_rng(20260909)
    for ax,(gas,label,unit,color) in zip(axes,[('co2','CO₂','ppm',BLUE),('ch4','CH₄','ppb',ORANGE),('co','CO','ppb',GREEN)]):
        groups=[data.loc[retained,gas].to_numpy(),data.loc[~retained,gas].to_numpy()]
        ax.boxplot(groups,positions=[0,1],widths=.5,patch_artist=True,showfliers=False,
            boxprops={"facecolor":"#EEEEEE","edgecolor":"#777777"},medianprops={"color":INK,"linewidth":1.4},
            whiskerprops={"color":"#777777"},capprops={"color":"#777777"})
        for j,values in enumerate(groups):
            ax.scatter(j+rng.uniform(-.12,.12,len(values)),values,s=13,color=color,alpha=.68,edgecolors="none")
        ax.set(xticks=[0,1],xticklabels=["Retained","Recovered"],ylabel=f"{label} ({unit})")
        ax.grid(axis="y",color="#E7E7E7",lw=.6);ax.set_axisbelow(True)
    axes[0].set_title("(a) CO₂");axes[1].set_title("(b) CH₄");axes[2].set_title("(c) CO")
    source(fig,"Data: quality-controlled hourly BKT observations. Grouping uses modeled particle retention, not gas concentration.")
    save(fig,"selection_concentrations")


def budget_convergence() -> None:
    data=pd.read_csv(TABLES/"convergence_matrix.csv",parse_dates=["time_utc"])
    if len(data)!=30: raise ValueError("Incomplete convergence figure input")
    fig,axes=plt.subplots(1,3,figsize=(7.4,4.9))
    fig.subplots_adjust(left=.09,right=.98,bottom=.17,top=.68,wspace=.43)
    header(fig,"Surface and endpoint-background terms must converge together",
        "Five pre-declared BKT receptors; 72, 120 and 168 hours backward. Thin lines are cases; thick lines are medians.")
    panels=[("net_surface_ppb","Surface contribution","ppb"),("background_ppb","Endpoint background","ppb"),("total_prior_ppb","Combined prior budget","ppb")]
    handles=[]
    for ax,(metric,title,unit) in zip(axes,panels):
        for domain,color,label,offset in [("original",BLUE,"Original",-1.1),("wide",ORANGE,"Widened",1.1)]:
            sub=data[data.domain.eq(domain)]
            for _,group in sub.groupby("time_utc"):
                ax.plot(group.hours_back+offset,group[metric],color=color,alpha=.28,lw=.8)
            med=sub.groupby("hours_back")[metric].median()
            handle,=ax.plot(med.index+offset,med.values,color=color,lw=2.3,marker="o",ms=4,label=label)
            if metric=="net_surface_ppb": handles.append(handle)
        ax.set(xlabel="Backward duration (hours)",ylabel=f"{title} ({unit})",xticks=[72,120,168],title=title)
        ax.grid(axis="y",color="#E7E7E7",lw=.6);ax.set_axisbelow(True)
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.54,.77),ncol=2,frameon=False)
    source(fig,"Data: HYSPLIT-STILT, EDGAR v8.0, GFED5.1 and CarbonTracker-CH4 2025; prior-budget sensitivity only.")
    save(fig,"budget_convergence")


def main() -> None:
    theme();domain_ensemble();selection_concentrations();budget_convergence()
    (FIGURES/"chart_specification.json").write_text(json.dumps({"renderer":"Matplotlib",
        "matplotlib_version":matplotlib.__version__,"width_inches":7.4,"dpi":300,
        "font":"DejaVu Sans","palette":[BLUE,ORANGE,GREEN,INK,GRAY],
        "uncertainty":"Intervals are in CSV/table output; figures show all cases and medians without inferential whiskers.",
        "captions":"docs/BKT_Domain_Budget_appendix.md"},indent=2)+"\n")


if __name__=="__main__":
    i18n.install(i18n.from_argv())
    main()
