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
tabs = st.tabs(["Overview", "Keywords", "Tracked keywords", "Share of voice", "AI visibility", "Insights"])

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
        st.dataframe(pd.DataFrame({ENG[e]: {b: round(100 * D["stat"][e][b][key] / D["n"][e]) for b in DOMS} for e in D["engines"]}).style.format("{}%"), width="stretch")
    st.subheader("Most cited sources"); st.bar_chart(pd.Series(dict(D["src"])))
    st.subheader("Prompt tracker")
    st.dataframe(pd.DataFrame([{"Prompt": p["p"], "Engine": ENG[p["e"]], "Mentioned": ", ".join(p["ment"]), "Cited": ", ".join(p["cit"])} for p in D["pp"]]), hide_index=True, width="stretch")
    st.caption("25 prompts x 3 engines, run once. Gemini citations are redirect URLs so its citation rate reads 0%. AI Overviews excluded (suppressed for UK gambling queries).")

with tabs[5]:
    m, w = M[ME]
    order_v = sorted(DOMS, key=lambda d: -M[d][0]["sov"])
    pos = order_v.index(ME) + 1
    leader = order_v[0] if order_v[0] != ME else order_v[1]
    ahead = {d: sum(1 for k in K if (a := rank(k, d, 0)) and (not k["r"][0] or a < k["r"][0])) for d in DOMS if d != ME}
    worst = max(ahead, key=ahead.get)
    up = sum(1 for k in K if k["r"][0] and k["r"][1] and k["r"][0] < k["r"][1])
    dn = sum(1 for k in K if k["r"][0] and k["r"][1] and k["r"][0] > k["r"][1])
    unr = sum(1 for k in K if not k["r"][0])
    near = sorted([k for k in K if k["r"][0] and 4 <= k["r"][0] <= 20], key=lambda k: -k["v"])
    ai_best = max((d for d in DOMS if d != ME), key=lambda d: ai_rate[d])
    st.subheader(f"Key takeaways: {MKT} casino")
    st.markdown(
        f"- **Organic position:** gambling.com ranks {pos} of {len(DOMS)} on Google visibility for tracked casino keywords (share of voice {sov_pct[ME]}%). "
        f"{leader} is ahead on {sov_pct[leader]}%.\n"
        f"- **Rankings:** {m['t3']} keywords in the top 3 and {m['t10']} in the top 10 out of {len(K)} tracked; average rank {round(m['avg'], 1)}. "
        f"Over 7 days {up} keywords improved and {dn} dropped; {unr} are not ranking in the top 100.\n"
        f"- **Toughest competitor:** {worst} outranks gambling.com on {ahead[worst]} tracked keywords.\n"
        f"- **AI visibility:** gambling.com is mentioned in {ai_rate[ME]}% of AI answers across ChatGPT, Gemini and Perplexity. "
        f"The best competitor, {ai_best}, is at {ai_rate[ai_best]}%.")
    st.subheader("Biggest opportunities: ranking 4-20, highest volume")
    st.dataframe(pd.DataFrame([{"Keyword": k["k"], "Volume": k["v"], "Rank": k["r"][0], "URL": k["lp"],
                                "Best competitor": min(((rank(k, d, 0), d) for d in DOMS[1:] if rank(k, d, 0)), default=(None, ""))[1]}
                               for k in near[:15]]), hide_index=True, width="stretch")
    st.subheader("Where competitors beat us on volume")
    beat = sorted([k for k in K if not k["r"][0] or k["r"][0] > 10], key=lambda k: -k["v"])
    rows = []
    for k in beat:
        who = sorted((rank(k, d, 0), d) for d in DOMS[1:] if rank(k, d, 0) and rank(k, d, 0) <= 5)
        if who: rows.append({"Keyword": k["k"], "Volume": k["v"], "Gambling.com": k["r"][0], "Leading": ", ".join(f"{d} #{r}" for r, d in who[:3])})
    st.dataframe(pd.DataFrame(rows[:15]), hide_index=True, width="stretch")
    st.subheader("AI prompts where a competitor is named and gambling.com is not")
    miss = [{"Prompt": p["p"], "Engine": ENG[p["e"]], "Named instead": ", ".join(p["ment"][:4])} for p in D["pp"] if ME not in p["ment"] and p["ment"]]
    st.dataframe(pd.DataFrame(miss[:20]), hide_index=True, width="stretch")
    st.subheader("What competitors do well that gambling.com does not")
    cmp_rows = []
    for d in DOMS[1:]:
        lead = [k for k in K if (a := rank(k, d, 0)) and a <= 5 and (not k["r"][0] or k["r"][0] > 10)]
        ai_m = sum(D["stat"][e][d]["m"] for e in D["engines"]); ai_c = sum(D["stat"][e][d]["c"] for e in D["engines"])
        ai_me_c = sum(D["stat"][e][ME]["c"] for e in D["engines"])
        cmp_rows.append({"Competitor": d, "Top-5 where we are outside top 10": len(lead),
                         "Search volume of those": sum(k["v"] for k in lead),
                         "Their top 3 vs ours": f"{M[d][0]['t3']} vs {M[ME][0]['t3']}",
                         "AI mention rate": f"{ai_rate[d]}% vs {ai_rate[ME]}%",
                         "AI citations": f"{ai_c} vs {ai_me_c}"})
    st.dataframe(pd.DataFrame(cmp_rows).sort_values("Search volume of those", ascending=False), hide_index=True, width="stretch")
    THEMES = {"Free spins": ["free spin"], "No deposit": ["no deposit"], "Welcome / sign-up bonus": ["welcome", "sign up", "signup", "bonus"],
              "Slots": ["slot"], "Live / table games": ["live", "blackjack", "roulette", "baccarat", "poker"], "New casinos": ["new casino", "new online"],
              "Payment methods": ["paypal", "visa", "apple pay", "trustly", "skrill", "neteller", "paysafe", "pay by", "bank transfer", "crypto", "bitcoin", "interac", "upi"],
              "Real money": ["real money", "pay out", "payout", "fast with", "withdraw"], "Mobile / app": ["app", "mobile"],
              "Brand / review": ["review", "casino login", "login"], "Best / top lists": ["best", "top "]}
    trows = []
    for th, subs in THEMES.items():
        ks = [k for k in K if any(x in k["k"].lower() for x in subs)]
        if len(ks) < 3: continue
        mine = sum(1 for k in ks if k["r"][0] and k["r"][0] <= 5)
        best = max(DOMS[1:], key=lambda d: sum(1 for k in ks if (rank(k, d, 0) or 99) <= 5))
        bc = sum(1 for k in ks if (rank(k, best, 0) or 99) <= 5)
        trows.append({"Topic": th, "Keywords": len(ks), "Gambling.com top 5": mine, "Strongest competitor": best, "Their top 5": bc, "Gap": bc - mine})
    st.markdown("**Topics where a competitor holds more top-5 rankings than gambling.com**")
    tdf = pd.DataFrame(trows)
    if len(tdf): st.dataframe(tdf.sort_values("Gap", ascending=False), hide_index=True, width="stretch")
    ext = [(d, n) for d, n in D["src"] if d != ME and "vertexai" not in d][:8]
    st.markdown("**Sources AI engines cite most (excluding gambling.com):** " + ", ".join(f"{d} ({n})" for d, n in ext))
    st.caption("Ranks: AccuRanker (casino.org from a live check, top 30 only). Topics are matched on keyword wording, so one keyword can sit in several topics.")
    st.subheader("Suggested next steps")
    top_near = ", ".join(k["k"] for k in near[:3])
    st.markdown(
        f"1. Push the near-page-1 keywords first ({top_near}): small on-page and internal-link gains move these fastest.\n"
        f"2. Review pages where {worst} leads and compare content depth, offers and freshness.\n"
        f"3. Close AI gaps: add clear brand-product-customer statements and FAQ answers on pages behind the prompts above, and check which sources the engines cite (AI visibility tab).\n"
        f"4. Re-pull the data regularly: this is a 23 Oct snapshot, and AccuRanker and live SERPs can disagree.")
