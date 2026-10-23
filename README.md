# Organic + AI Visibility (gambling.com, casino)

Streamlit dashboard. Run: `pip install -r requirements.txt && streamlit run app.py`.
Deploy: Streamlit Community Cloud, main file `app.py`.

Data is a snapshot in `data/data.json` (AccuRanker "UK BOFU" domain 616840, DataForSEO, AI prompts), generated 2026-10-23. No automatic refresh yet.

Markets: UK, IE, CA, NZ, IN (toggle at top). Each uses its Group SEO "<market> BOFU" AccuRanker domain; competitors are that domain's AccuRanker competitor set, plus casino.org via live SERP where not tracked. UK uses the fixed 8-competitor list.
