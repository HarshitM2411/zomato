# Restaurant Recommendation System — Problem Statement


## Overview


Build an intelligent, LLM-powered restaurant recommendation system that takes a user's personal preferences (location, budget, cuisine, rating) and returns ranked, human-readable recommendations drawn from a real-world restaurant dataset.


---


## Problem Being Solved


Discovering the right restaurant from hundreds of options is overwhelming. Generic search tools return long, unsorted lists with no reasoning behind the results. Users waste time reading through reviews and comparing options manually.


This system solves that by:
- Accepting natural preference inputs from the user
- Filtering a real-world dataset to a relevant shortlist
- Passing that shortlist to an LLM which ranks and explains each recommendation in plain English


The result: a concise, personalised, reasoned set of recommendations — as if a knowledgeable friend had done the research.


---


## Dataset


**Source:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on Hugging Face


**Key fields used:**
| Field | Description |
|---|---|
| `name` | Restaurant name |
| `location` / `city` | Geographic location |
| `cuisines` | Comma-separated list of cuisines served |
| `cost` / `approx_cost` | Approximate cost for two people |
| `rating` / `aggregate_rating` | Aggregate user rating (0–5) |
| `votes` | Number of votes/reviews |
| `restaurant_type` | Dine-in, Delivery, Café, etc. |
| `highlights` | Notable features (family-friendly, rooftop, etc.) |


---


## User Inputs


| Preference | Type | Example |
|---|---|---|
| Location | String | `"Delhi"`, `"Bangalore"` |
| Budget | Enum | `low` / `medium` / `high` |
| Cuisine | String | `"Italian"`, `"Chinese"` |
| Minimum rating | Float | `3.5` |
| Additional preferences | Free text | `"family-friendly"`, `"quick service"` |


---


## System Workflow


```
User Preferences
      │
      ▼
Data Ingestion Layer
  └── Load Zomato dataset from Hugging Face
  └── Clean & normalise fields
      │
      ▼
Filtering Layer
  └── Filter by location, budget range, cuisine, min rating
  └── Produce a ranked shortlist (top N candidates)
      │
      ▼
LLM Integration Layer
  └── Build a structured prompt with shortlist + user preferences
  └── Call LLM API (OpenAI / compatible)
  └── Parse and validate LLM response
      │
      ▼
Output Display
  └── Restaurant name, cuisine, rating, cost
  └── AI-generated explanation of why it fits
```


---


## Technical Architecture


```
llm-restaurant-recommender/
├── data/
│   └── (cached dataset files)
├── src/
│   ├── ingest.py          # Load & preprocess Zomato dataset
│   ├── filter.py          # Filter restaurants by user preferences
│   ├── prompt_builder.py  # Build structured LLM prompts
│   ├── llm_client.py      # LLM API integration
│   └── display.py         # Format and print results
├── app.py                 # Main CLI entrypoint
├── requirements.txt
└── README.md
```


---


## Success Criteria


1. The system correctly filters the dataset based on all four preference dimensions.
2. The LLM produces a ranked list with a clear, coherent explanation for each recommendation.
3. Results are displayed in a clean, readable format in the terminal.
4. The pipeline runs end-to-end without manual intervention after preferences are entered.


---


## Constraints & Assumptions


- Dataset is loaded from Hugging Face `datasets` library (requires internet on first run; cached thereafter).
- LLM calls require a valid API key (OpenAI-compatible endpoint).
- Budget bands map to approximate cost-for-two: low ≤ ₹300, medium ₹301–₹700, high > ₹700.
- Minimum viable output: top 3–5 recommendations with AI explanations.