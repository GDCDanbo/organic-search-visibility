import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gambling.com Organic + AI Visibility", layout="wide")
ALL = json.loads((Path(__file__).parent / "data" / "data.json").read_text())
MKT = st.radio("Market", list(ALL["markets"]), horizontal=True)
D = ALL["markets"][MKT]
D["generated"] = ALL["generated"]
ME, DOMS, K = D["me"], D["doms"], D["K"]
ENG = {"chat_gpt": "ChatGPT", "gemini": "Gemini", "perplexity": "Perplexity"}
CTR = {1: .3, 2: .16, 3: .1, 4: .07, 5: .05, 6: .04, 7: .03, 8: .025, 9: .02, 10: .018}


def rank(k, d, i):
    return k["r"][i] if d == ME else (k["c"].get(d) or [None] * 3)[i]


def metrics(d, i):
    n = t3 = t10 = 0; s = tot = 0
    for k in K:
        r = rank(k, d, i)
        if r:
            n += 1; tot += r; t3 += r <= 3; t10 += r <= 10; s += k["v"] * CTR.get(r, 0)
    return dict(n=n, t3=t3, t10=t10, avg=tot / n if n else None, sov=s)


M = {d: (metrics(d, 0), metrics(d, 1)) for d in DOMS}
tot_sov = sum(M[d][0]["sov"] for d in DOMS) or 1
sov_pct = {d: round(100 * M[d][0]["sov"] / tot_sov, 1) for d in DOMS}
ai_rate = {b: round(100 * sum(D["stat"][e][b]["m"] for e in D["engines"]) / sum(D["n"].values())) for b in DOMS}

st.title(f"Gambling.com {MKT}: Organic + AI Visibility (casino)")
st.caption(f"Snapshot {D['generated']}. AccuRanker (Group SEO BOFU domain for the market, mobile), DataForSEO, live AI prompts.")
tabs = st.tabs(["Overview", "Keywords", "Tracked keywords", "Share of voice", "AI visibility"])

with tabs[0]:
    m, w = M[ME]
    c = st.columns(5)
    c[0].metric("Casino keywords tracked", len(K), f"{m['n']} ranking")
    c[1].metric("Top 3", m["t3"], m["t3"] - w["t3"])
    c[2].metric("Top 10", m["t10"], m["t10"] - w["t10"])
    c[3].metric("Avg rank", round(m["avg"], 1), round(m["avg"] - w["avg"], 1), delta_color="inverse")
    c[4].metric("AI mention rate", f"{ai_rate[ME]}%")
    st.subheader("Visibility trend, 30 days (volume x CTR)")
    tr = pd.DataFrame({d: {x[0]: x[2] for x in v} for d, v in D["trend"].items()})
    st.line_chart(tr)
    st.caption("casino.org has no daily history (not in AccuRanker's competitor set).")
    a, b = st.columns(2)
    a.subheader("Google SoV %"); a.bar_chart(pd.Series(sov_pct))
    b.subheader("AI mention rate %"); b.bar_chart(pd.Series(ai_rate))

with tabs[1]:
    st.caption("DataForSEO top-10 keywords on the market root and /online-casinos/ URLs only.")
    df = pd.DataFrame(D["kw"], columns=["Keyword", "Pos", "Volume", "CPC", "KD", "Intent", "URL", "Est. traffic"])
    c = st.columns(4)
    inc = c[0].text_input("Include words (comma separated)")
    exc = c[1].text_input("Exclude words")
    mp = c[2].selectbox("Position", [10, 3], format_func=lambda x: f"Top {x}")
    it = c[3].selectbox("Intent", ["All"] + sorted(df["Intent"].dropna().unique()))
    f = df[df["Pos"] <= mp]
    if it != "All": f = f[f["Intent"] == it]
    iw = [x.strip().lower() for x in inc.split(",") if x.strip()]
    ew = [x.strip().lower() for x in exc.split(",") if x.strip()]
    if iw: f = f[f["Keyword"].str.lower().apply(lambda s: any(x in s for x in iw))]
    if ew: f = f[~f["Keyword"].str.lower().apply(lambda s: any(x in s for x in ew))]
    c = st.columns(3)
    c[0].metric("Keywords", f"{len(f):,}"); c[1].metric("Volume", f"{int(f['Volume'].sum()):,}"); c[2].metric("Est. traffic", f"{int(f['Est. traffic'].sum()):,}")
    st.dataframe(f.sort_values("Est. traffic", ascending=False), width="stretch", hide_index=True)

with tabs[2]:
    st.subheader("Top casino competitors (ranked by visibility on tracked casino keywords)")
    order = sorted(DOMS, key=lambda d: -M[d][0]["sov"])
    rows = []
    for i, d in enumerate(order, 1):
        m, w = M[d]
        rows.append({"#": i, "Domain": d + ("*" if d == "casino.org" else ""), "Visibility": round(m["sov"]),
                     "7d change": round(m["sov"] - w["sov"]) if (d == ME or d in D["trend"]) else None,
                     "Top 3": m["t3"], "Top 10": m["t10"], "Avg rank": round(m["avg"], 1) if m["avg"] else None,
                     "Kws ahead of gambling.com": sum(1 for k in K if (a := rank(k, d, 0)) and (not k["r"][0] or a < k["r"][0]))})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("*casino.org is not in AccuRanker's competitor set for this domain: its rank is a live Google UK mobile check (top 30 only), not like-for-like. "
               "AccuRanker and live SERPs can disagree on the same keyword.")
    st.subheader("Winning and losing keywords")
    c = st.columns(2)
    sel = c[0].selectbox("Domain", [d for d in order if d == ME or d in D["trend"]], index=0)
    span = c[1].selectbox("Compare", ["7 days ago", "30 days ago"])
    i = 1 if span.startswith("7") else 2
    mv = []
    for k in K:
        a, b = rank(k, sel, 0), rank(k, sel, i)
        if not a and not b: continue
        ch = (b or 101) - (a or 101)
        if ch: mv.append({"Keyword": k["k"], "Volume": k["v"], "Was": str(b or ">100"), "Now": str(a or ">100"), "Move": ch})
    mdf = pd.DataFrame(mv)
    a, b = st.columns(2)
    if len(mdf):
        a.markdown("**Top 10 winners**"); a.dataframe(mdf[mdf.Move > 0].sort_values(["Move", "Volume"], ascending=False).head(10), hide_index=True, width="stretch")
        b.markdown("**Top 10 losers**"); b.dataframe(mdf[mdf.Move < 0].sort_values(["Move", "Volume"], ascending=[True, False]).head(10), hide_index=True, width="stretch")
    st.subheader(f'Top 50 "{MKT} Casino" keywords (by volume)')
    t50 = []
    for k in sorted([k for k in K if k["t"] == f"{MKT} Casino"], key=lambda k: -k["v"])[:50]:
        r = {"Keyword": k["k"], "Volume": k["v"], "Gambling.com": k["r"][0],
             "7d": (k["r"][1] - k["r"][0]) if k["r"][0] and k["r"][1] else None, "URL": k["lp"]}
        for d in DOMS[1:]: r[d] = rank(k, d, 0)
        t50.append(r)
    st.dataframe(pd.DataFrame(t50), hide_index=True, width="stretch")
    st.caption("Google UK mobile. Empty = not ranking.")

with tabs[3]:
    a, b = st.columns(2)
    a.subheader("Casino share of voice %"); a.bar_chart(pd.Series(sov_pct))
    b.subheader(f"Most often in top 10 ({D['nserp']} casino keywords, live SERP)"); b.bar_chart(pd.Series(dict(D["riv"])))
    st.subheader("Keyword gaps: a named competitor in top 5, gambling.com outside top 10")
    gaps = []
    for k in K:
        if k["r"][0] and k["r"][0] <= 10: continue
        who = [f"{d} #{rank(k, d, 0)}" for d in DOMS[1:] if (rank(k, d, 0) or 99) <= 5]
        if who: gaps.append({"Keyword": k["k"], "Volume": k["v"], "Who ranks top 5": ", ".join(who), "Gambling.com": k["r"][0]})
    st.dataframe(pd.DataFrame(gaps).sort_values("Volume", ascending=False).head(60), hide_index=True, width="stretch")

with tabs[4]:
    c = st.columns(3)
    for col, e in zip(c, D["engines"]):
        s, n = D["stat"][e][ME], D["n"][e]
        col.metric(f"{ENG[e]}: mention / citation", f"{round(100*s['m']/n)}% / {round(100*s['c']/n)}%", f"avg pos {s['avgpos']}", delta_color="off")
    for title, key in [("Mention rate by engine", "m"), ("Citation rate (linked as source)", "c")]:
        st.subheader(title)
        st.dataframe(pd.DataFrame({ENG[e]: {b: round(100 * D["stat"][e][b][key] / D["n"][e]) for b in DOMS} for e in D["engines"]}).style.format("{}%").background_gradient(cmap="Blues"), width="stretch")
    st.subheader("Most cited sources"); st.bar_chart(pd.Series(dict(D["src"])))
    st.subheader("Prompt tracker")
    st.dataframe(pd.DataFrame([{"Prompt": p["p"], "Engine": ENG[p["e"]], "Mentioned": ", ".join(p["ment"]), "Cited": ", ".join(p["cit"])} for p in D["pp"]]), hide_index=True, width="stretch")
    st.caption("25 prompts x 3 engines, run once. Gemini citations are redirect URLs so its citation rate reads 0%. AI Overviews excluded (suppressed for UK gambling queries).")
