# Restaurant Recommender

An AI-powered restaurant recommendation app that filters a real [Zomato dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) from Hugging Face and uses [Groq](https://console.groq.com/) to return ranked picks with short, personalized explanations.

**Repository:** https://github.com/HarshitM2411/zomato

---

## Features

- Filter ~51,000 restaurants by **location**, **budget**, **cuisine**, and **minimum rating**
- Send a shortlist (up to 10 candidates) to an LLM for **ranking and explanations**
- **Streamlit** web UI for local use and [Streamlit Cloud](https://streamlit.io/cloud) deployment
- Optional **Flask** app for local development

---

## How it works

```
User preferences → Filter dataset → Build prompt → Groq LLM → Display top 3–5 recommendations
```

| Layer | File | Role |
|-------|------|------|
| Ingestion | `src/ingest.py` | Load and clean Zomato data |
| Filtering | `src/filter.py` | Apply hard constraints |
| Prompt | `src/prompt_builder.py` | Build structured LLM prompt |
| LLM | `src/llm_client.py` | Call Groq API, parse JSON response |
| Display | `src/display.py` | Format results (terminal / HTML) |
| UI | `streamlit_app.py` | Streamlit entrypoint (deploy) |
| UI (local) | `app.py` | Flask entrypoint (optional) |

---

## Budget bands

| Band | Cost for two (₹) |
|------|------------------|
| Low | 0 – 300 |
| Medium | 301 – 700 |
| High | Above 700 |

---

## Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com/)
- Internet access (first run downloads the dataset from Hugging Face)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/HarshitM2411/zomato.git
cd zomato
```

### 2. Create a virtual environment

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Edit `.env` and set your Groq API key:

```env
GROQ_API_KEY=gsk_your-key-here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

---

## Run locally

### Streamlit (recommended)

```bash
streamlit run streamlit_app.py
```

Open **http://localhost:8501**

### Flask (optional)

```bash
python app.py
```

Open **http://127.0.0.1:5000**

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub (already at `HarshitM2411/zomato`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select the repo, branch `main`, main file **`streamlit_app.py`**.
4. Under **Settings → Secrets**, add:

```toml
GROQ_API_KEY = "gsk_xxxxxxxx"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
```

5. Deploy. The first load may take 1–3 minutes while the dataset downloads.

See [`docs/deploymentPlan.md`](docs/deploymentPlan.md) for full deployment details.

---

## Example usage

| Field | Example |
|-------|---------|
| Location | `Bangalore` |
| Budget | `medium` |
| Cuisine | `Italian` |
| Minimum rating | `3.5` |
| Extra preferences | `family-friendly` |

You should receive 3–5 ranked restaurants with explanations.

---

## Project structure

```
zomato/
├── streamlit_app.py      # Streamlit UI (deploy entrypoint)
├── app.py                # Flask UI (local dev)
├── requirements.txt
├── src/
│   ├── ingest.py
│   ├── filter.py
│   ├── prompt_builder.py
│   ├── llm_client.py
│   └── display.py
├── templates/            # Flask HTML
├── static/               # Flask CSS
├── docs/                 # Architecture, implementation plan, deployment
└── .streamlit/           # Streamlit config
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/problemStatement.md`](docs/problemStatement.md) | Problem and goals |
| [`docs/architecture.md`](docs/architecture.md) | System design |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Phase-wise build plan |
| [`docs/deploymentPlan.md`](docs/deploymentPlan.md) | Streamlit deployment guide |
| [`docs/edgecase.md`](docs/edgecase.md) | Edge cases and handling |

---

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | — |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | No | `https://api.groq.com/openai/v1` |
| `HF_TOKEN` | No | — (optional, faster HuggingFace downloads) |

Never commit `.env` or API keys to Git.

---

## License

This project uses the public Zomato dataset on Hugging Face. Check the dataset and Groq terms of use for your deployment.
