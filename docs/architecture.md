# Detailed Architecture — Restaurant Recommendation System


---


## 1. High-Level Component Diagram


```
┌─────────────────────────────────────────────────────────────────┐
│                        User (CLI)                               │
│  Inputs: location, budget, cuisine, min_rating, extra_prefs     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     app.py  (Orchestrator)                      │
│  • Collects user input                                          │
│  • Calls each layer in sequence                                 │
│  • Handles errors and edge cases                                │
└────┬──────────────┬──────────────┬──────────────┬──────────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
 ingest.py      filter.py    prompt_builder.py  display.py
                                   │
                                   ▼
                             llm_client.py
                                   │
                                   ▼
                          Groq API (LLM)
```


---


## 2. Layer-by-Layer Breakdown


### 2.1 Data Ingestion Layer — `src/ingest.py`


**Responsibility:** Load the raw Zomato dataset and return a clean, normalised Pandas DataFrame.


**Steps:**
1. Call `datasets.load_dataset("ManikaSaini/zomato-restaurant-recommendation")` — downloads on first run, cached by HuggingFace thereafter.
2. Convert to `pandas.DataFrame`.
3. Normalise column names (lowercase, underscores) to handle dataset variants.
4. Rename ambiguous columns to canonical names:
   - `restaurant_name` → `name`
   - `city` / `locality` → `location`
   - `approx_cost(for_two_people)` / `average_cost_for_two` → `cost`
   - `aggregate_rating` / `rate` → `rating`
5. Coerce `cost` and `rating` to `float`, stripping commas and non-numeric characters.
6. Drop rows missing `name` or `location`.


**Output:** `pd.DataFrame` with guaranteed columns: `name`, `location`, `cuisines`, `cost`, `rating`, `votes`.


---


### 2.2 Filtering Layer — `src/filter.py`


**Responsibility:** Narrow the full dataset down to the top N candidates that match the user's hard constraints.


**Budget band mapping:**


| Band   | Cost range (₹, for two) |
|--------|-------------------------|
| low    | 0 – 300                 |
| medium | 301 – 700               |
| high   | > 700                   |


**Filter pipeline (applied in order):**


```
DataFrame (full)
    │
    ├─ [location]   str.contains(location, case=False)
    ├─ [cuisine]    str.contains(cuisine, case=False)  ← skipped if blank
    ├─ [rating]     rating >= min_rating
    └─ [cost]       cost between budget_band[low], budget_band[high]
    │
    ▼
Sort by: rating DESC, votes DESC
    │
    ▼
Head(10)  ← MAX_CANDIDATES passed to LLM
```


**Output:** `pd.DataFrame` of up to 10 rows.


---


### 2.3 Prompt Builder — `src/prompt_builder.py`


**Responsibility:** Convert the filtered DataFrame and user preferences into a structured natural-language prompt for the LLM.


**Prompt structure:**


```
[System context]
  You are a friendly, knowledgeable food expert…


[User Preferences block]
  Location / Budget / Cuisine / Min rating / Extra preferences


[Candidate Restaurant List]
  1. <name> | Location: … | Cuisine: … | Rating: … | Cost: ₹… | Votes: …
  2. …
  …


[Task Instructions]
  - Rank restaurants best-to-worst for this user
  - Return top 3–5 as a JSON array
  - Each item: { rank, name, cuisine, rating, cost_for_two, explanation }
  - No text outside the JSON array
```


**Design rationale:** Giving the LLM the candidate list (not the full dataset) keeps the prompt short, reduces cost, and constrains hallucination — the LLM can only recommend restaurants that actually exist in the filtered set.


---


### 2.4 LLM Client — `src/llm_client.py`


**Responsibility:** Send the prompt to the Groq API and return parsed recommendation objects.


**Provider:** [Groq](https://console.groq.com/) — the `openai` Python SDK is configured with Groq's OpenAI-compatible base URL.


**Configuration (via environment variables):**


| Variable        | Required | Default                          | Purpose                              |
|-----------------|----------|----------------------------------|--------------------------------------|
| `GROQ_API_KEY`  | Yes      | —                                | Groq API authentication              |
| `GROQ_MODEL`    | No       | `llama-3.3-70b-versatile`        | Groq model selection                 |
| `GROQ_BASE_URL` | No       | `https://api.groq.com/openai/v1` | Groq OpenAI-compatible API endpoint  |


**API call parameters:**
- `temperature: 0.4` — low enough for consistent ranking, enough for natural language variation
- `max_tokens: 1500` — sufficient for 5 recommendations with explanations


**Response handling:**
1. Strip markdown code fences (` ```json … ``` `) if present.
2. `json.loads()` the response.
3. If the root is a dict, search its values for the first list (handles models that wrap the array).
4. Return empty list on parse failure (graceful degradation).


---


### 2.5 Display Layer — `src/display.py`


**Responsibility:** Format and print the LLM output to stdout in a human-readable layout.


**Output format per recommendation:**
```
#1  <Restaurant Name>
────────────────────────────────────────────────────────────
  Cuisine   : <cuisine>
  Rating    : <rating> / 5
  Cost/Two  : ₹<cost>


  Why this? : <AI explanation>
```


---


### 2.6 Orchestrator — `app.py`


**Responsibility:** Wire all layers together and manage the end-to-end flow.


**Execution flow:**
```
1. collect_preferences()        → dict of user inputs (validated inline)
2. load_zomato_dataset()        → full DataFrame
3. filter_restaurants(df, ...)  → candidate DataFrame (≤10 rows)
4. build_prompt(candidates, ...) → prompt string
5. get_recommendations(prompt)  → list of recommendation dicts
6. display_recommendations(...)  → printed output
```


**Input validation:**
- `location` — required; exit if blank.
- `budget` — restricted to `low` / `medium` / `high`; re-prompts until valid.
- `min_rating` — clamped to `[0.0, 5.0]`; defaults to `3.5` on invalid input.


---


## 3. Data Flow Diagram


```
HuggingFace API
      │  (datasets library, cached after first download)
      ▼
  raw DataFrame  (51,000+ rows)
      │
      │  ingest.py: normalise columns, coerce types, drop nulls
      ▼
  clean DataFrame
      │
      │  filter.py: location / cuisine / rating / budget filters
      ▼
  candidate DataFrame  (≤10 rows)
      │
      │  prompt_builder.py: render to structured text
      ▼
  prompt string
      │
      │  llm_client.py: HTTP POST → Groq Chat Completions API
      ▼
  raw JSON string  (from LLM)
      │
      │  llm_client.py: parse & validate JSON
      ▼
  list[dict]  (ranked recommendations)
      │
      │  display.py: format to terminal
      ▼
  Printed output  (user sees top 3–5 recommendations)
```


---


## 4. File Structure


```
llm-restaurant-recommender/
├── app.py                    # Orchestrator / CLI entrypoint
├── requirements.txt          # openai, datasets, pandas
├── docs/
│   ├── problemStatement.md
│   └── architecture.md       # (this file)
├── data/
│   └── .gitkeep              # HuggingFace cache written here at runtime
└── src/
    ├── __init__.py
    ├── ingest.py             # Data ingestion & cleaning
    ├── filter.py             # Preference-based filtering
    ├── prompt_builder.py     # LLM prompt construction
    ├── llm_client.py         # Groq API wrapper (openai SDK)
    └── display.py            # Terminal output formatting
```


---


## 5. Key Design Decisions


| Decision | Rationale |
|---|---|
| Filter before prompting | Avoids sending thousands of rows to the LLM; reduces cost and latency |
| Structured JSON response | Enables reliable parsing without fragile string extraction |
| Low temperature (0.4) | Produces stable, consistent rankings while keeping explanations natural |
| Graceful degradation on parse failure | App doesn't crash if the LLM returns unexpected output |
| Environment variable config | Keeps secrets out of code; supports swapping models or endpoints without code changes |
| Groq via `openai` SDK | Fast inference with an OpenAI-compatible client — no separate Groq SDK required |
| HuggingFace `datasets` library | Handles download, caching, and format conversion automatically |


---


## 6. Dependencies


| Package | Version | Purpose |
|---|---|---|
| `openai` | ≥ 1.25.0 | LLM API client (configured for Groq's OpenAI-compatible endpoint) |
| `datasets` | ≥ 2.19.0 | Load Zomato dataset from HuggingFace |
| `pandas` | ≥ 2.0.0 | DataFrame operations for filtering |