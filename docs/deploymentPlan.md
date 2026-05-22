# Deployment Plan — Streamlit (Streamlit Community Cloud)


## Overview


This project will be deployed on **[Streamlit Community Cloud](https://streamlit.io/cloud)** (free tier available). Streamlit replaces the current Flask + HTML frontend with a single Python UI file while reusing the existing pipeline in `src/`.


| Current (local) | Target (deployed) |
|-----------------|-------------------|
| `app.py` (Flask) | `streamlit_app.py` (Streamlit entrypoint) |
| `templates/` + `static/` | Streamlit widgets + native layout |
| `.env` (local secrets) | Streamlit **Secrets** (cloud dashboard) |
| Port 5000 | Hosted URL from Streamlit Cloud |


**LLM provider:** Groq (unchanged) — configured via `GROQ_API_KEY` in Streamlit secrets.


---


## Pre-deployment checklist


Before deploying, complete these implementation steps:


- [x] Add `streamlit_app.py` at the project root (Streamlit entrypoint)
- [x] Add `streamlit>=1.32.0` to `requirements.txt`
- [x] Use `@st.cache_data` around `load_zomato_dataset()` to avoid reloading ~51k rows on every interaction
- [x] Wire the same pipeline: filter → `build_prompt` → `get_recommendations` → display results with `st` components
- [x] Keep Flask files locally only (`app.py`, `templates/`, `static/`) — Streamlit Cloud uses `streamlit_app.py`
- [x] Confirm `.env` is in `.gitignore` (never commit API keys)
- [ ] Push the repo to GitHub (public repo for free Streamlit Cloud, or private with permissions)


---


## Target file structure


```
llm-restaurant-recommender/
├── streamlit_app.py          # Streamlit UI + orchestration (REQUIRED for deploy)
├── requirements.txt          # Must include streamlit + all src dependencies
├── .streamlit/
│   └── config.toml           # Optional: theme, layout
├── src/
│   ├── ingest.py
│   ├── filter.py
│   ├── prompt_builder.py
│   ├── llm_client.py
│   └── display.py            # Reuse logic; render with st instead of HTML where needed
├── docs/
│   └── deploymentPlan.md     # (this file)
├── app.py                    # Optional: keep for local Flask testing only
└── .gitignore                # .env, .venv/, __pycache__/
```


Streamlit Cloud looks for **`streamlit_app.py`** in the repo root by default. You can also set a custom path in the deploy settings (e.g. `Home.py`).


---


## `streamlit_app.py` design (to implement)


High-level flow mirroring `app.py`:


```python
# Pseudocode — implement in streamlit_app.py

import streamlit as st
from dotenv import load_dotenv

from src.ingest import load_zomato_dataset
from src.filter import filter_restaurants
from src.prompt_builder import build_prompt, NO_RESTAURANTS_MESSAGE
from src.llm_client import get_recommendations

load_dotenv()

@st.cache_data(show_spinner="Loading restaurant dataset…")
def get_dataset():
    return load_zomato_dataset()

st.set_page_config(page_title="Restaurant Recommender", layout="wide")
st.title("Restaurant Recommender")

with st.form("preferences"):
    location = st.text_input("Location *", placeholder="e.g. Bangalore")
    budget = st.selectbox("Budget", ["low", "medium", "high"], index=1)
    cuisine = st.text_input("Cuisine", placeholder="e.g. Italian (optional)")
    min_rating = st.slider("Minimum rating", 0.0, 5.0, 3.5, 0.1)
    extra = st.text_area("Extra preferences", placeholder="e.g. family-friendly")
    submitted = st.form_submit_button("Get Recommendations")

if submitted:
    # validate → filter → build_prompt → get_recommendations → st cards / errors
    ...
```


**UI mapping from Flask form:**


| Field | Streamlit widget |
|-------|------------------|
| Location | `st.text_input` (required) |
| Budget | `st.selectbox` (`low` / `medium` / `high`) |
| Cuisine | `st.text_input` (optional) |
| Min rating | `st.slider` or `st.number_input` |
| Extra preferences | `st.text_area` |
| Submit | `st.form_submit_button` |
| Results | `st.success` / `st.error` + `st.expander` or columns per recommendation |
| Loading | `st.spinner` during dataset load and Groq API call |


---


## Dependencies (`requirements.txt`)


Minimum packages for Streamlit Cloud (pin or use lower bounds as today):


```text
streamlit>=1.32.0
openai>=1.25.0
datasets>=2.19.0
pandas>=2.0.0
python-dotenv>=1.0.0
```


**Notes:**


- `flask` is **not required** on Streamlit Cloud; omit it from the deploy branch or keep only if you still run Flask locally.
- `pyarrow` is pulled in by `datasets` — no separate line needed unless the build fails (then add `pyarrow>=14.0.0`).
- First deploy may take several minutes while HuggingFace downloads the Zomato dataset; caching helps subsequent runs.


---


## Secrets and environment variables


Streamlit Cloud does **not** read a local `.env` file. Configure secrets in the dashboard:


**App → Settings → Secrets** (TOML format):


```toml
GROQ_API_KEY = "gsk_xxxxxxxx"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
```


**In code** (`src/llm_client.py` already uses `os.environ`):


```python
# Optional helper in streamlit_app.py for local dev + cloud
import os
import streamlit as st

def load_secrets():
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        os.environ.setdefault("GROQ_API_KEY", st.secrets["GROQ_API_KEY"])
        os.environ.setdefault("GROQ_MODEL", st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile"))
        os.environ.setdefault("GROQ_BASE_URL", st.secrets.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
```


Call `load_secrets()` once at the top of `streamlit_app.py`. Local runs can still use `.env` via `python-dotenv`.


| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | — |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | No | `https://api.groq.com/openai/v1` |


Optional (faster HuggingFace downloads on cloud):


```toml
HF_TOKEN = "hf_xxxxxxxx"
```


Set `HF_TOKEN` in secrets and export to `os.environ["HF_TOKEN"]` before `load_dataset()` if rate limits are hit.


---


## Optional Streamlit config (`.streamlit/config.toml`)


```toml
[theme]
primaryColor = "#2563eb"
backgroundColor = "#f4f6f8"
secondaryBackgroundColor = "#ffffff"
textColor = "#1a1a1a"
font = "sans serif"

[server]
headless = true
```


---


## Deployment steps (Streamlit Community Cloud)


### 1. Prepare the repository


```bash
git add streamlit_app.py requirements.txt .streamlit/
git commit -m "Add Streamlit app for cloud deployment"
git push origin main
```


Ensure the default branch contains `streamlit_app.py` and `requirements.txt` at the repo root.


### 2. Create the Streamlit Cloud app


1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select:
   - **Repository:** your `llm-restaurant-recommender` (or project) repo
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Click **Deploy**.


### 3. Add secrets


1. Open the deployed app → **Manage app** (bottom right) → **Settings** → **Secrets**.
2. Paste the TOML block from [Secrets and environment variables](#secrets-and-environment-variables) above.
3. Save — the app will reboot automatically.


### 4. Verify deployment


| Check | Expected |
|-------|----------|
| App loads | Title and form visible, no import errors in logs |
| First run | Spinner while dataset downloads (may take 1–3 min) |
| Valid query | e.g. Location `Bangalore`, Budget `medium`, Cuisine `Italian` → 3–5 recommendations |
| Missing `GROQ_API_KEY` | Clear error in UI, not a raw stack trace |
| No matches | “No restaurants found…” message |
| Second query | Faster due to `@st.cache_data` on dataset |


### 5. Share the URL


Streamlit provides a public URL:


```text
https://<app-name>-<branch>-<username>.streamlit.app/
```


Use this for demos and manual testing.


---


## Performance and limits (Streamlit Cloud free tier)


| Topic | Guidance |
|-------|----------|
| **Cold start** | App sleeps after inactivity; first visit reloads the app and may re-fetch the dataset unless cached in memory during the session |
| **Dataset cache** | `@st.cache_data` on `load_zomato_dataset()` — critical (~50 MB in memory, ~12s first load) |
| **Memory** | ~1 GB RAM on free tier; pandas DataFrame + dependencies should fit; avoid loading duplicate copies |
| **Groq API** | Network egress from Streamlit servers to `api.groq.com` — ensure Groq allows cloud IPs (default) |
| **Timeout** | Long first dataset download + LLM call may approach widget timeouts; show `st.spinner` and status text |
| **Secrets** | Rotated in dashboard; redeploy not required after secret update (app restarts automatically) |


---


## CI / branch strategy (recommended)


| Branch | Purpose |
|--------|---------|
| `main` | Production Streamlit deploy |
| `dev` | Optional preview deploy (second Streamlit app pointing at `dev`) |


Only merge to `main` when `streamlit run streamlit_app.py` works locally with secrets from `.env`.


**Local test before deploy:**


```powershell
cd "c:\Users\ASUS\Desktop\LLM Learning"
.\.venv\Scripts\Activate.ps1
pip install streamlit
streamlit run streamlit_app.py
```


Opens at `http://localhost:8501`.


---


## Security checklist


- [ ] Never commit `.env` or API keys
- [ ] Use Streamlit Secrets for `GROQ_API_KEY` only on cloud
- [ ] Restrict Groq key permissions if Groq console supports scoped keys
- [ ] Treat `extra_preferences` as untrusted input (prompt builder already labels the block; keep system instructions strict)
- [ ] Pin dependency versions in `requirements.txt` after a successful deploy to avoid surprise breakages


---


## Rollback and local fallback


If Streamlit deploy fails:


1. Check **Logs** in Streamlit Cloud (Manage app → Logs) for import or memory errors.
2. Fall back to local Flask: `python app.py` on port 5000.
3. Fix `requirements.txt` or missing files, push, and redeploy (Streamlit auto-rebuilds on push).


---


## Post-deploy documentation updates


After `streamlit_app.py` exists and the app is live:


- [ ] Add deploy URL and setup steps to `README.md` (Phase 8)
- [ ] Note in `docs/architecture.md` that production UI is Streamlit; Flask is dev-only (optional)
- [ ] Update `docs/implementation-plan.md` with a **Phase 9 — Streamlit deployment** section if you track phases there


---


## Summary timeline


| Step | Action | Owner |
|------|--------|-------|
| 1 | Implement `streamlit_app.py` + `@st.cache_data` | Dev |
| 2 | Update `requirements.txt` (+ optional `.streamlit/config.toml`) | Dev |
| 3 | Test locally with `streamlit run streamlit_app.py` | Dev |
| 4 | Push to GitHub | Dev |
| 5 | Create Streamlit Cloud app + add Secrets | Dev |
| 6 | Smoke-test deployed URL | Dev |
| 7 | Update README with live link | Dev |


**Exit criterion:** Public Streamlit URL returns ranked recommendations for a valid query (e.g. Bangalore, medium, Italian, min rating 3.5) with no unhandled errors.
