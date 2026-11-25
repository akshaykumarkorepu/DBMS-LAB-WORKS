#!/usr/bin/env python3
"""Reproducible analysis pipeline for Akshay kumar korepu's DBMS Lab End-Sem project."""
from pathlib import Path
import json, sqlite3, math, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (roc_auc_score, average_precision_score,
    precision_score, recall_score, f1_score, precision_recall_curve)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
TABLES = OUT / "tables"
CHARTS = OUT / "charts"
for d in (TABLES, CHARTS): d.mkdir(parents=True, exist_ok=True)
CUTOFF = pd.Timestamp("2026-04-30")


def read_inputs():
    pp = pd.read_csv(DATA / "player_profile.csv", dtype={"device_id": str, "original_device_id": str})
    pd_day = pd.read_csv(DATA / "player_day.csv", dtype={"device_id": str})
    pur = pd.read_csv(DATA / "purchase.csv", dtype={"purchase_id": str, "device_id": str})
    cs = pd.read_csv(DATA / "currency_spend.csv", dtype={"device_id": str})
    ad = pd.read_csv(DATA / "ad_view.csv", dtype={"device_id": str})
    pp["install_date"] = pd.to_datetime(pp["install_date"], errors="coerce")
    pp["first_purchase_date"] = pd.to_datetime(pp["first_purchase_date"], errors="coerce")
    pd_day["activity_date"] = pd.to_datetime(pd_day["activity_date"].astype(str), format="%Y%m%d", errors="coerce")
    pur["event_ts"] = pd.to_datetime(pur["event_ts"], errors="coerce")
    cs["event_ts"] = pd.to_datetime(cs["event_ts"], errors="coerce")
    ad["event_ts"] = pd.to_datetime(ad["event_ts"], errors="coerce")
    return pp, pd_day, pur, cs, ad


def execute_sql(pp, pd_day, pur, cs, ad):
    """Load source tables into SQLite and run every statement in Deliverable 1 SQL."""
    db_path = OUT / "dbms_lab.sqlite"
    if db_path.exists(): db_path.unlink()
    conn = sqlite3.connect(db_path)
    frames = {
        "player_profile": pp.copy(), "player_day": pd_day.copy(),
        "purchase": pur.copy(), "currency_spend": cs.copy(), "ad_view": ad.copy()
    }
    for name, df in frames.items():
        if name == "player_day":
            df["activity_date"] = pd.to_datetime(df["activity_date"]).dt.strftime("%Y%m%d").astype(int)
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime("%Y-%m-%d %H:%M:%S")
        df.to_sql(name, conn, index=False, if_exists="replace", chunksize=50000)
    conn.execute("CREATE INDEX idx_pd_device_date ON player_day(device_id, activity_date)")
    conn.execute("CREATE INDEX idx_purchase_id ON purchase(purchase_id)")
    sql = (ROOT / "sql" / "deliverable_1_queries.sql").read_text(encoding="utf-8")
    sql = "\n".join(line.split("--")[0] for line in sql.splitlines())
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    names = ["daily_health_by_platform", "weekly_retention", "revenue_concentration",
             "time_to_first_purchase", "repeat_purchase_gaps", "ad_cap_by_cap",
             "ad_cap_unique", "daily_ad_volume"]
    results = {}
    for name, statement in zip(names, statements):
        results[name] = pd.read_sql_query(statement, conn)
        results[name].to_csv(TABLES / f"{name}.csv", index=False)
    conn.close()
    return results


def run_arpdau(pp, pd_day, pur):
    # Deterministic deduplication: earliest timestamp for each transaction ID.
    dedup = pur.sort_values(["event_ts", "purchase_id"]).drop_duplicates("purchase_id", keep="first").copy()
    dedup["date"] = dedup["event_ts"].dt.normalize()
    pd_m = pd_day.merge(pp[["device_id", "country_tier"]], on="device_id", how="inner")
    pd_m["date"] = pd_m["activity_date"].dt.normalize()
    pur_m = dedup[(dedup.usd_amount > 0)].merge(pp[["device_id", "country_tier"]], on="device_id", how="inner")
    pur_m["date"] = pur_m["event_ts"].dt.normalize()
    p1_pd = pd_m[pd_m.date.between("2026-01-01", "2026-01-30")]
    p2_pd = pd_m[pd_m.date.between("2026-04-01", "2026-04-30")]
    p1_pur = pur_m[pur_m.date.between("2026-01-01", "2026-01-30")]
    p2_pur = pur_m[pur_m.date.between("2026-04-01", "2026-04-30")]
    rows=[]
    for label, act, rev in [("first_30d",p1_pd,p1_pur),("last_30d",p2_pd,p2_pur)]:
        den=act.groupby("country_tier").size()
        num=rev.groupby("country_tier").usd_amount.sum()
        for tier in sorted(pp.country_tier.dropna().unique()):
            d=int(den.get(tier,0)); r=float(num.get(tier,0.0))
            rows.append([label,int(tier),d,r,r/d if d else np.nan])
    tier=pd.DataFrame(rows,columns=["period","country_tier","player_days","gross_iap_usd","arpdau"])
    a=tier[tier.period=="first_30d"].set_index("country_tier")
    b=tier[tier.period=="last_30d"].set_index("country_tier")
    s1=a.player_days/a.player_days.sum(); s2=b.player_days/b.player_days.sum()
    within=float((s2*(b.arpdau-a.arpdau)).sum())
    mix=float(((s2-s1)*a.arpdau).sum())
    ar1=float(a.gross_iap_usd.sum()/a.player_days.sum())
    ar2=float(b.gross_iap_usd.sum()/b.player_days.sum())
    decomp=pd.DataFrame([
        ["first_30d",int(a.player_days.sum()),float(a.gross_iap_usd.sum()),ar1],
        ["last_30d",int(b.player_days.sum()),float(b.gross_iap_usd.sum()),ar2]
    ],columns=["period","player_days","gross_iap_usd","blended_arpdau"])
    tier.to_csv(TABLES/"arpdau_by_country_tier.csv",index=False)
    decomp.to_csv(TABLES/"arpdau_period_summary.csv",index=False)
    mixdf=pd.DataFrame({"first_30d_share":s1,"last_30d_share":s2,
                        "mix_change_percentage_points":(s2-s1)*100,
                        "first_30d_arpdau":a.arpdau,"last_30d_arpdau":b.arpdau,
                        "tier_arpdau_change_pct":(b.arpdau/a.arpdau-1)*100}).reset_index()
    mixdf.to_csv(TABLES/"arpdau_mix_decomposition.csv",index=False)
    return {"tier":tier,"decomp":decomp,"mix":mixdf,"within_effect":within,
            "mix_effect":mix,"total_change":ar2-ar1,"pct_change":ar2/ar1-1}


def run_acquisition(pp, pd_day, pur):
    dedup=pur.sort_values(["event_ts","purchase_id"]).drop_duplicates("purchase_id",keep="first")
    ch=pp[pp.install_date.between("2026-01-01","2026-03-31")].copy()
    ch["inst_week"]=ch.install_date.dt.to_period("W-SUN").astype(str)
    act=pd_day.merge(ch[["device_id","install_date"]],on="device_id",how="inner")
    act=act[(act.activity_date>=act.install_date)&(act.activity_date<act.install_date+pd.Timedelta(days=30))]
    eng=act.groupby("device_id").size().rename("active_days_30")
    rev=dedup[dedup.usd_amount>0].merge(ch[["device_id","install_date"]],on="device_id",how="inner")
    rev=rev[(rev.event_ts.dt.normalize()>=rev.install_date)&
            (rev.event_ts.dt.normalize()<rev.install_date+pd.Timedelta(days=30))]
    ltv=rev.groupby("device_id").usd_amount.sum().rename("ltv_30")
    df=ch.set_index("device_id").join(eng).join(ltv).reset_index()
    df[["active_days_30","ltv_30"]]=df[["active_days_30","ltv_30"]].fillna(0)
    df["acquisition_channel"]=pd.Categorical(df.acquisition_channel,
        categories=["organic","paid_social","paid_video"])
    summary=df.groupby("acquisition_channel",observed=True).agg(
        installs=("device_id","size"),mean_active_days_30=("active_days_30","mean"),
        median_active_days_30=("active_days_30","median"),mean_gross_iap_ltv_30=("ltv_30","mean"),
        median_gross_iap_ltv_30=("ltv_30","median"),payer_share=("ltv_30",lambda x:(x>0).mean())
    ).reset_index()
    summary.to_csv(TABLES/"acquisition_channel_summary.csv",index=False)
    models={}
    coef=[]
    for outcome in ["ltv_30","active_days_30"]:
        m0=smf.ols(f"{outcome} ~ C(acquisition_channel, Treatment('organic'))",data=df).fit(cov_type="HC3")
        m1=smf.ols(f"{outcome} ~ C(acquisition_channel, Treatment('organic')) + C(country_tier) + C(platform) + C(inst_week)",data=df).fit(cov_type="HC3")
        models[outcome]=(m0,m1)
        for label,m in [(outcome+"_unadjusted",m0),(outcome+"_adjusted",m1)]:
            for term in m.params.index:
                if "acquisition_channel" in term:
                    lo,hi=m.conf_int().loc[term]
                    coef.append([label,term,float(m.params[term]),float(lo),float(hi),float(m.pvalues[term])])
    coefdf=pd.DataFrame(coef,columns=["outcome","term","estimate","ci95_low","ci95_high","p_value"])
    coefdf.to_csv(TABLES/"acquisition_channel_regression.csv",index=False)
    df.to_csv(TABLES/"acquisition_player_level_30d.csv",index=False)
    return {"player_level":df,"summary":summary,"coefficients":coefdf,"models":models}


def build_churn_features(snapshot, pp, pd_day, pur, cs, ad):
    T=pd.Timestamp(snapshot); m7=T-pd.Timedelta(days=6); m14=T-pd.Timedelta(days=13)
    act7=pd_day[pd_day.activity_date.between(m7,T)]
    elig=pp[(pp.install_date<=T-pd.Timedelta(days=1)) & pp.device_id.isin(act7.device_id)].copy()
    future=set(pd_day[pd_day.activity_date.between(T+pd.Timedelta(days=1),T+pd.Timedelta(days=14))].device_id)
    elig["churned"]=(~elig.device_id.isin(future)).astype(int)
    elig["tenure_days"]=(T-elig.install_date).dt.days
    h14=pd_day[pd_day.activity_date.between(m14,T)]
    agg=h14.groupby("device_id").agg(active_days_14d=("activity_date","count"),
        sessions_14d=("session_count","sum"),playtime_14d=("playtime_minutes","sum"),
        max_level=("player_level","max"),last_dt=("activity_date","max")).reset_index()
    agg["recency_days"]=(T-agg.last_dt).dt.days
    s7=pd_day[pd_day.activity_date.between(m7,T)].groupby("device_id").session_count.sum().rename("sess_w2")
    s_prev=pd_day[(pd_day.activity_date>=m14)&(pd_day.activity_date<m7)].groupby("device_id").session_count.sum().rename("sess_w1")
    dedup=pur.sort_values(["event_ts","purchase_id"]).drop_duplicates("purchase_id",keep="first")
    ph=dedup[(dedup.usd_amount>0)&(dedup.event_ts<=T+pd.Timedelta(days=1)-pd.Timedelta(seconds=1))].groupby("device_id").agg(
        cum_spend=("usd_amount","sum"),purch_count=("usd_amount","count")).reset_index()
    a14=ad[(ad.event_ts.dt.normalize().between(m14,T))&(ad.status=="completed")].groupby("device_id").size().rename("ads_14d")
    c14=cs[cs.event_ts.dt.normalize().between(m14,T)].groupby("device_id").size().rename("spend_events_14d")
    out=elig.merge(agg.drop(columns="last_dt"),on="device_id",how="left")
    out=out.merge(s7,on="device_id",how="left").merge(s_prev,on="device_id",how="left")
    out=out.merge(ph,on="device_id",how="left").merge(a14,on="device_id",how="left").merge(c14,on="device_id",how="left")
    for c in ["sess_w2","sess_w1","cum_spend","purch_count","ads_14d","spend_events_14d"]: out[c]=out[c].fillna(0)
    out["sess_delta"]=out.sess_w2-out.sess_w1
    out["is_payer"]=(out.cum_spend>0).astype(int)
    out["log_spend"]=np.log1p(out.cum_spend)
    out["log_tenure"]=np.log1p(out.tenure_days)
    out["snapshot"]=T.strftime("%Y-%m-%d")
    return out


def run_churn(pp,pd_day,pur,cs,ad):
    train=build_churn_features("2026-03-31",pp,pd_day,pur,cs,ad)
    test=build_churn_features("2026-04-15",pp,pd_day,pur,cs,ad)
    num=["log_tenure","active_days_14d","sessions_14d","playtime_14d","max_level","recency_days",
         "sess_delta","log_spend","purch_count","is_payer","ads_14d","spend_events_14d"]
    cat=["platform","country_tier","acquisition_channel"]
    Xtr=pd.get_dummies(train[num+cat],columns=cat,drop_first=True,dtype=float)
    Xte=pd.get_dummies(test[num+cat],columns=cat,drop_first=True,dtype=float).reindex(columns=Xtr.columns,fill_value=0)
    model=Pipeline([("scaler",StandardScaler()),("lr",LogisticRegression(max_iter=1000,C=1.0,random_state=42))])
    model.fit(Xtr,train.churned)
    probs=model.predict_proba(Xte)[:,1]
    roc=float(roc_auc_score(test.churned,probs)); ap=float(average_precision_score(test.churned,probs))
    test=test.copy(); test["churn_probability"]=probs
    test[["device_id","snapshot","tenure_days","churned","churn_probability"]].to_csv(TABLES/"churn_test_predictions.csv",index=False)
    thresholds=[]
    for th in [.35,.45,.50,.55]:
        pred=(probs>=th).astype(int)
        thresholds.append([th,int(pred.sum()),float(precision_score(test.churned,pred,zero_division=0)),
                           float(recall_score(test.churned,pred)),float(f1_score(test.churned,pred))])
    thdf=pd.DataFrame(thresholds,columns=["threshold","targeted_players","precision","recall","f1"])
    thdf.to_csv(TABLES/"churn_threshold_metrics.csv",index=False)
    test["tenure_bucket"]=pd.cut(test.tenure_days,bins=[0,7,30,90,np.inf],labels=["1-7 days","8-30 days","31-90 days","90+ days"],include_lowest=True)
    seg=[]
    for bucket,g in test.groupby("tenure_bucket",observed=False):
        y=g.churned.values; pr=g.churn_probability.values; pred=(pr>=.5).astype(int)
        seg.append([str(bucket),len(g),float(y.mean()),float(roc_auc_score(y,pr)) if len(np.unique(y))>1 else np.nan,
                    float(precision_score(y,pred,zero_division=0)),float(recall_score(y,pred)),int(pred.sum())])
    segdf=pd.DataFrame(seg,columns=["tenure_bucket","test_n","churn_rate","roc_auc","precision_at_0_5","recall_at_0_5","predicted_at_0_5"])
    segdf.to_csv(TABLES/"churn_tenure_diagnostics.csv",index=False)
    pd.DataFrame([{"snapshot":"2026-03-31","n":len(train),"churn_rate":train.churned.mean()},
                  {"snapshot":"2026-04-15","n":len(test),"churn_rate":test.churned.mean(),"roc_auc":roc,"pr_auc":ap}]).to_csv(TABLES/"churn_snapshot_summary.csv",index=False)
    # Standardized coefficients from the fitted logistic regression.
    coefs=pd.DataFrame({"feature":Xtr.columns,"standardized_log_odds_coefficient":model.named_steps["lr"].coef_[0]})
    coefs.to_csv(TABLES/"churn_model_coefficients.csv",index=False)
    return {"train":train,"test":test,"model":model,"roc_auc":roc,"pr_auc":ap,"thresholds":thdf,"segments":segdf}


def make_charts(arp,acq,churn,sql_results,ad):
    # ARPDAU by tier
    t=arp["tier"]
    a=t[t.period=="first_30d"].set_index("country_tier").arpdau
    b=t[t.period=="last_30d"].set_index("country_tier").arpdau
    x=np.arange(len(a)); w=.36
    fig,ax=plt.subplots(figsize=(8.5,4.8)); ax.bar(x-w/2,a.values,w,label="First 30 days"); ax.bar(x+w/2,b.values,w,label="Last 30 days")
    ax.set_xticks(x,[f"Tier {i}" for i in a.index]); ax.set_ylabel("Gross IAP ARPDAU (USD)"); ax.set_title("ARPDAU improves within every country tier"); ax.legend(); fig.tight_layout(); fig.savefig(CHARTS/"arpdau_by_tier.png",dpi=180); plt.close(fig)
    # DAU mix
    mix=arp["mix"].set_index("country_tier")[["first_30d_share","last_30d_share"]]
    fig,ax=plt.subplots(figsize=(8,4.8)); mix.T.plot(kind="bar",stacked=True,ax=ax); ax.set_ylabel("Share of active player-days"); ax.set_title("Active player-day mix shifts toward Tier 4"); ax.legend(title="Country tier",ncol=4,loc="upper center",bbox_to_anchor=(.5,-.15)); fig.tight_layout(); fig.savefig(CHARTS/"dau_mix_shift.png",dpi=180,bbox_inches="tight"); plt.close(fig)
    # Daily ad events
    d=sql_results["daily_ad_volume"].copy(); d["dt"]=pd.to_datetime(d.dt)
    fig,ax=plt.subplots(figsize=(10.5,4.8)); ax.plot(d.dt,d.completed_ads,label="Completed"); ax.plot(d.dt,d.started_ads+d.abandoned_ads,label="Started + abandoned",linestyle="--")
    ax.set_ylabel("Daily events"); ax.set_title("Rewarded-ad events by day (Jan 1–Apr 30, 2026)"); ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d")); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(CHARTS/"daily_ad_volume.png",dpi=180); plt.close(fig)
    # Acquisition adjusted/unadjusted LTV coefficients
    cf=acq["coefficients"]; cf=cf[cf.outcome.isin(["ltv_30_unadjusted","ltv_30_adjusted"])].copy()
    fig,ax=plt.subplots(figsize=(8.2,4.5)); labels=[]
    for i,r in enumerate(cf.itertuples()):
        labels.append(("Unadjusted " if "unadjusted" in r.outcome else "Adjusted ")+ ("Paid social" if "paid_social" in r.term else "Paid video"))
        ax.errorbar(r.estimate,i,xerr=[[r.estimate-r.ci95_low],[r.ci95_high-r.estimate]],fmt="o",capsize=4)
    ax.axvline(0,linestyle="--"); ax.set_yticks(range(len(labels)),labels); ax.set_xlabel("30-day gross IAP revenue difference vs organic (USD)"); ax.set_title("Paid-video LTV gap shrinks after adjustment"); fig.tight_layout(); fig.savefig(CHARTS/"acquisition_ltv_coefficients.png",dpi=180); plt.close(fig)
    # Churn PR curve
    p,r,ths=precision_recall_curve(churn["test"].churned,churn["test"].churn_probability)
    fig,ax=plt.subplots(figsize=(7.2,4.8)); ax.plot(r,p,label=f"Logistic regression (AP={churn['pr_auc']:.3f})"); ax.axhline(churn["test"].churned.mean(),linestyle="--",label=f"Prevalence baseline ({churn['test'].churned.mean():.1%})")
    for th in [.35,.45,.55]:
        idx=int(np.argmin(np.abs(ths-th))); ax.scatter(r[idx],p[idx],label=f"Threshold≈{ths[idx]:.2f}")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_title("14-day churn model: precision–recall trade-off"); ax.legend(); fig.tight_layout(); fig.savefig(CHARTS/"churn_precision_recall.png",dpi=180); plt.close(fig)
    # Retention heatmap
    ret=sql_results["weekly_retention"].copy(); vals=ret[["d1_pct","d7_pct","d14_pct","d30_pct"]].to_numpy(dtype=float)
    fig,ax=plt.subplots(figsize=(8,5.8)); im=ax.imshow(vals,aspect="auto"); ax.set_xticks(range(4),["D1","D7","D14","D30"]); ax.set_yticks(range(len(ret)),pd.to_datetime(ret.install_week).dt.strftime("%b %d")); ax.set_title("Weekly install-cohort retention")
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            if np.isfinite(vals[i,j]): ax.text(j,i,f"{vals[i,j]:.1f}%",ha="center",va="center")
    fig.colorbar(im,ax=ax,label="Retention (%)"); fig.tight_layout(); fig.savefig(CHARTS/"retention_heatmap.png",dpi=180); plt.close(fig)


def main():
    pp,pd_day,pur,cs,ad=read_inputs()
    # Basic schema checks
    assert len(pp)==80295 and pp.device_id.nunique()==80295, "Unexpected profile table shape/uniqueness"
    assert len(pd_day)==667435 and pd_day.duplicated(["device_id","activity_date"]).sum()==0, "Unexpected player_day structure"
    assert len(pur)==15426 and pur.purchase_id.nunique()==15304, "Unexpected raw purchase structure"
    sql=execute_sql(pp,pd_day,pur,cs,ad)
    # Additional summary tables derived from the SQL result sets.
    dh=sql["daily_health_by_platform"].copy()
    dh_summary=dh.groupby("platform").agg(
        mean_dau=("dau","mean"), mean_daily_gross_iap_usd=("gross_iap_usd","mean"),
        mean_daily_arpdau=("arpdau","mean"), mean_daily_active_payer_pct=("active_payer_pct","mean"),
        total_dau_player_days=("dau","sum"), total_gross_iap_usd=("gross_iap_usd","sum"),
        total_active_payers=("active_payers","sum")
    ).reset_index()
    dh_summary["weighted_active_payer_pct"] = 100*dh_summary.total_active_payers/dh_summary.total_dau_player_days
    dh_summary["aggregate_arpdau"] = dh_summary.total_gross_iap_usd/dh_summary.total_dau_player_days
    dh_summary.to_csv(TABLES/"daily_health_platform_summary.csv",index=False)

    fp=sql["time_to_first_purchase"].copy()
    fp["days_to_first_purchase"]=pd.to_numeric(fp["days_to_first_purchase"],errors="coerce")
    def delay_summary(label, frame):
        v=frame.days_to_first_purchase.dropna()
        v=v[v>=0]
        return [label,len(frame),int(frame.days_to_first_purchase.notna().sum()),
                int((frame.days_to_first_purchase<0).sum()),int((frame.days_to_first_purchase.isna()).sum()),
                float(v.quantile(.25)) if len(v) else np.nan,float(v.median()) if len(v) else np.nan,
                float(v.quantile(.75)) if len(v) else np.nan,float(v.mean()) if len(v) else np.nan]
    fp_summary=pd.DataFrame([delay_summary("all_installs",fp),
        delay_summary("2026_installs",fp[fp.install_date >= "2026-01-01"] )],
        columns=["population","players","ever_paid","negative_delay_records","never_paid","p25_days","median_days","p75_days","mean_days"])
    fp_summary.to_csv(TABLES/"first_purchase_delay_summary.csv",index=False)

    gaps=sql["repeat_purchase_gaps"].copy()
    gaps["gap_days"]=pd.to_numeric(gaps["gap_days"],errors="coerce")
    gs=gaps.gap_days.dropna()
    pd.DataFrame([{"repeat_payers":gaps.device_id.nunique(),"repeat_purchase_gaps":len(gs),
        "p25_gap_days":gs.quantile(.25),"median_gap_days":gs.median(),"p75_gap_days":gs.quantile(.75),"mean_gap_days":gs.mean()}]).to_csv(TABLES/"repeat_purchase_gap_summary.csv",index=False)

    dedup_purchase=pur.sort_values(["event_ts","purchase_id"]).drop_duplicates("purchase_id",keep="first").copy()
    dedup_purchase.to_csv(TABLES/"purchase_deduplicated.csv",index=False)
    pd.DataFrame([{"raw_rows":len(pur),"unique_purchase_ids":pur.purchase_id.nunique(),
        "duplicate_rows":int(pur.duplicated("purchase_id").sum()),
        "dedup_gross_positive_usd":dedup_purchase.loc[dedup_purchase.usd_amount>0,"usd_amount"].sum(),
        "dedup_negative_usd":dedup_purchase.loc[dedup_purchase.usd_amount<0,"usd_amount"].sum(),
        "dedup_net_usd":dedup_purchase.usd_amount.sum()}]).to_csv(TABLES/"purchase_reconciliation.csv",index=False)
    ad_in=ad[ad.event_ts.dt.date<=CUTOFF.date()]
    pd.DataFrame([{"window_rows":len(ad_in),"completed":int((ad_in.status=="completed").sum()),
        "started":int((ad_in.status=="started").sum()),"abandoned":int((ad_in.status=="abandoned").sum()),
        "out_of_window_may1_rows":int((ad.event_ts.dt.date> CUTOFF.date()).sum()),
        "march6_rows":int((ad_in.event_ts.dt.date==pd.Timestamp("2026-03-06").date()).sum())}]).to_csv(TABLES/"ad_status_summary.csv",index=False)
    arp=run_arpdau(pp,pd_day,pur)
    acq=run_acquisition(pp,pd_day,pur)
    churn=run_churn(pp,pd_day,pur,cs,ad)
    make_charts(arp,acq,churn,sql,ad)
    summary={
      "student":"Akshay kumar korepu","roll_number":"24MAB0A03","institution":"National Institute of Technology Warangal",
      "course":"DBMS Lab","instructor":"Dr. Vikas Srivastava",
      "rows":{"player_profile":len(pp),"player_day":len(pd_day),"purchase_raw":len(pur),"purchase_deduplicated":pur.purchase_id.nunique(),"currency_spend":len(cs),"ad_view":len(ad)},
      "purchase":{"gross_positive_usd":float(pur.sort_values("event_ts").drop_duplicates("purchase_id").query("usd_amount > 0").usd_amount.sum()),
                  "negative_usd":float(pur.sort_values("event_ts").drop_duplicates("purchase_id").query("usd_amount < 0").usd_amount.sum()),
                  "net_usd":float(pur.sort_values("event_ts").drop_duplicates("purchase_id").usd_amount.sum())},
      "arpdau":{"first_30d":float(arp["decomp"].iloc[0].blended_arpdau),"last_30d":float(arp["decomp"].iloc[1].blended_arpdau),
                 "pct_change":float(arp["pct_change"]),"within_effect":arp["within_effect"],"mix_effect":arp["mix_effect"]},
      "acquisition":{"n":len(acq["player_level"]),"adjusted_paid_video_ltv_difference":float(acq["coefficients"].query("outcome == 'ltv_30_adjusted' and term.str.contains('paid_video')",engine="python").estimate.iloc[0]),
                      "adjusted_paid_video_ltv_p_value":float(acq["coefficients"].query("outcome == 'ltv_30_adjusted' and term.str.contains('paid_video')",engine="python").p_value.iloc[0])},
      "churn":{"train_n":len(churn["train"]),"test_n":len(churn["test"]),"test_churn_rate":float(churn["test"].churned.mean()),"roc_auc":churn["roc_auc"],"pr_auc":churn["pr_auc"]}
    }
    (OUT/"analysis_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    warnings.filterwarnings("ignore",category=FutureWarning)
    main()
