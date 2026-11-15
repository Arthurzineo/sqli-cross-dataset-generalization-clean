#!/usr/bin/env python3
"""Plot-only manuscript revision. Reads saved tables; never fits or predicts."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FINAL=ROOT/'figures/manuscript_final'
AUDIT=ROOT/'figures/visual_revision_audit'
ADD=ROOT/'analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES'
INTER=ADD/'SOURCE_INTERACTIONS'
SUP=ROOT/'analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS'
MODELS=['logistic','catboost','mlp']
LABELS={'logistic':'Logistic Regression','catboost':'CatBoost','mlp':'MLP'}
REPS=['RAW','CANONICALIZED']
COLORS={'RAW':'#0072B2','CANONICALIZED':'#D55E00'}
WIDTH=174/25.4
COMMAND=' '.join([sys.executable,*sys.argv])
FILES={
    '04':'04_marginal_gain_per_added_source',
    '05':'05_marginal_gain_by_source_and_pool_size',
    '06':'06_marginal_gain_by_source_and_target',
    '07':'07_source_contribution',
    '11':'11_controlled_separability',
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return str(Path(path).relative_to(ROOT.parent))


def text_color(rgba):
    rgb=np.array(rgba[:3]);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    lum=float(linear @ np.array([.2126,.7152,.0722]))
    black=(lum+.05)/.05;white=1.05/(lum+.05)
    return ('black',black) if black>=white else ('white',white)


class Revision:
    def __init__(self):
        AUDIT.mkdir(exist_ok=True)
        self.sources={};self.frames={};self.figures={};self.spec={};self.annotations=[];self.checks=[];self.values=[]
        self.previous={p.name:sha(p) for p in FINAL.glob('*.pdf')}
        assert len(self.previous)==11
        previous_audit=AUDIT/'VISUAL_REVISION_AUDIT.json'
        if previous_audit.exists():
            prior=json.loads(previous_audit.read_text())
            for record in prior['changed'].values():
                if self.previous.get(record['filename'])==record['pdf_sha256']:
                    self.previous[record['filename']]=record['old_pdf_sha256']
        self.input_docs={name:(FINAL/name).read_text() for name in ['LATEX_FIGURE_INDEX.md','MANUSCRIPT_FIGURE_TRACEABILITY.md']}
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8.5,'axes.titlesize':8.5,
            'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':8,'axes.linewidth':.6,
            'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})

    def read(self,path):
        frame=pd.read_parquet(path);csv=path.with_suffix('.csv')
        counterpart=pd.read_csv(csv,float_precision='round_trip',keep_default_na=False)
        pd.testing.assert_frame_equal(frame,counterpart,check_dtype=False,check_exact=True)
        for p in [path,csv]:self.sources[rel(p)]={'sha256':sha(p),'rows':len(frame)}
        return frame

    def used(self,number,frame,path,columns):
        for _,r in frame.iterrows():
            for column in columns:
                value=float(r[column])
                self.values.append(dict(figure=FILES[number],source_table=rel(path),source_row_id=r.row_id,
                    column=column,value=value,float64_hex=value.hex(),experiment_ids=r.experiment_ids))

    def check(self,figure,element,actual,expected):
        np.testing.assert_array_equal(np.asarray(actual),np.asarray(expected))
        self.checks.append({'figure':figure,'element':element,'exact_match':True,'n_values':int(np.size(expected))})

    def marginal(self):
        number='04';path=ADD/'tables/marginal_gain_by_pool_size_target_macro.parquet'
        d=self.read(path);d=d[d.n_sources_before.isin([1,2,3,4])].copy()
        assert d.n_targets.eq(7).all() and len(d)==24
        fig,axes=plt.subplots(2,3,figsize=(WIDTH,4.15),sharex='col',layout='constrained',gridspec_kw={'height_ratios':[3.2,1]})
        for j,model in enumerate(MODELS):
            ax=axes[0,j];strip=axes[1,j]
            series={rep:d[(d.model==model)&(d.representation==rep)].set_index('n_sources_before').loc[[1,2,3,4]] for rep in REPS}
            for rep in REPS:
                g=series[rep]
                line,=ax.plot(g.index,g.target_macro_mean_delta_f1,color=COLORS[rep],marker='o' if rep=='RAW' else 'D',ms=3.5,lw=1,label=rep)
                self.check(number,model+'/'+rep+' mean',line.get_ydata(),g.target_macro_mean_delta_f1)
                for k,row in g.iterrows():
                    other=series[REPS[1] if rep=='RAW' else REPS[0]].loc[k].target_macro_mean_delta_f1
                    offset=10 if row.target_macro_mean_delta_f1>=other else -13
                    annotation=ax.annotate(f'{row.target_macro_mean_delta_f1:+.3f}',(k,row.target_macro_mean_delta_f1),
                        xytext=(0,offset),textcoords='offset points',ha='center',va='center',fontsize=7.5,
                        color=COLORS[rep],bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':.3})
                    self.annotations.append((number,annotation,None))
            ax.axhline(0,color='#222222',lw=.9,ls='--',zorder=0)
            ax.set_ylim(-.032,.102);ax.set_xlim(.6,4.4);ax.set_title(LABELS[model],pad=7)
            ax.set_yticks([-.02,0,.02,.04,.06,.08,.10]);ax.grid(axis='y',alpha=.12)
            if j:ax.tick_params(labelleft=False)
            ax.spines[['top','right']].set_visible(False);ax.tick_params(axis='x',labelbottom=False)
            strip.set_title('Negative additions (%)',fontsize=7.5,pad=5)
            strip.set_ylim(1.5,-.5);strip.set_yticks([0,1],REPS if j==0 else ['', ''])
            strip.set_xticks([1,2,3,4],['1→2','2→3','3→4','4→5'])
            strip.tick_params(length=0,pad=5)
            for i,rep in enumerate(REPS):
                for k,row in series[rep].iterrows():
                    text=strip.text(k,i,f'{100*row.target_macro_fraction_negative:.0f}%',ha='center',va='center',fontsize=8,color=COLORS[rep])
                    self.annotations.append((number,text,None))
            for x in [1.5,2.5,3.5]:strip.axvline(x,color='#EEEEEE',lw=.6)
            for spine in strip.spines.values():spine.set_visible(False)
        axes[0,0].set_ylabel('Mean marginal ΔF1')
        fig.supxlabel('Source-pool size before → after (seven targets)',fontsize=8)
        fig.legend(*axes[0,0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.figures[number]=fig
        columns=['target_macro_mean_delta_f1','target_macro_fraction_negative']
        self.used(number,d,path,columns)
        self.spec[number]=dict(old='Edge-distribution boxplots',new='Target-macro connected points with signed values and aligned negative-addition percentage strips',
            sources=[rel(path)],columns=['model','representation','n_sources_before','n_targets',*columns],
            filters='n_sources_before in {1,2,3,4}; exactly seven targets in every plotted row. 5→6 omitted from this main figure; data remain unchanged in source.',
            aggregation='Already saved: matched-seed means within exact edges; within-target edge means/fractions; equal target macro means. No edge-weighted replacement.',
            calculations='Coordinates copied exactly; signed values formatted to3 decimals; target_macro_fraction_negative ×100 rounded to whole percent for display only. No aggregation or metrics recalculated.',
            caption='Target-macro marginal F1 change after adding one source, across seven targets. Each target receives equal weight after matched-seed and coalition-context aggregation. The lower strips show target-macro percentages of negative additions. Dashed line: zero gain. Only transitions1→2 through4→5 are connected;5→6 is omitted because its target cohort differs.',
            lineage=rel(ADD/'SOURCE_LINEAGE.parquet'))

    def heatmaps(self):
        paths={'05':INTER/'tables/marginal_gain_by_added_source_and_pool_size.parquet',
               '06':INTER/'tables/marginal_gain_by_added_source_target.parquet',
               '07':SUP/'tables/source_contribution_by_target.parquet'}
        frames={n:self.read(p) for n,p in paths.items()}
        # Same shared05/06 bound used in the previous validated render, including retained historical k5 data.
        bound=max(frames['05'].mean_target_delta_f1.abs().max(),frames['06'].mean_delta_f1.abs().max())
        for number in ['05','06','07']:
            d=frames[number]
            if number=='05':d=d[d.n_sources_before.isin([1,2,3,4])]
            sourcecol='removed_source' if number=='07' else 'added_source'
            valuecol={'05':'mean_target_delta_f1','06':'mean_delta_f1','07':'delta_f1_mean'}[number]
            xcol='n_sources_before' if number=='05' else 'target'
            sources=sorted(d[sourcecol].unique())
            xorder=list(range(1,5)) if number=='05' else sorted(d.target.unique())
            limit=float(d[valuecol].abs().max()) if number=='07' else float(bound)
            norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)
            rows,cols=(2,3) if number=='05' else (3,2)
            fig,axes=plt.subplots(rows,cols,figsize=(WIDTH,5.1 if number=='05' else 8.1),sharex=True,sharey=True,layout='constrained')
            cmap=plt.get_cmap('RdBu').copy();cmap.set_bad('#D9D9D9')
            for mi,model in enumerate(MODELS):
                for ri,rep in enumerate(REPS):
                    i,j=(ri,mi) if number=='05' else (mi,ri)
                    ax=axes[i,j];g=d[(d.model==model)&(d.representation==rep)]
                    wide=g.pivot(index=sourcecol,columns=xcol,values=valuecol).reindex(index=sources,columns=xorder)
                    data=wide.to_numpy()
                    artist=ax.pcolormesh(np.ma.masked_invalid(data),norm=norm,cmap=cmap,rasterized=False,edgecolors='white',linewidth=.45)
                    self.check(number,model+'/'+rep+' heatmap',np.ma.filled(artist.get_array(),np.nan).reshape(data.shape),data)
                    ax.set_ylim(len(sources),0);ax.set_title(LABELS[model]+'\n'+rep,pad=6)
                    ax.set_yticks(np.arange(len(sources))+.5,sources)
                    ax.set_xticks(np.arange(len(xorder))+.5,[str(k)+'→'+str(k+1) for k in xorder] if number=='05' else xorder,
                        rotation=0 if number=='05' else 55,ha='center' if number=='05' else 'right',rotation_mode='anchor')
                    ax.tick_params(length=0,pad=4)
                    if j==0:ax.set_ylabel('Source removed' if number=='07' else 'Added source')
                    if i==rows-1:ax.set_xlabel('Pool size before → after' if number=='05' else 'Target dataset' if number=='07' else 'Unseen target')
                    for spine in ax.spines.values():spine.set_visible(False)
                    for (y,x),value in np.ndenumerate(data):
                        if not np.isfinite(value):continue
                        color,contrast=text_color(cmap(norm(value)))
                        assert contrast>=4.5
                        text=ax.text(x+.5,y+.5,f'{value:+.3f}',ha='center',va='center',fontsize=7.5,color=color)
                        self.annotations.append((number,text,(ax,x,y)))
            bar=fig.colorbar(artist,ax=axes,orientation='horizontal',shrink=.84,fraction=.045,pad=.03,aspect=38)
            bar.set_label('Full-pool F1 − source-removed F1' if number=='07' else 'Mean ΔF1: after adding source minus before')
            bar.solids.set_rasterized(False)
            bar.solids.set_edgecolor('face')  # prevent PDF rasterizer seams between vector colorbar patches
            bar.ax.set_title('Gray: missing / ineligible',fontsize=7.5,pad=4)
            self.figures[number]=fig;self.used(number,d,paths[number],[valuecol])
            calculation=f'Existing cell values plotted without rounding; annotations only use signed3 decimals. Symmetric scale [−{limit!r},+{limit!r}], zero center. Automatic black/white text maximizes sRGB luminance contrast; missing cells masked gray and unannotated.'
            if number=='05':
                caption='Target-macro marginal F1 change by added source and existing pool size. Numeric annotations show signed effects; zero-centered colors are shared across all panels. Targets have equal weight after seed and within-target coalition aggregation. Only1→2 through4→5 are shown, preserving each source’s eligible target set. The5→6 results remain in the analytical table but are omitted here.'
                aggregation='Already saved: matched-seed edge means → contexts within target/source/model/view/k → equal targets.'
            elif number=='06':
                caption='Mean marginal change in target F1 when a source was added across all valid existing coalition contexts, not one dataset-addition order. Signed cell values and a shared zero-centered scale show magnitude and sign. Gray cells are self-target or otherwise ineligible. Six panels are arranged as model rows and representation columns for readable annotations.'
                aggregation='Already saved: matched-seed means within edges, then equal coalition contexts within source/target/model/view. Not independent targets or an arbitrary addition order.'
            else:
                caption='Controlled leave-one-source-out contribution: full-pool F1 minus source-removed F1. Positive values mean the source was beneficial because removing it reduced F1; negative values mean removing the source improved F1. Eligible matched-seed means are annotated; missing combinations remain gray. Six panels use model rows and representation columns.'
                aggregation='Already saved controlled supplement: same eligible seed pairs, fixed validation/test, full-pool minus source-removed F1. Original sign convention preserved.'
            self.spec[number]=dict(old='Unannotated six-panel heatmap',new='Annotated heatmap; '+('2 representation rows ×3 model columns; four transitions' if number=='05' else '3 model rows ×2 representation columns'),
                sources=[rel(paths[number])],columns=[sourcecol,xcol,'model','representation',valuecol],
                filters='n_sources_before in {1,2,3,4}' if number=='05' else 'All existing eligible rows; missing grid combinations remain missing.',
                aggregation=aggregation,calculations=calculation,caption=caption,
                lineage=rel(SUP/'SOURCE_FILES.parquet') if number=='07' else rel(INTER/'SOURCE_LINEAGE.parquet'))

    def separability(self):
        number='11';path=SUP/'tables/separability.parquet';delta_path=SUP/'tables/separability_paired_deltas.parquet'
        d=self.read(path);delta=self.read(delta_path).set_index('condition')
        conditions=['all','benign','malicious'];fig,ax=plt.subplots(figsize=(WIDTH,3.65),layout='constrained')
        for i,condition in enumerate(conditions):
            g=d[d.condition==condition].set_index('representation')
            raw=float(g.loc['RAW','origin_macro_f1_mean']);can=float(g.loc['CANONICALIZED','origin_macro_f1_mean'])
            connector,=ax.plot([raw,can],[i,i],color='#777777',lw=1.1,zorder=1)
            self.check(number,condition+' connector',connector.get_xdata(),[raw,can])
            for rep,value,marker,offset in [('RAW',raw,'o',12),('CANONICALIZED',can,'D',-16)]:
                point,=ax.plot([value],[i],marker=marker,ms=5.3,color=COLORS[rep],markeredgecolor='white',markeredgewidth=.45,
                    linestyle='none',label=rep if i==0 else None,zorder=3)
                self.check(number,condition+'/'+rep,point.get_xdata(),[value])
                text=ax.annotate(f'{rep} {value:.3f}',(value,i),xytext=(0,offset),textcoords='offset points',
                    ha='center',va='center',fontsize=8,color=COLORS[rep])
                self.annotations.append((number,text,None))
            # Use saved paired delta rather than calculating any new metric/difference.
            value=float(delta.loc[condition,'delta_origin_macro_f1_mean'])
            text=ax.text(.49,i,f'Δ = {value:+.3f}',ha='center',va='center',fontsize=8.5,color='#333333')
            self.annotations.append((number,text,None))
        chance=float(d.origin_chance_accuracy_uniform_mean.iloc[0])
        reference=ax.axvline(chance,ls='--',color='#555555',lw=1)
        self.check(number,'chance reference',reference.get_xdata(),[chance,chance])
        ax.text(chance+.015,.035,f'Uniform chance ≈ {chance:.3f}',transform=ax.get_xaxis_transform(),ha='left',va='bottom',fontsize=8,color='#444444')
        ax.set_xlim(0,1);ax.set_ylim(2.68,-.68);ax.set_yticks(range(3),['All samples','Benign only','Malicious only'])
        ax.set_xlabel('Dataset-origin macro-F1');ax.set_xticks(np.arange(0,1.01,.2))
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0,pad=8)
        fig.legend(*ax.get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.figures[number]=fig;self.used(number,d,path,['origin_macro_f1_mean','origin_chance_accuracy_uniform_mean'])
        self.used(number,delta.reset_index(),delta_path,['delta_origin_macro_f1_mean'])
        self.spec[number]=dict(old='Grouped bars with seed-SD error bars',new='Paired dumbbell/connected-dot plot, direct RAW/CANONICALIZED labels and saved paired deltas; SD bars omitted',
            sources=[rel(path),rel(delta_path)],columns=['condition','representation','origin_macro_f1_mean','origin_chance_accuracy_uniform_mean','delta_origin_macro_f1_mean'],
            filters='Conditions all,benign,malicious in that order; RAW and CANONICALIZED; x-axis0..1.',
            aggregation='Already saved seed means and saved mean paired CANONICALIZED-minus-RAW deltas; no recalculation. Chance copied from existing table.',
            calculations='No new metric calculations: coordinates and delta annotations from saved columns; labels rounded to3 decimals. Connect paired means visually; omit SD only from rendering.',
            caption='Dataset-origin separability as paired RAW and CANONICALIZED seed means for all samples, benign-only and malicious-only conditions. Labels show both saved means and saved paired Δ (CANONICALIZED minus RAW). The vertical dashed uniform reference is approximately0.143 (1/7; an asymptotic balanced macro-F1 reference, not a finite-sample guarantee). The x-axis spans0–1; seed SD is omitted for clarity.',
            lineage=rel(SUP/'SOURCE_FILES.parquet'))

    def layout_checks(self,number,fig):
        fig.canvas.draw();renderer=fig.canvas.get_renderer();records=[]
        for n,text,cell in self.annotations:
            if n!=number:continue
            bbox=text.get_window_extent(renderer)
            assert bbox.x0>=0 and bbox.y0>=0 and bbox.x1<=fig.bbox.width and bbox.y1<=fig.bbox.height,(number,'clipped',text.get_text())
            if cell:
                ax,x,y=cell;p0=ax.transData.transform((x,y));p1=ax.transData.transform((x+1,y+1))
                low=np.minimum(p0,p1);high=np.maximum(p0,p1)
                assert bbox.x0>low[0]+.5 and bbox.x1<high[0]-.5 and bbox.y0>low[1]+.5 and bbox.y1<high[1]-.5,(number,'cell border overlap',text.get_text(),bbox.width,high-low)
            records.append((text,bbox))
        for i,(a,boxa) in enumerate(records):
            for b,boxb in records[i+1:]:
                assert not boxa.overlaps(boxb),(number,'annotation overlap',a.get_text(),b.get_text())
        self.checks.append(dict(figure=number,element='annotation bounds and nonoverlap',exact_match=True,n_values=len(records)))

    def export(self):
        output={}
        # Stage every replacement first; a failed validation does not remove current manuscript PDFs.
        with tempfile.TemporaryDirectory(prefix='manuscript-visual-',dir=AUDIT) as staging:
            stage=Path(staging)
            for number,fig in self.figures.items():
                self.layout_checks(number,fig)
                pdf=stage/(FILES[number]+'.pdf')
                fig.savefig(pdf,metadata={'CreationDate':None,'ModDate':None,'Creator':rel(Path(__file__))});plt.close(fig)
                assert len(subprocess.check_output(['pdfimages','-list',str(pdf)],text=True).strip().splitlines())==2
                fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True)
                assert 'TrueType' in fonts and 'Type 3' not in fonts
                # Deliver the actual PDF rasterization, not a separately drawn PNG.
                subprocess.run(['pdftoppm','-r','300','-png','-singlefile',str(pdf),str(pdf.with_suffix(''))],check=True,stdout=subprocess.DEVNULL)
                png=pdf.with_suffix('.png')
                with Image.open(png) as image:
                    assert all(abs(v-300)<.01 for v in image.info['dpi'])
                    output[number]={'filename':pdf.name,'pdf_sha256':sha(pdf),'png_sha256':sha(png),'png_pixels':list(image.size),'dpi':300,
                        'old_pdf_sha256':self.previous[pdf.name],'vector_pdf':True,'fonts_embedded':True,'pdf_rendered_to_png':True,**self.spec[number]}
            for path,meta in self.sources.items():assert sha(ROOT.parent/path)==meta['sha256']
            for number in self.figures:
                for ext in ['.pdf','.png']:(stage/(FILES[number]+ext)).replace(FINAL/(FILES[number]+ext))
        unchanged={n:h for n,h in self.previous.items() if n not in [v+'.pdf' for v in FILES.values()]}
        for name,h in unchanged.items():assert sha(FINAL/name)==h
        pd.DataFrame(self.values).to_csv(AUDIT/'PLOTTED_SOURCE_VALUES.csv',index=False,float_format='%.17g')
        self.result={'generated_at':datetime.now(timezone.utc).isoformat(),'script':rel(Path(__file__)),'script_sha256':sha(__file__),
            'command':COMMAND,'sources':self.sources,'changed':output,'unchanged_pdf_sha256':unchanged,'checks':self.checks,
            'no_training':True,'no_prediction_regeneration':True,'no_metric_recomputation':True,'no_statistical_test_recomputation':True,
            'source_tables_unchanged':True,'visual_inspection_confirmed':False}
        (AUDIT/'VISUAL_REVISION_AUDIT.json').write_text(json.dumps(self.result,indent=2)+'\n')
        self.documents()

    def documents(self):
        index=self.input_docs['LATEX_FIGURE_INDEX.md']
        trace=self.input_docs['MANUSCRIPT_FIGURE_TRACEABILITY.md']
        for number,record in self.result['changed'].items():
            filename=record['filename'];stem=filename[:-4]
            block=f'''## {number} — {stem[3:].replace('_',' ')}

Filename: `{filename}`. Section: {'5.7 Canonicalization and Dataset Separability' if number=='11' else '5.4 Source-Dataset Contribution'}.

Purpose / suggested caption: {record['caption']}

Source analytical tables: {', '.join('`'+p+'`' for p in record['sources'])}.

Label: `fig:{stem[3:].replace('_','-')}`. Width: `\\textwidth` (174 mm, full two-column figure*).

```latex
\\includegraphics[width=\\textwidth]{{figures/manuscript_final/{filename}}}
```

Visual revision: {record['old']} → {record['new']}. Corresponding PDF-rendered PNG: `{stem}.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

'''
            index,count=re.subn(r'(?m)^## '+number+r' — .*?\n[\s\S]*?(?=^## |\Z)',lambda _:block,index,count=1)
            assert count==1
            block=f'''## {filename}

- Final PDF: `{rel(FINAL/filename)}`.
- Final PNG: `{rel(FINAL/(stem+'.png'))}`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: {record['old']}.
- New visualization: {record['new']}.
- Source analytical tables: {', '.join('`'+p+'`' for p in record['sources'])}; corresponding CSV files verified exactly against Parquet.
- Columns: {', '.join(record['columns'])}; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: {record['filters']}
- Aggregation ALREADY PRESENT: {record['aggregation']}
- Plotting-only calculations: {record['calculations']}
- Experiment lineage: `{record['lineage']}`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `{rel(Path(__file__))}`.
- Command: `{COMMAND}`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `{record['old_pdf_sha256']}`.
- Current PDF SHA-256: `{record['pdf_sha256']}`.
- Current PNG SHA-256: `{record['png_sha256']}`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: {record['caption']}

'''
            trace,count=re.subn(r'(?m)^## '+re.escape(filename)+r'\n[\s\S]*?(?=^## |\Z)',lambda _:block,trace,count=1)
            assert count==1
        index=index.replace('The clean inclusion directory contains final PDFs plus the two explicitly requested index/traceability documents; PNGs, analytical tables and scripts remain outside it.',
            'The inclusion directory contains eleven final PDFs, the requested revised-figure PNGs at300 dpi, and manuscript documentation. Analytical tables and plotting scripts remain outside it.')
        trace=trace.replace('All earlier PDFs were copied byte-for-byte after checking their existing validation-manifest hashes. New source-interaction figures use saved historical matched edges only. No originals were moved, deleted or rerendered.',
            'The initial collection copied validated PDFs byte-for-byte. The current visual revision replaces only04,05,06,07,11 in place; their updated sections supersede the initial collection hashes. All other manuscript PDFs and every upstream analytical table remain unchanged.')
        trace=trace.replace('Both analyses cover this same set; counting an edge in multiple summaries does not create independent observations.',
            'The underlying complete interaction tables cover that same set; revised figure05 displays only base sizes1..4, whereas figure06 retains all valid contexts. Counting an edge in multiple summaries does not create independent observations.')
        for name,text in [('LATEX_FIGURE_INDEX.md',index),('MANUSCRIPT_FIGURE_TRACEABILITY.md',trace)]:
            if 'Visual revision audit:' not in text:
                text+='\nVisual revision audit: `artigo/figures/visual_revision_audit/VISUAL_REVISION_AUDIT.json`. NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION. The original collection manifest is a historical snapshot; current hashes for revised figures are in this audit and the updated traceability sections.\n'
            (FINAL/name).write_text(text)
        write_report(self.result)


def write_report(result):
    lines=['# Final visual revision report','',
        'NO TRAINING · NO PREDICTION REGENERATION · NO METRIC RECOMPUTATION · NO STATISTICAL TEST RECOMPUTATION','',
        'All analytical tables and saved values remained unchanged. Revised figures replaced the same LaTeX-facing filenames in manuscript_final. Existing revised-name PNGs are replaced in place; no _v2/_new/_updated files or old/new PDF duplicates are retained in that directory. Upstream historical analytical figures were not modified.', '',
        '## Changed figures','']
    for number,r in result['changed'].items():
        lines += [f'- `{r["filename"]}` and `{r["filename"][:-4]}.png`: {r["old"]} → {r["new"]}.']
    lines += ['', '## Intentionally unchanged','',
        '01_lodo_by_target.pdf and10_canonicalization_effect.pdf already have readable numeric annotations and were checked without rerendering. Non-heatmaps02,03,08,09 were intentionally left unchanged; their SHA-256 values match the pre-revision files.', '',
        '## Numerical and visual checks','',
        '- CSV/Parquet source values agree exactly; Matplotlib data arrays match the saved source values before label formatting.',
        '- Three decimals affect annotation text only. No value was rounded before plotting. Negative percentages use the saved target-macro fraction, multiplied by100 only for display.',
        '- Figure11 deltas come directly from the existing separability_paired_deltas table; no new metric or paired-difference aggregation was computed.',
        '- Heatmap text contrast maximizes black/white contrast using sRGB relative luminance; contrast ≥4.5. Missing/ineligible cells remain gray and unannotated. Scales remain symmetric and exactly zero-centered.',
        '- Numeric labels are checked against cell borders and canvas bounds, and against other annotations for overlap.',
        '- Revised PDFs contain vector graphics and embedded TrueType fonts. Each was rasterized with pdftoppm at300 dpi to produce its delivered PNG.',
        '- PDF-to-PNG visual inspection: '+('CONFIRMED for all five revised figures.' if result['visual_inspection_confirmed'] else 'PENDING human/assistant visual inspection of the generated PNGs.'), '',
        '## Data Sources and Traceability','',
        'Per-figure old/new type, source table, columns, filters, existing aggregation, plotting-only operations and PDF/PNG hashes: MANUSCRIPT_FIGURE_TRACEABILITY.md. Updated captions/LaTeX paths: LATEX_FIGURE_INDEX.md.',
        f'Script: `{result["script"]}`. Command: `{result["command"]}`. Audit: `artigo/figures/visual_revision_audit/VISUAL_REVISION_AUDIT.json`. Exact plotted source values, hex-float values, source row IDs and experiment IDs: `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.',
        'Figure04 filters n_sources_before=1..4, all seven targets; figure05 likewise omits5→6. Figure06/07 use all existing eligible cells. Figure11 uses all three saved conditions. No seeds, targets, coalition contexts, SDs, thresholds, feature importances or statistical tests were reaggregated. Source SHA-256 values were checked unchanged before installation.',
        'The PNGs and the two updated figures04/11 supersede only their manuscript renderings; all prior scientific source tables remain valid. The directory now intentionally contains the PNGs and revision report explicitly requested in this revision, in addition to its existing PDFs and documentation.']
    (FINAL/'VISUAL_REVISION_REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-visual-review',action='store_true',help='Record completed visual inspection without rerendering any figure.')
    args=parser.parse_args()
    if args.confirm_visual_review:
        path=AUDIT/'VISUAL_REVISION_AUDIT.json';result=json.loads(path.read_text())
        for r in result['changed'].values():
            assert sha(FINAL/r['filename'])==r['pdf_sha256']
            assert sha((FINAL/r['filename']).with_suffix('.png'))==r['png_sha256']
        result['visual_inspection_confirmed']=True;result['visual_inspection_at']=datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(result,indent=2)+'\n');write_report(result)
        print('Visual inspection recorded; figures not rerendered.')
    else:
        r=Revision();r.marginal();r.heatmaps();r.separability();r.export()
        print(json.dumps({'changed':list(FILES.values()),'exact_checks':len(r.checks),'sources_unchanged':True,'visual_review_pending':True},indent=2))
