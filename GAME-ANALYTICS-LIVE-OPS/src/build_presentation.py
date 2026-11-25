#!/usr/bin/env python3
"""Build the eight-slide executive readout plus technical appendix."""
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_THEME_COLOR

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'outputs'; T=OUT/'tables'; C=OUT/'charts'; PRES=ROOT/'presentation'
PRES.mkdir(exist_ok=True)
NAME='Akshay kumar korepu'; ROLL='24MAB0A03'
NAVY=RGBColor(25,42,72); TEAL=RGBColor(16,122,116); GREY=RGBColor(93,105,122); LIGHT=RGBColor(242,245,249); DARK=RGBColor(35,43,55); WHITE=RGBColor(255,255,255); ORANGE=RGBColor(222,133,30); RED=RGBColor(183,55,55)

# Load analysis outputs.
summary=pd.read_json(OUT/'analysis_summary.json',typ='series')
daily=pd.read_csv(T/'daily_health_platform_summary.csv')
ret=pd.read_csv(T/'weekly_retention.csv')
conc=pd.read_csv(T/'revenue_concentration.csv')
fp=pd.read_csv(T/'first_purchase_delay_summary.csv')
repeat=pd.read_csv(T/'repeat_purchase_gap_summary.csv').iloc[0]
adcap=pd.read_csv(T/'ad_cap_by_cap.csv')
aduniq=pd.read_csv(T/'ad_cap_unique.csv').iloc[0]
adstatus=pd.read_csv(T/'ad_status_summary.csv').iloc[0]
arp_tier=pd.read_csv(T/'arpdau_by_country_tier.csv')
arp_period=pd.read_csv(T/'arpdau_period_summary.csv')
arp_mix=pd.read_csv(T/'arpdau_mix_decomposition.csv')
acqsum=pd.read_csv(T/'acquisition_channel_summary.csv')
acqcoef=pd.read_csv(T/'acquisition_channel_regression.csv')
thresh=pd.read_csv(T/'churn_threshold_metrics.csv')
churnseg=pd.read_csv(T/'churn_tenure_diagnostics.csv')
churncoef=pd.read_csv(T/'churn_model_coefficients.csv')

# DAU chart generated from canonical activity data.
pd_day=pd.read_csv(DATA/'player_day.csv')
pd_day['date']=pd.to_datetime(pd_day.activity_date.astype(str),format='%Y%m%d')
dau=pd_day.groupby('date').device_id.nunique().rename('dau').reset_index()
fig,ax=plt.subplots(figsize=(9,3.7)); ax.plot(dau.date,dau.dau); ax.set_title('Daily active players, Jan–Apr 2026'); ax.set_ylabel('DAU'); ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d')); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(C/'daily_dau_trend.png',dpi=180); plt.close(fig)

prs=Presentation(); prs.slide_width= Inches(13.333); prs.slide_height= Inches(7.5)
blank=prs.slide_layouts[6]

def add_bg(slide, color=WHITE):
    fill=slide.background.fill; fill.solid(); fill.fore_color.rgb=color

def add_text(slide, x,y,w,h, text, size=16, color=DARK, bold=False, font='Aptos', align=None):
    box=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=box.text_frame; tf.clear(); tf.word_wrap=True
    p=tf.paragraphs[0]; p.text=str(text); p.font.name=font; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=color
    if align is not None: p.alignment=align
    return box

def add_title(slide,title,subtitle=None,appendix=False):
    add_text(slide,.55,.28,12.2,.52,title,25,NAVY,True)
    if subtitle: add_text(slide,.58,.83,12.1,.35,subtitle,10,GREY)
    line=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.58), Inches(1.22), Inches(12.15), Inches(.025))
    line.fill.solid(); line.fill.fore_color.rgb=TEAL; line.line.fill.background()
    footer=f'{NAME}  |  {ROLL}  |  DBMS Lab  |  '+('Technical appendix' if appendix else 'Executive readout')
    add_text(slide,.6,7.18,11.9,.18,footer,8,GREY)

def add_bullets(slide,x,y,w,h,items,size=16,color=DARK,spacing=8):
    box=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf=box.text_frame; tf.clear(); tf.word_wrap=True
    for i,item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text='• '+item; p.font.name='Aptos'; p.font.size=Pt(size); p.font.color.rgb=color; p.space_after=Pt(spacing)
    return box

def add_kpi(slide,x,y,w,h,label,value,sub=None,accent=TEAL):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=LIGHT; sh.line.color.rgb=RGBColor(220,226,234)
    add_text(slide,x+.16,y+.12,w-.32,.25,label,10,GREY,True)
    add_text(slide,x+.16,y+.42,w-.32,.55,value,25,accent,True)
    if sub: add_text(slide,x+.16,y+1.02,w-.32,.38,sub,9,GREY)

def add_image(slide,path,x,y,w,h):
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))

def add_table(slide,x,y,w,h,headers,rows,font_size=10):
    tbl=slide.shapes.add_table(len(rows)+1,len(headers), Inches(x), Inches(y), Inches(w), Inches(h)).table
    for j,head in enumerate(headers):
        c=tbl.cell(0,j); c.text=str(head); c.fill.solid(); c.fill.fore_color.rgb=NAVY
        for p in c.text_frame.paragraphs:
            p.font.size=Pt(font_size); p.font.bold=True; p.font.color.rgb=WHITE
    for i,row in enumerate(rows,1):
        for j,val in enumerate(row):
            c=tbl.cell(i,j); c.text=str(val); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2 else LIGHT
            for p in c.text_frame.paragraphs:
                p.font.size=Pt(font_size); p.font.color.rgb=DARK
    return tbl

# Slide 1 — title + executive summary
s=prs.slides.add_slide(blank); add_bg(s)
add_text(s,.75,.65,11.8,.5,'DBMS LAB END-SEM PROJECT',15,TEAL,True)
add_text(s,.75,1.25,11.7,1.25,'Player Telemetry Analytics',34,NAVY,True)
add_text(s,.78,2.55,11.5,.5,'Product health, monetisation mix, acquisition quality and 14-day churn prediction',16,GREY)
add_text(s,.8,3.45,5.7,.85,f'{NAME}\nRoll No. {ROLL}',17,DARK,True)
add_text(s,.8,4.35,5.8,.55,'National Institute of Technology Warangal\nDBMS Lab  |  Dr. Vikas Srivastava',12,GREY)
add_kpi(s,7.1,3.25,2.5,1.55,'Blended ARPDAU change','−16.5%','Jan 1–30 vs Apr 1–30',RED)
add_kpi(s,9.85,3.25,2.5,1.55,'Tier 4 DAU mix','17.7% → 46.0%','Largest composition shift',ORANGE)
add_kpi(s,7.1,5.05,2.5,1.55,'Churn model PR-AUC','0.420','Baseline prevalence: 0.191',TEAL)
add_kpi(s,9.85,5.05,2.5,1.55,'Player records','80,295','Five telemetry datasets',NAVY)
add_text(s,.8,6.55,11.8,.35,'Executive readout (8 slides) followed by technical appendices.',10,GREY)

# Slide 2 — product health
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'1. The player base expanded, while platform monetisation differs','The four-month telemetry window shows strong activity growth; iOS monetises at a higher rate per active player.')
add_image(s,C/'daily_dau_trend.png',.7,1.45,7.2,4.6)
rows=[]
for r in daily.itertuples():
    rows.append([r.platform,f'{r.mean_dau:,.0f}',f'${r.mean_daily_gross_iap_usd:,.0f}',f'${r.mean_daily_arpdau:.3f}',f'{r.mean_daily_active_payer_pct:.2f}%'])
add_table(s,8.1,1.75,4.6,1.65,['Platform','Mean DAU','Daily IAP','Mean ARPDAU','Active payer %'],rows,9)
add_kpi(s,8.15,4.0,2.0,1.45,'DAU on Jan 1','1,789','Partial first day',NAVY)
add_kpi(s,10.35,4.0,2.0,1.45,'DAU on Apr 30','11,097','6.2× Jan 1 level',TEAL)
add_text(s,8.15,5.75,4.45,.8,'Payer-share correction: only purchasers with same-day activity are counted. The friend’s higher percentages included 2,429 off-session payer-days.',11,GREY)

# Slide 3 — retention and spender behaviour
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'2. Retention is modest; revenue is concentrated among a minority','Exact-day retention uses 2026 install cohorts only; immature cohort milestones are left blank.')
add_image(s,C/'retention_heatmap.png',.65,1.42,7.2,5.2)
concp=conc.set_index('population')
payer=concp.loc['payers_only']
add_kpi(s,8.05,1.6,2.0,1.45,'Never paid','86.2%','Of all profiles',ORANGE)
add_kpi(s,10.25,1.6,2.0,1.45,'Top 10% payers','47.6%','Share of payer revenue',TEAL)
add_kpi(s,8.05,3.35,2.0,1.45,'First purchase','22 days','Median among valid payers',NAVY)
add_kpi(s,10.25,3.35,2.0,1.45,'Repeat gap','15.3 days','Median consecutive purchase gap',NAVY)
add_text(s,8.1,5.15,4.1,1.0,'The 110 negative install-to-purchase delays are excluded from nonnegative delay percentiles and documented as a date anomaly.',11,GREY)

# Slide 4 — ARPDAU deep dive
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'3. The ARPDAU decline is a mix shift, not within-tier deterioration','Every country tier improved, but Tier 4 grew to nearly half of active player-days.')
add_image(s,C/'arpdau_by_tier.png',.65,1.42,6.1,3.9)
add_image(s,C/'dau_mix_shift.png',6.85,1.42,5.8,3.9)
add_kpi(s,.85,5.55,2.55,1.15,'Within-tier effect','+$0.0186','Positive contribution',TEAL)
add_kpi(s,3.65,5.55,2.55,1.15,'Tier-mix effect','−$0.0771','Negative contribution',RED)
add_kpi(s,6.45,5.55,2.55,1.15,'Blended change','−$0.0585','−16.51% overall',RED)
add_text(s,9.25,5.55,3.25,1.15,'Recommendation: investigate the acquisition and activity mix by tier before changing monetisation prices or offers.',11,GREY)

# Slide 5 — acquisition
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'4. The paid-video LTV gap largely disappears after adjustment','30-day outcomes for 37,489 installs from Jan 1–Mar 31; adjusted for country tier, platform and install week.')
add_image(s,C/'acquisition_ltv_coefficients.png',.65,1.45,6.2,4.8)
rows=[]
for r in acqsum.itertuples():
    rows.append([r.acquisition_channel.replace('_',' '),f'{r.installs:,}',f'{r.mean_active_days_30:.2f}',f'${r.mean_gross_iap_ltv_30:.2f}',f'{r.payer_share:.1%}'])
add_table(s,7.0,1.7,5.6,2.0,['Channel','Installs','Active days','30d IAP LTV','Payer share'],rows,9)
add_bullets(s,7.1,4.05,5.35,2.2,[
    'Paid video unadjusted LTV gap: −$0.92 (95% CI −$1.18 to −$0.67).',
    'Adjusted gap: −$0.14 (95% CI −$0.45 to +$0.16; p=0.366).',
    'No CPI or ad-revenue data: ROI and budget optimality cannot be inferred.'
],11,spacing=8)

# Slide 6 — churn
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'5. Logistic regression ranks churn risk better than the prevalence baseline','Train snapshot: Mar 31. Out-of-time test snapshot: Apr 15. Churn means no activity in the next 14 days.')
add_image(s,C/'churn_precision_recall.png',.65,1.42,6.4,4.9)
add_kpi(s,7.35,1.65,2.15,1.4,'ROC-AUC','0.757','Ranking quality',TEAL)
add_kpi(s,9.75,1.65,2.15,1.4,'PR-AUC','0.420','Baseline: 0.191',TEAL)
rows=[]
for r in thresh.itertuples():
    rows.append([f'{r.threshold:.2f}',f'{r.targeted_players:,}',f'{r.precision:.1%}',f'{r.recall:.1%}'])
add_table(s,7.35,3.45,4.65,2.15,['Threshold','Targeted','Precision','Recall'],rows,9)
add_text(s,7.4,5.9,4.9,.75,'Lower thresholds catch more churners but send more offers to players who would stay.',11,GREY)

# Slide 7 — operational recommendations
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'6. Turn model scores into a controlled live-ops test','The model supports prioritisation; only a randomized holdout can measure incremental saves.')
add_bullets(s,.85,1.55,5.8,4.9,[
    'Use 0.35 as a candidate threshold for low-cost in-app interventions: 44.2% precision and 39.7% recall; targets 6,443 of 37,455 test players.',
    'Use a higher threshold such as 0.55 for expensive offers: 62.9% precision but only 6.5% recall.',
    'Calibrate by tenure: test churn prevalence rises from 4.8% in days 1–7 to 36.7% at 90+ days.',
    'Run an offer/no-offer randomized holdout and estimate save lift before scaling.'
],15,spacing=13)
add_kpi(s,7.2,1.75,2.2,1.55,'Low-cost test','0.35','Broader coverage',TEAL)
add_kpi(s,9.7,1.75,2.2,1.55,'High-cost test','0.55','Higher precision',ORANGE)
add_text(s,7.25,4.0,4.8,1.5,'Economic rule:\nExpected retained value × incremental save lift × churn probability must exceed the offer cost. The data does not provide these economic inputs.',15,NAVY,True)

# Slide 8 — caveats and next steps
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'7. Decisions we can make — and what the telemetry cannot tell us','Use the findings to focus investigation, not to claim causal effects or profitability.')
add_bullets(s,.8,1.55,5.8,4.95,[
    'Prioritise understanding why the active mix shifted toward Tier 4; do not react to blended ARPDAU alone.',
    'Do not reallocate acquisition budget based only on LTV: CPI and ad revenue are absent.',
    'Use churn probabilities to design a randomized re-engagement experiment, with tenure-aware thresholds.',
    'Investigate 228 extreme currency values and the ad logging gap on Mar 6 before using those fields for product decisions.'
],14,spacing=12)
add_bullets(s,6.9,1.55,5.55,4.95,[
    'Data quality: 122 duplicate purchase IDs; 110 pre-install first-purchase dates; 45 zero-playtime days.',
    'Ad telemetry: Jan 1 partial, Mar 6 no rows, 7,732 May 1 events outside the study window.',
    'Linked-device IDs need a documented identity rule before histories are merged.',
    'Next: validate instrumentation, define unit economics, and run controlled experiments.'
],14,spacing=12)

# Appendix 9 — data quality
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix A. Data-quality audit and handling','All row counts below were rechecked against the five canonical tables.',True)
rows=[
 ['Purchase','122 repeated IDs; identical transaction fields, later timestamps','Keep earliest timestamp per purchase_id'],
 ['Refunds','228 raw negative rows; 226 after deduplication','Report separately; net = gross + deduplicated negatives'],
 ['Player profile','110 first-purchase dates 1–4 days before install','Exclude negative delays from percentile summary; disclose'],
 ['Currency spend','228 values >100,000; max 75,809,670','Flag as suspect; do not silently clip'],
 ['Rewarded ads','7,732 May 1 events; Mar 6 no rows; Jan 1 partial','Restrict to Jan–Apr; show missing day and partial day'],
 ['Player day','45 zero-playtime rows; no duplicate player-date pairs','Retain and document; no negative sessions/playtime'],
 ['Linked devices','3,211 links; one self-link','Do not merge until identity semantics are confirmed']]
add_table(s,.7,1.55,12.0,4.9,['Area','Finding','Treatment'],rows,10)

# Appendix 10 — SQL metrics
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix B. Daily health and retention outputs','Daily health uses same-day active purchasers; retention is exact-day and maturity-gated.',True)
rows=[]
for r in daily.itertuples(): rows.append([r.platform,f'{r.mean_dau:,.1f}',f'${r.mean_daily_gross_iap_usd:,.2f}',f'${r.mean_daily_arpdau:.4f}',f'{r.mean_daily_active_payer_pct:.2f}%'])
add_table(s,.7,1.5,6.0,1.55,['Platform','Mean DAU','Mean daily IAP','Mean ARPDAU','Mean active payer'],rows,9)
add_image(s,C/'retention_heatmap.png',7.0,1.5,5.5,4.8)
add_text(s,.85,3.5,5.7,1.4,'Retention denominator: all installs in the 2026 weekly cohort. D1/D7/D14/D30 are activity on exactly the milestone date. A cell is NULL unless the latest install in that cohort has complete follow-up by Apr 30.',12,GREY)

# Appendix 11 — spenders and ads
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix C. Spender behaviour and rewarded-ad engagement',None,True)
rows=[['Payers only','9.16%','47.62%','89.94%'],['All profiles','39.94%','96.66%','100.00%']]
add_table(s,.7,1.55,5.7,1.35,['Population','Top 1%','Top 10%','Top 50%'],rows,10)
add_text(s,.85,3.25,5.6,2.6,f"First purchase: all payers P25/median/P75 = {fp.iloc[0].p25_days:.0f}/{fp.iloc[0].median_days:.0f}/{fp.iloc[0].p75_days:.0f} days; 110 negative delays.\nRepeat gaps: {repeat.p25_gap_days:.1f}/{repeat.median_gap_days:.1f}/{repeat.p75_gap_days:.1f} days (P25/median/P75); {int(repeat.repeat_payers):,} repeat payers and {int(repeat.repeat_purchase_gaps):,} gaps.",13,DARK)
rows=[]
for r in adcap.itertuples(): rows.append([int(r.ad_daily_cap),f'{r.player_days_exposed_to_cap:,}',f'{r.player_days_hitting_cap:,}',f'{r.cap_hit_pct:.3f}%'])
add_table(s,6.8,1.55,5.7,1.35,['Cap','Player-day exposures','Hit cap','Hit rate'],rows,10)
add_image(s,C/'daily_ad_volume.png',6.8,3.15,5.7,3.2)
add_text(s,.85,6.25,5.6,.5,'Unique completed-ad player-days hitting any cap: 3,131 / 396,825 (0.789%).',11,TEAL,True)

# Appendix 12 — ARPDAU calculation
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix D. ARPDAU decomposition details','Positive deduplicated IAP revenue divided by player-days.',True)
rows=[]
for tier in sorted(arp_mix.country_tier.unique()):
    r=arp_mix[arp_mix.country_tier==tier].iloc[0]
    rows.append([f'Tier {tier}',f'{r.first_30d_share:.1%}',f'{r.last_30d_share:.1%}',f'${r.first_30d_arpdau:.4f}',f'${r.last_30d_arpdau:.4f}',f'{r.tier_arpdau_change_pct:+.1f}%'])
add_table(s,.7,1.5,12.0,2.4,['Tier','First mix','Last mix','First ARPDAU','Last ARPDAU','Tier change'],rows,10)
add_bullets(s,.95,4.35,11.4,1.9,[
    f"Blended ARPDAU: ${arp_period.iloc[0].blended_arpdau:.4f} → ${arp_period.iloc[1].blended_arpdau:.4f} ({summary['arpdau']['pct_change']:.1%}).",
    f"Within-tier effect = +${summary['arpdau']['within_effect']:.4f}; mix effect = ${summary['arpdau']['mix_effect']:.4f}; sum = ${summary['arpdau']['within_effect']+summary['arpdau']['mix_effect']:.4f}.",
    'Tier 4 active-player-day share rises by 28.3 percentage points; the decomposition is descriptive, not causal.'
],14,spacing=10)

# Appendix 13 — acquisition
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix E. Acquisition channel statistical results','HC3-robust OLS; organic is the reference channel. Adjusted for tier, platform and install week.',True)
rows=[]
for r in acqcoef.itertuples():
    outcome='LTV' if 'ltv' in r.outcome else 'Active days'
    model='Adjusted' if 'adjusted' in r.outcome else 'Unadjusted'
    channel='Paid social' if 'paid_social' in r.term else 'Paid video'
    rows.append([outcome,model,channel,f'{r.estimate:+.3f}',f'[{r.ci95_low:+.3f}, {r.ci95_high:+.3f}]',f'{r.p_value:.3g}'])
add_table(s,.65,1.55,12.0,3.55,['Outcome','Model','Channel vs organic','Estimate','95% CI','p-value'],rows,9)
add_text(s,.85,5.45,11.5,.9,'Interpretation: paid video’s unadjusted 30-day LTV disadvantage is large, but becomes small and statistically unresolved after adjustment. Adjusted engagement differences are statistically detectable but less than 0.3 active days over 30 days. These are observational associations, not causal channel effects.',12,GREY)

# Appendix 14 — churn model
s=prs.slides.add_slide(blank); add_bg(s); add_title(s,'Appendix F. Churn model diagnostics','Standardised logistic regression; features available on or before each snapshot.',True)
rows=[]
for r in churnseg.itertuples(): rows.append([r.tenure_bucket,f'{r.test_n:,}',f'{r.churn_rate:.1%}',f'{r.roc_auc:.3f}',f'{r.precision_at_0_5:.1%}',f'{r.recall_at_0_5:.1%}'])
add_table(s,.65,1.5,7.2,2.25,['Tenure','Test N','Churn','ROC-AUC','Precision @.5','Recall @.5'],rows,9)
add_image(s,C/'churn_precision_recall.png',8.0,1.45,4.7,3.2)
# Top coefficients by absolute magnitude
co=churncoef.reindex(churncoef.standardized_log_odds_coefficient.abs().sort_values(ascending=False).index).head(8)
rows=[[r.feature,f'{r.standardized_log_odds_coefficient:+.3f}'] for r in co.itertuples()]
add_table(s,.9,4.25,6.1,2.1,['Feature','Standardised log-odds coefficient'],rows,9)
add_text(s,7.35,4.55,5.0,1.6,'At threshold 0.50, no players in the first 30 tenure days are targeted. Tenure-aware calibration and randomized offer testing are recommended before deployment.',12,GREY)

outfile=PRES/'DBMS_Lab_EndSem_Akshay_24MAB0A03.pptx'
prs.save(outfile)
print('Saved',outfile,'slides',len(prs.slides))
