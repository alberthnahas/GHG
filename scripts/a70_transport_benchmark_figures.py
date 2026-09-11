"""Reproducible static figures for the general transport benchmark."""
from __future__ import annotations
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from a64_transport_benchmark import OUT
from a69_transport_benchmark_report import LABELS

BLUE='#006A8E';ORANGE='#D55E00';INK='#333333';GRAY='#777777'
FIGURES=OUT/'figures';TABLES=OUT/'tables'


def theme():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.labelsize':9.5,
        'axes.titlesize':10,'xtick.labelsize':9,'ytick.labelsize':9,
        'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
        'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#AAAAAA',
        'axes.linewidth':.7,'pdf.fonttype':42,'savefig.facecolor':'white'})


def header(fig,title,highlight,left=.1):
    fig.text(left,.97,title,ha='left',va='top',fontsize=11.5,fontweight='bold')
    fig.text(left,.90,highlight,ha='left',va='top',fontsize=9.2,color='#555555',linespacing=1.4)


def save(fig,name):
    FIGURES.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIGURES/(name+'.pdf'))
    fig.savefig(FIGURES/(name+'.png'),dpi=300)
    plt.close(fig)


def receptor_label(value):
    stamp=pd.Timestamp(value)
    if stamp.tzinfo is None:stamp=stamp.tz_localize('UTC')
    local=stamp.tz_convert('Asia/Jakarta')
    return f'{local.day} {local:%b}, {local:%H:%M} WIB'


def domain():
    summary=pd.read_csv(TABLES/'domain_comparison.csv').set_index('scenario')
    curve=pd.read_csv(TABLES/'domain_sensitivity_by_lag.csv')
    if summary.loc['loss_wide_output','retained_percent']<95:raise ValueError('Domain figure claim fails')
    fig,axes=plt.subplots(1,2,figsize=(7.4,4.8))
    fig.subplots_adjust(left=.10,right=.98,bottom=.15,top=.69,wspace=.43)
    header(fig,'Expanded meteorology prevents boundary loss in the five-day test',
        f'BKT, 6 October 2019 at 06:00 UTC; {int(summary.iloc[0].emitted)} emitted particles.\n'
        'Particle survival and surface sensitivity test different forms of truncation.')
    cases=[('loss_control','Original domains',GRAY,'--'),('loss_wide','Wider meteorology',BLUE,'-'),
           ('loss_wide_output','Both domains wider',ORANGE,'-.')]
    handles=[]
    for case,label,color,style in cases:
        retention=pd.read_csv(TABLES/f'{case}_retention.csv')
        if case!='loss_wide_output':
            axes[0].plot(retention.lag_hours,retention.retained_percent,color=color,ls=style,lw=1.7)
        sub=curve[curve.scenario==case]
        handle,=axes[1].plot(sub.lag_hours,sub.cumulative_sensitivity,label=label,color=color,ls=style,lw=1.7)
        handles.append(handle)
    axes[0].axhline(95,color='#BBBBBB',lw=.8,zorder=0)
    axes[0].text(4,91,'95% screen',fontsize=8,color='#666666')
    axes[0].set(ylim=(0,105),ylabel='Active particles (%)',title='(a) Meteorological-domain retention')
    axes[1].set(ylim=(0,None),ylabel='Accumulated sensitivity\n[ppm / (µmol m⁻² s⁻¹)]',title='(b) Surface-flux sensitivity')
    for ax in axes:
        ax.set(xlim=(0,120),xlabel='Backward age (hours)',xticks=[0,24,48,72,96,120])
        ax.grid(axis='y',color='#E5E5E5',lw=.6);ax.set_axisbelow(True)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.79),ncol=3,frameon=False,fontsize=8.5)
    save(fig,'domain_completeness')


def physics():
    data=pd.read_csv(TABLES/'physics_contrasts.csv')
    required=set(LABELS)|{'control_seedm10','control_seedm20'}
    if set(data.scenario)!=required or len(data)!=32:raise ValueError('Incomplete physics figure evidence')
    fig,ax=plt.subplots(figsize=(7.4,5.3))
    fig.subplots_adjust(left=.30,right=.98,bottom=.14,top=.72)
    header(fig,'Transport responses vary by mixing assumption and receptor time',
        'BKT; receptor dates 9 and 23 September 2019 (UTC); 72 hours backward.\n'
        'Ratios are sensitivities, not skill scores; control repeats show sampling variation.',left=.06)
    names=list(LABELS);labels=[LABELS[k].replace('CAPE threshold: 500 J kg⁻¹','CAPE: 500 J kg⁻¹') for k in names]+['Control seed repeats']
    ax.axvline(1,color='#999999',lw=1,zorder=0)
    anchors=sorted(data.time_utc.unique())
    handles=[]
    for j,stamp in enumerate(anchors):
        when=pd.Timestamp(stamp);color=BLUE if when.hour==6 else ORANGE
        marker='o' if when.day==9 else '^';offset=(-.21,-.07,.07,.21)[j]
        for i,name in enumerate(names):
            value=data[(data.scenario==name)&(data.time_utc==stamp)].sensitivity_ratio.item()
            ax.plot(value,i+offset,marker=marker,color=color,ms=5,ls='none',mec=color,mew=.8)
        for k,seed in enumerate(('control_seedm10','control_seedm20')):
            value=data[(data.scenario==seed)&(data.time_utc==stamp)].sensitivity_ratio.item()
            ax.plot(value,len(names)+offset,marker=marker,color=color,ms=5,ls='none',
                    mfc=color if k==0 else 'white',mec=color,mew=.8)
        handle,=ax.plot([],[],marker=marker,color=color,ls='none',ms=5,
            label=receptor_label(stamp))
        handles.append(handle)
    ax.set(yticks=range(len(labels)),yticklabels=labels,ylim=(len(labels)-.5,-.5),
        xlabel='Integrated sensitivity / same-time control')
    ax.grid(axis='x',color='#E5E5E5',lw=.6);ax.set_axisbelow(True)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.58,.81),ncol=2,frameon=False,fontsize=8.5)
    save(fig,'physics_sensitivity')


def profiles():
    data=pd.read_csv(TABLES/'profile_by_pressure.csv')
    data=data[data.station=='IDM00096163']
    fig,axes=plt.subplots(1,2,figsize=(7.4,4.9),sharey=True)
    fig.subplots_adjust(left=.10,right=.98,bottom=.15,top=.70,wspace=.37)
    header(fig,'Profile agreement depends on pressure and sampling support',
        'Padang, 9 September–6 October 2019; GFS versus balloon profiles.\n'
        'Whiskers: pointwise 95% intervals from three-day block resampling.')
    handles=[]
    for case,label,color,marker in [('primary','Available levels',BLUE,'o'),
                                   ('complete_profiles','Complete five-level profiles',ORANGE,'s')]:
        group=data[data.scenario==case].sort_values('pressure_hpa')
        for ax,metric,estimate in [(axes[0],'vector_rmse','vector_rmse_ms'),
                                   (axes[1],'temperature_bias','temperature_bias_k')]:
            value=group[estimate].to_numpy();lo=group[metric+'_ci95_low'].to_numpy();hi=group[metric+'_ci95_high'].to_numpy()
            if not np.isfinite(np.r_[value,lo,hi]).all():raise ValueError('Profile figure lacks intervals')
            h=ax.errorbar(value,group.pressure_hpa,xerr=np.vstack([value-lo,hi-value]),
                color=color,marker=marker,ms=4,lw=1,elinewidth=.8,capsize=2,
                markerfacecolor='white' if case=='complete_profiles' else color,label=label)
        handles.append(h)
    axes[0].set(xlabel='Wind-vector RMSE (m s⁻¹)',ylabel='Pressure (hPa)',title='(a) Wind-vector agreement',xlim=(0,None))
    axes[1].set(xlabel='Temperature bias (K)',title='(b) Model minus observation')
    axes[1].axvline(0,color='#999999',lw=.8,zorder=0)
    for ax in axes:
        ax.set(ylim=(970,260),yticks=[925,850,700,500,300])
        ax.grid(axis='y',color='#E5E5E5',lw=.6);ax.set_axisbelow(True)
    fig.legend(handles=handles,labels=['Available levels','Complete five-level profiles'],loc='upper center',
        bbox_to_anchor=(.54,.79),ncol=2,frameon=False,fontsize=8.5)
    save(fig,'profile_evaluation')


if __name__=='__main__':
    theme();domain();physics();profiles()
    (FIGURES/'chart_specification.json').write_text(json.dumps(dict(
        renderer='Matplotlib',matplotlib_version=matplotlib.__version__,width_inches=7.4,dpi=300,
        font='DejaVu Sans',palette=[BLUE,ORANGE,INK,GRAY],
        uncertainty='Profile intervals: 3000 circular 3-day blocks; physics markers are cases, not confidence intervals',
        captions='docs/BKT_Transport_Benchmark_appendix.md',source_tables=str(TABLES)),indent=2)+'\n')
