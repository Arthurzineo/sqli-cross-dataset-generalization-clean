#!/usr/bin/env python3
"""Formatting only: render saved analytical values, never import the analysis runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.ticker import MaxNLocator
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS'
OUTPUT = ROOT / 'figures/final'
MODELS = ['logistic', 'catboost', 'mlp']
LABELS = {'logistic': 'Logistic Regression', 'catboost': 'CatBoost', 'mlp': 'MLP'}
REPS = ['RAW', 'CANONICALIZED']
PALETTE = {'RAW': '#0072B2', 'CANONICALIZED': '#D55E00'}  # Okabe–Ito
WIDTH = 174 / 25.4  # mm -> inches; full Springer two-column width
SPECS = {
    'lodo_by_target': ('tables/lodo_by_target', ['target', 'model', 'representation', 'test_f1_mean']),
    'id_ood_common_test_gap': ('tables/id_ood_same_test', ['target', 'model', 'representation', 'gap_f1_mean']),
    'source_contribution': ('tables/source_contribution_by_target', ['target', 'removed_source', 'model', 'representation', 'delta_f1_mean']),
    'selected_score_shift': ('derived/selected_score_histograms', ['role', 'label', 'left', 'right', 'fraction']),
    'canonicalization_effect': ('tables/canonicalization_by_target', ['target', 'model', 'delta_test_f1_mean']),
    'controlled_separability': ('tables/separability', ['condition', 'representation', 'origin_macro_f1_mean', 'origin_macro_f1_std', 'origin_chance_accuracy_uniform_mean']),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return str(Path(path).relative_to(ROOT.parent))


class Renderer:
    def __init__(self):
        self.sources = {}
        self.tables = {}
        self.points = []
        self.checks = []
        self.figures = {}
        self.filters = {}
        self.extra = {}
        plt.rcParams.update({
            'font.family': 'DejaVu Sans', 'font.size': 8,
            'axes.labelsize': 8.5, 'axes.titlesize': 9, 'axes.titleweight': 'normal',
            'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
            'axes.linewidth': .6, 'lines.linewidth': 1.3,
            'xtick.major.width': .6, 'ytick.major.width': .6,
            'pdf.fonttype': 42, 'ps.fonttype': 42,
            'savefig.facecolor': 'white', 'figure.facecolor': 'white',
        })
        # Read only the seven explicitly named small analytical table pairs.
        for name in [v[0] for v in SPECS.values()] + ['selected_runs/cases']:
            parquet, csv = SOURCE / (name + '.parquet'), SOURCE / (name + '.csv')
            frame = pd.read_parquet(parquet)
            text = pd.read_csv(csv, float_precision='round_trip', keep_default_na=False)
            assert list(frame.columns) == list(text.columns)
            assert len(frame) == len(text)
            for col in frame:
                if pd.api.types.is_numeric_dtype(frame[col]):
                    np.testing.assert_array_equal(frame[col].to_numpy(), pd.to_numeric(text[col]).to_numpy())
                else:
                    assert frame[col].fillna('').astype(str).tolist() == text[col].fillna('').astype(str).tolist(), (name, col)
            assert frame.row_id.is_unique
            self.tables[name] = frame
            for path in [parquet, csv]:
                self.sources[relative(path)] = {'sha256': sha(path), 'rows': len(frame)}
        self.targets = sorted(self.tables['tables/lodo_by_target'].target.unique())
        selected = self.tables['selected_runs/cases']
        self.selected = selected[selected.criterion == 'largest_oracle_gap'].iloc[0]
        self.eid = json.loads(self.selected.experiment_ids)[0]
        # Preserve the original selection and row/line order exactly.
        h = self.tables['derived/selected_score_histograms']
        self.hist = h[h.experiment_ids == json.dumps([self.eid])]
        assert len(self.hist) > 0
        self.filters['selected_score_shift'] = 'experiment_ids == json.dumps([first ID in first selected_runs/cases row with criterion == largest_oracle_gap]); ' + self.eid
        for name in SPECS:
            self.filters.setdefault(name, 'All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.')
        self.original_hashes = {
            relative(SOURCE / 'figures' / (name + ext)): sha(SOURCE / 'figures' / (name + ext))
            for name in SPECS for ext in ['.pdf', '.png']
        }
        self.original_script = ROOT / 'scripts/analyze_supplemental_results.py'
        self.original_hashes[relative(self.original_script)] = sha(self.original_script)

    def record(self, name, frame, columns):
        table = SPECS[name][0]
        for _, row in frame.iterrows():
            for col in columns:
                value = float(row[col])
                self.points.append(dict(figure=name, source_table=relative(SOURCE / (table + '.parquet')),
                    source_row_id=row.row_id, source_column=col, value=value, float64_hex=value.hex(),
                    experiment_ids=row.experiment_ids))

    def check(self, name, element, actual, expected):
        np.testing.assert_array_equal(np.asarray(actual), np.asarray(expected))
        self.checks.append(dict(figure=name, element=element, values=int(np.size(expected)), exact_match=True))

    def mesh(self, name, ax, data, norm, cmap, annotate=False, signed=False):
        colors=plt.get_cmap(cmap).copy(); colors.set_bad('#D9D9D9')
        array=data.to_numpy(dtype=float)
        artist=ax.pcolormesh(np.arange(array.shape[1]+1), np.arange(array.shape[0]+1),
                            np.ma.masked_invalid(array), norm=norm, cmap=colors, rasterized=False,
                            edgecolors='white', linewidth=.3)
        self.check(name, 'heatmap values', np.ma.filled(artist.get_array(), np.nan).reshape(array.shape), array)
        ax.set_ylim(array.shape[0],0)
        ax.set_xticks(np.arange(array.shape[1])+.5)
        ax.set_yticks(np.arange(array.shape[0])+.5, data.index)
        ax.tick_params(length=0, pad=4)
        for spine in ax.spines.values():spine.set_visible(False)
        if annotate:
            for (i,j), value in np.ndenumerate(array):
                if not np.isfinite(value):continue
                red,green,blue,_=colors(norm(value))
                luminance=.2126*red+.7152*green+.0722*blue
                ax.text(j+.5,i+.5,format(value,'+.3f' if signed else '.3f'),
                        ha='center',va='center',fontsize=8,color='white' if luminance<.48 else '#111111')
        return artist

    @staticmethod
    def colorbar(fig, artist, ax, label, **kwargs):
        bar=fig.colorbar(artist,ax=ax,**kwargs)
        bar.set_label(label)
        bar.outline.set_linewidth(.5)
        if bar.solids is not None:bar.solids.set_rasterized(False)
        return bar

    @staticmethod
    def clean(ax):
        ax.spines[['top','right']].set_visible(False)
        ax.set_axisbelow(True)

    def build(self):
        name='lodo_by_target'; d=self.tables[SPECS[name][0]]
        wide=d.pivot(index='target',columns=['model','representation'],values='test_f1_mean').reindex(
            index=self.targets,columns=pd.MultiIndex.from_product([MODELS,REPS]))
        fig,ax=plt.subplots(figsize=(WIDTH,3.7),layout='constrained')
        im=self.mesh(name,ax,wide,Normalize(.5,1),'viridis',annotate=True)
        ax.set_xticklabels(REPS*3,fontsize=7.5)
        ax.set_ylabel('Target dataset')
        top=ax.secondary_xaxis('top');top.set_xticks([1,3,5],[LABELS[m] for m in MODELS])
        top.tick_params(length=0,pad=7,labelsize=8.5);top.spines['top'].set_visible(False)
        for x in [2,4]:ax.axvline(x,color='white',lw=1.5)
        self.colorbar(fig,im,ax,'Attack F1 (seed mean)',fraction=.045,pad=.025)
        self.record(name,d,['test_f1_mean']);self.figures[name]=fig

        name='canonicalization_effect';d=self.tables[SPECS[name][0]]
        wide=d.pivot(index='target',columns='model',values='delta_test_f1_mean').reindex(index=self.targets,columns=MODELS)
        bound=np.abs(wide.to_numpy()).max()
        fig,ax=plt.subplots(figsize=(WIDTH,3.6),layout='constrained')
        im=self.mesh(name,ax,wide,TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),'RdBu',annotate=True,signed=True)
        ax.set_xticklabels([LABELS[m] for m in MODELS]);ax.set_ylabel('Target dataset')
        self.colorbar(fig,im,ax,'F1: CANONICALIZED − RAW',fraction=.045,pad=.025)
        self.record(name,d,['delta_test_f1_mean']);self.figures[name]=fig

        name='id_ood_common_test_gap';d=self.tables[SPECS[name][0]]
        fig,axes=plt.subplots(1,3,figsize=(WIDTH,3.5),sharey=True,sharex=True,layout='constrained')
        for ax,model in zip(axes,MODELS):
            for offset,rep in [(-.17,'RAW'),(.17,'CANONICALIZED')]:
                g=d[(d.model==model)&(d.representation==rep)].set_index('target').loc[self.targets]
                bars=ax.barh(np.arange(len(self.targets))+offset,g.gap_f1_mean,height=.32,label=rep,color=PALETTE[rep])
                self.check(name,model+'/'+rep,[b.get_width() for b in bars],g.gap_f1_mean)
            ax.set_yticks(range(len(self.targets)),self.targets)
            ax.axvline(0,color='#333333',lw=.6)
            ax.set_title(LABELS[model],pad=7);ax.xaxis.set_major_locator(MaxNLocator(4))
            ax.grid(axis='x',alpha=.15);self.clean(ax)
        axes[0].set_ylabel('Target dataset')
        fig.supxlabel('F1 ID − OOD (same test)',fontsize=8.5)
        fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.record(name,d,['gap_f1_mean']);self.figures[name]=fig

        name='source_contribution';d=self.tables[SPECS[name][0]]
        bound=float(d.delta_f1_mean.abs().max())
        norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
        fig,axes=plt.subplots(2,3,figsize=(WIDTH,6.15),sharex=True,sharey=True,layout='constrained')
        for i,rep in enumerate(REPS):
            for j,model in enumerate(MODELS):
                ax=axes[i,j];g=d[(d.model==model)&(d.representation==rep)]
                wide=g.pivot(index='removed_source',columns='target',values='delta_f1_mean').reindex(index=self.targets,columns=self.targets)
                im=self.mesh(name,ax,wide,norm,'RdBu')
                ax.set_aspect('equal');ax.set_title(LABELS[model]+'\n'+rep,fontsize=8.5,pad=5)
                ax.set_xticklabels(self.targets,rotation=55,ha='right',rotation_mode='anchor',fontsize=7.5)
                ax.tick_params(axis='y',labelsize=7.5)
                if j==0:ax.set_ylabel('Source removed')
                if i==1:ax.set_xlabel('Target dataset')
        bar=self.colorbar(fig,im,axes,'Full-pool F1 minus source-removed F1',orientation='horizontal',fraction=.06,pad=.025,shrink=.8,aspect=35)
        bar.ax.set_title('Gray: ineligible source–target combination',fontsize=7.5,pad=5)
        self.record(name,d,['delta_f1_mean']);self.figures[name]=fig

        name='controlled_separability';d=self.tables[SPECS[name][0]]
        fig,ax=plt.subplots(figsize=(WIDTH,3.1),layout='constrained')
        conditions=['all','benign','malicious']
        for offset,rep in [(-.18,'RAW'),(.18,'CANONICALIZED')]:
            g=d[d.representation==rep].set_index('condition').loc[conditions]
            bars=ax.bar(np.arange(3)+offset,g.origin_macro_f1_mean,width=.35,yerr=g.origin_macro_f1_std,
                        label=rep,color=PALETTE[rep],capsize=3,error_kw={'elinewidth':.8,'capthick':.8})
            self.check(name,rep+' bar heights',[b.get_height() for b in bars],g.origin_macro_f1_mean)
            segments=bars.errorbar.lines[2][0].get_segments()
            self.check(name,rep+' SD endpoints',[s[:,1] for s in segments],
                np.column_stack([g.origin_macro_f1_mean-g.origin_macro_f1_std,g.origin_macro_f1_mean+g.origin_macro_f1_std]))
        chance=float(d.origin_chance_accuracy_uniform_mean.iloc[0])
        line=ax.axhline(chance,ls='--',lw=1,color='#555555',label='Uniform balanced asymptotic reference')
        self.check(name,'chance reference',line.get_ydata(),[chance,chance])
        ax.set_xticks(range(3),['All classes','Benign only','Malicious only']);ax.set_ylim(0,1)
        ax.set_ylabel('Origin macro-F1 (seed mean ± SD)');self.clean(ax)
        handles=dict(zip(*reversed(ax.get_legend_handles_labels())))
        order=['RAW','Uniform balanced asymptotic reference','CANONICALIZED']
        fig.legend([handles[label] for label in order],order,loc='outside upper center',ncol=2,frameon=False)
        self.record(name,d,['origin_macro_f1_mean','origin_macro_f1_std','origin_chance_accuracy_uniform_mean']);self.figures[name]=fig

        name='selected_score_shift';fig,ax=plt.subplots(figsize=(WIDTH,3.2),layout='constrained')
        for (role,label),g in self.hist.groupby(['role','label']):
            x=(g.left+g.right)/2  # unchanged original bin-center plotting expression
            role_label={'test':'Target test','validation':'Source validation'}[role]
            line,=ax.plot(x,g.fraction,label=role_label+' / '+('attack' if label else 'benign'),
                ls='-' if role=='test' else '--',color='#D55E00' if label else '#0072B2')
            self.check(name,role+'/'+str(label)+' y',line.get_ydata(),g.fraction)
            self.check(name,role+'/'+str(label)+' x (existing bin centers)',line.get_xdata(),x)
        ax.set_xlabel('Attack score');ax.set_ylabel('Fraction within role/class')
        self.clean(ax);ax.grid(axis='y',alpha=.15)
        fig.legend(*ax.get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.record(name,self.hist,['left','right','fraction']);self.figures[name]=fig

    def trace(self, complete=False):
        lines=['# Final manuscript figure traceability','',
            'Visual formatting only. No experiments, metrics, statistical tests, model outputs, seed aggregation, or histograms were recomputed. Only the saved analytical tables were read. CSV values parsed with float_precision=round_trip match their Parquet counterparts exactly. Matplotlib artist data are checked against those values before any figure is saved.', '',
            'Original plotting recipe: `artigo/scripts/analyze_supplemental_results.py`, `Analysis.plots`; not imported or executed. Source PDF/PNG files remain untouched. The existing representative score run, all seed means/SDs, heatmap bounds, missing cells and chance reference are preserved. Annotation precision remains three decimals; plotted values are never rounded.', '',
            'Format: vector PDF (embedded TrueType DejaVu Sans, no rasterized heatmaps), PNG at 300 dpi; 174 mm full two-column width, 7.5–9 pt labels. Do not shrink these multi-panel figures to single-column width. Okabe–Ito blue/orange distinguish representations/classes; RdBu is a diverging zero-centered scale. Model labels: Logistic Regression, CatBoost, MLP. Representations: RAW, CANONICALIZED. Captions belong in the manuscript.', '',
            '**Status:** '+('Rendered and verified.' if complete else 'Source and plotted-value verification passed; output rendering pending.'),'',
            '## Data Sources and Traceability','',
            'Exactly seven existing CSV/Parquet table pairs are read (six data tables and one existing selection table). Full paths, columns, filters, hashes and row counts are below and in `FIGURE_VALIDATION.json`. Each plotted source value, original row_id and experiment_ids are recorded in `PLOTTED_VALUES.csv`; float64_hex preserves the exact binary value. No new means, SDs, thresholds, metrics or tests were computed.', '',
            f'Script: `{relative(Path(__file__))}`. Command: `{sys.executable} {relative(Path(__file__))}`. Script SHA-256: `{sha(__file__)}`.', '',
            'Seed aggregation is inherited unchanged from each existing analytical table. All figures use saved seed means; controlled_separability additionally uses the saved seed SD, not a confidence interval. Score fractions were already computed by the original analysis; the sole plotting coordinate formula is x=(left+right)/2 for those existing bins.', '']
        for name,(table,cols) in SPECS.items():
            lines += [f'## {name}','',f'- Source table: `{relative(SOURCE/(table+".parquet"))}`.',
                f'- Corresponding CSV: `{relative(SOURCE/(table+".csv"))}`.',
                '- Columns: '+', '.join('`'+c+'`' for c in cols+['row_id','experiment_ids'])+'.',
                '- Filters: '+self.filters[name],
                f'- Script: `{relative(Path(__file__))}`; original recipe: `Analysis.plots` in `{relative(self.original_script)}`.',
                f'- Output PDF: `{relative(OUTPUT/(name+".pdf"))}`.',
                f'- Output PNG: `{relative(OUTPUT/(name+".png"))}`.']
            if name=='selected_score_shift':
                lines += ['- Selection table: `'+relative(SOURCE/'selected_runs/cases.parquet')+'`; columns criterion, experiment_ids, row_id. Same saved selection, no reselection or score loading.',
                    '- Selected experiment ID: `'+self.eid+'`.']
            if name=='source_contribution':lines += ['- Sign: **full-pool F1 minus source-removed F1**. Shared symmetric color bounds use the existing maximum absolute delta; zero is the center. Gray cells remain missing/ineligible, never zero-filled.']
            if name=='controlled_separability':lines += ['- Chance-reference line is copied from origin_chance_accuracy_uniform_mean.iloc[0]; label retains the original asymptotic-reference qualification.']
            for ext in ['.parquet','.csv']:
                source=relative(SOURCE/(table+ext));lines.append(f'- Source {ext} SHA-256: `{self.sources[source]["sha256"]}`.')
            if complete:
                for ext in ['.pdf','.png']:lines.append(f'- Output {ext} SHA-256: `{sha(OUTPUT/(name+ext))}`.')
            lines.append('')
        return '\n'.join(lines)+'\n'

    def write(self, overwrite=False):
        OUTPUT.mkdir(parents=True,exist_ok=True)
        names=[name+ext for name in SPECS for ext in ['.pdf','.png']]
        names+=['FIGURE_TRACEABILITY.md','FIGURE_VALIDATION.json','PLOTTED_VALUES.csv']
        existing=[OUTPUT/n for n in names if (OUTPUT/n).exists()]
        if existing and not overwrite:
            raise FileExistsError('Final outputs already exist; inspect them and use --overwrite to back them up before replacement.')
        # All table comparisons and artist checks already passed before writing.
        if existing:
            backup=OUTPUT/'backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup.mkdir(parents=True)
            for path in existing:shutil.copy2(path,backup/path.name)
        (OUTPUT/'FIGURE_TRACEABILITY.md').write_text(self.trace())
        points=pd.DataFrame(self.points)
        points.to_csv(OUTPUT/'PLOTTED_VALUES.csv',index=False,float_format='%.17g')
        output_info={}
        with tempfile.TemporaryDirectory(prefix='manuscript-render-',dir=OUTPUT) as staging:
            staging=Path(staging)
            for name,fig in self.figures.items():
                fig.canvas.draw()
                renderer=fig.canvas.get_renderer()
                texts=list(fig.texts)
                for ax in list(fig.axes)+[child for ax in fig.axes for child in ax.child_axes]:
                    texts.extend([ax.xaxis.label,ax.yaxis.label,ax.title])
                    for axis,limits in [(ax.xaxis,ax.get_xlim()),(ax.yaxis,ax.get_ylim())]:
                        lo,hi=sorted(limits)
                        for tick in axis.get_major_ticks():
                            if lo<=tick.get_loc()<=hi:texts.extend([tick.label1,tick.label2])
                for text in texts:
                    if not text.get_visible() or not text.get_text():continue
                    box=text.get_window_extent(renderer)
                    assert box.x0>=-1 and box.y0>=-1 and box.x1<=fig.bbox.width+1 and box.y1<=fig.bbox.height+1,(name,'clipped text',text.get_text())
                for legend in fig.legends:
                    box=legend.get_window_extent(renderer)
                    assert box.x0>=-1 and box.y0>=-1 and box.x1<=fig.bbox.width+1 and box.y1<=fig.bbox.height+1,(name,'clipped legend')
                # Fixed physical size: no tight crop that silently changes publication width.
                fig.savefig(staging/(name+'.pdf'),metadata={'Creator':relative(Path(__file__)),'CreationDate':None,'ModDate':None})
                fig.savefig(staging/(name+'.png'),dpi=300)
                with Image.open(staging/(name+'.png')) as image:
                    assert all(abs(d-300)<.01 for d in image.info['dpi'])
                    output_info[name]={'inches':list(fig.get_size_inches()),'png_pixels':list(image.size),'png_dpi':image.info['dpi']}
                output_info[name]['text_within_canvas']=True
                if shutil.which('pdfimages'):
                    images=subprocess.check_output(['pdfimages','-list',str(staging/(name+'.pdf'))],text=True)
                    assert len(images.strip().splitlines())==2,(name,'raster PDF content')
                    output_info[name]['pdf_raster_images']=0
                if shutil.which('pdffonts'):
                    fonts=subprocess.check_output(['pdffonts',str(staging/(name+'.pdf'))],text=True)
                    assert 'Type 3' not in fonts and 'TrueType' in fonts,(name,'unexpected PDF font')
                    output_info[name]['pdf_fonts']=fonts
                plt.close(fig)
            for path,info in self.sources.items():assert sha(ROOT.parent/path)==info['sha256']
            for path,digest in self.original_hashes.items():assert sha(ROOT.parent/path)==digest
            for name in names[:12]:(staging/name).replace(OUTPUT/name)
        report=dict(script=relative(Path(__file__)),script_sha256=sha(__file__),sources=self.sources,
            checks=self.checks,outputs=output_info,original_files_unchanged=True,csv_parquet_exact_match=True,
            source_value_count=len(points),selected_experiment_id=self.eid,
            original_file_sha256=self.original_hashes,scientific_recomputations=0,
            numeric_storage='PLOTTED_VALUES.csv: exact float64 hex plus 17-significant-digit decimal',
            output_sha256={name:sha(OUTPUT/name) for name in names[:12]})
        (OUTPUT/'FIGURE_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
        (OUTPUT/'FIGURE_TRACEABILITY.md').write_text(self.trace(complete=True))
        print(json.dumps({'outputs':str(OUTPUT),'figures':len(self.figures),'exact_artist_checks':len(self.checks),
                          'source_values':len(points),'scientific_recomputations':0},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite',action='store_true',help='Back up existing final outputs before replacing them; never modifies original analysis figures.')
    args=parser.parse_args()
    renderer=Renderer();renderer.build();renderer.write(args.overwrite)
