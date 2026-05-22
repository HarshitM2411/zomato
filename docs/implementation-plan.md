# Phase-wise Implementation Plan — Restaurant Recommendation System


---


## Phase 0 — Project Setup


**Goal:** Establish a working local environment before writing any application code.


### Tasks
- [ ] Create the project directory structure as defined in `architecture.md §4`
- [ ] Create and activate a Python virtual environment (`python -m venv .venv`)
- [ ] Create `requirements.txt` with pinned dependencies: `openai>=1.25.0`, `datasets>=2.19.0`, `pandas>=2.0.0`
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Create `src/__init__.py` (empty, marks `src` as a package)
- [ ] Create a `.env.example` file documenting the required environment variables (`GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL`)
- [ ] Set `GROQ_API_KEY` in the local environment and verify it is accessible


**Exit criterion:** `python -c "import openai, datasets, pandas; print('OK')"` runs without errors.


---


## Phase 1 — Data Ingestion (`src/ingest.py`)


**Goal:** Load the Zomato dataset from HuggingFace and produce a clean, normalised DataFrame.


### Tasks
- [ ] Implement `load_zomato_dataset()` — calls `datasets.load_dataset(...)` and converts to DataFrame
- [ ] Implement column name normalisation (lowercase, underscores)
- [ ] Implement column renaming for known variants (`restaurant_name → name`, `aggregate_rating → rating`, etc.)
- [ ] Implement type coercion for `cost` (strip commas, extract numeric) and `rating` (extract float)
- [ ] Drop rows where `name` or `location` is null
- [ ] Define `BUDGET_BANDS` dict (`low / medium / high → (min, max)`)


### Verification
- [ ] Print `df.columns.tolist()` and confirm canonical column names are present
- [ ] Print `df[['name','location','cuisines','cost','rating']].head(5)` — all values should be non-null and correctly typed
- [ ] Confirm `df['cost'].dtype == float64` and `df['rating'].dtype == float64`


**Exit criterion:** `load_zomato_dataset()` returns a DataFrame with ≥ 10,000 rows and the expected column types.


---


## Phase 2 — Filtering Layer (`src/filter.py`)


**Goal:** Implement preference-based filtering that returns a shortlist of up to 10 candidates.


### Tasks
- [ ] Implement `filter_restaurants(df, location, budget, cuisine, min_rating, extra_preferences)`
- [ ] Location filter — case-insensitive partial string match on `location` column
- [ ] Cuisine filter — case-insensitive partial string match on `cuisines` column; skip if blank
- [ ] Rating filter — `rating >= min_rating`
- [ ] Budget filter — map `budget` string to `BUDGET_BANDS` and apply `cost` range filter
- [ ] Sort results by `rating` DESC, then `votes` DESC
- [ ] Return `head(MAX_CANDIDATES)` (10 rows)


### Verification
- [ ] Call with `location="Bangalore"`, `budget="medium"`, `cuisine="Italian"`, `min_rating=3.5` — confirm result is ≤ 10 rows
- [ ] Call with a non-existent location — confirm empty DataFrame is returned (not an error)
- [ ] Call with `cuisine=""` — confirm the cuisine filter is skipped


**Exit criterion:** All three verification cases behave as expected.


---


## Phase 3 — Prompt Builder (`src/prompt_builder.py`)


**Goal:** Convert the candidate DataFrame and user preferences into a well-structured LLM prompt.


### Tasks
- [ ] Implement `_format_candidates(df)` — renders each row as a numbered text line with all key fields
- [ ] Implement `build_prompt(candidates, location, budget, cuisine, min_rating, extra_preferences)` — assembles the full prompt string
- [ ] Include system context, user preferences block, candidate list, and JSON output instructions
- [ ] Handle the empty-candidates edge case (return a "no restaurants found" message)


### Verification
- [ ] Print a generated prompt for a sample input and manually inspect:
  - Preferences are accurately reflected
  - All candidate restaurants appear in the list
  - JSON output format instructions are clear and unambiguous


**Exit criterion:** Generated prompt is human-readable, complete, and contains no placeholder text.


---


## Phase 4 — LLM Client (`src/llm_client.py`)


**Goal:** Send the prompt to the Groq API and return a parsed list of recommendation dicts.


**Provider:** [Groq](https://console.groq.com/) — accessed via the `openai` Python SDK using Groq's OpenAI-compatible Chat Completions endpoint (`https://api.groq.com/openai/v1`).


### Tasks
- [ ] Implement `_build_client()` — reads `GROQ_API_KEY` and optional `GROQ_BASE_URL` (default `https://api.groq.com/openai/v1`) from environment; raises a clear `EnvironmentError` if key is missing
- [ ] Implement `get_recommendations(prompt)` — calls `client.chat.completions.create(...)` with `model` from `GROQ_MODEL` (default `llama-3.3-70b-versatile`), `temperature=0.4`, `max_tokens=1500`
- [ ] Implement `_parse_response(raw)` — strips markdown fences, runs `json.loads`, handles dict-wrapped arrays, returns `[]` on parse failure


### Verification
- [ ] Send a minimal test prompt and confirm a non-empty list is returned
- [ ] Manually pass a response string with markdown fences — confirm they are stripped correctly
- [ ] Unset `GROQ_API_KEY` and confirm a clear `EnvironmentError` is raised (not an `AttributeError` or silent failure)


**Exit criterion:** `get_recommendations(prompt)` returns a `list[dict]` with `rank`, `name`, `cuisine`, `rating`, `cost_for_two`, and `explanation` keys.


---


## Phase 5 — Display Layer (`src/display.py`)


**Goal:** Format and print recommendations to the terminal in a clean, readable layout.


### Tasks
- [ ] Implement `display_recommendations(recommendations)` — iterates the list and prints each recommendation
- [ ] Handle empty list — print a helpful "no recommendations" message
- [ ] Format each item: rank, name, divider line, cuisine, rating, cost, explanation


### Verification
- [ ] Pass a hardcoded list of 3 mock recommendation dicts — confirm the output is well-formatted
- [ ] Pass an empty list — confirm the fallback message is printed


**Exit criterion:** Output is readable and correctly handles both the populated and empty cases.


---


## Phase 6 — Orchestrator & CLI (`app.py`)


**Goal:** Wire all layers together into a single runnable CLI script.


### Tasks
- [ ] Implement `collect_preferences()` — prompts user for all five inputs with inline validation
  - `location`: required; exit with message if blank
  - `budget`: re-prompt until `low` / `medium` / `high` is entered
  - `min_rating`: parse float, clamp to `[0.0, 5.0]`, default to `3.5` on invalid input
- [ ] Implement `main()` — calls all layers in sequence, prints progress messages between steps
- [ ] Add `if __name__ == "__main__": main()` guard


### Verification
- [ ] Run end-to-end with valid inputs — confirm recommendations are printed
- [ ] Enter a blank location — confirm the application exits with a clear message
- [ ] Enter an invalid budget (e.g. `"cheap"`) — confirm it re-prompts


**Exit criterion:** Full pipeline runs from `python app.py` without errors for a valid set of inputs.


---


## Phase 7 — End-to-End Testing


**Goal:** Validate the complete system against the success criteria from `problemStatement.md`.


### Test Cases


| # | Input | Expected outcome |
|---|---|---|
| T1 | Valid location + all filters | 3–5 ranked recommendations with explanations |
| T2 | Location with no matches | "No restaurants matched" message, clean exit |
| T3 | Very low `min_rating` (0.0), broad location | Returns results (confirms filters aren't over-restrictive) |
| T4 | Missing `GROQ_API_KEY` | Clear error message, no stack trace shown to user |
| T5 | LLM returns malformed JSON | Graceful degradation, "No recommendations" message |


### Checklist
- [ ] All 5 test cases pass
- [ ] No unhandled exceptions under normal usage
- [ ] Dataset loads from cache on second run (faster startup)


---


## Phase 8 — Documentation


**Goal:** Ensure the project is understandable and runnable by anyone.


### Tasks
- [ ] Write `README.md` with: setup steps, environment variable instructions, example session output, budget band table
- [ ] Confirm `docs/problemStatement.md` and `docs/architecture.md` are up to date


**Exit criterion:** A new developer can clone the repo, follow the README, and run the app successfully.


---


## Summary Timeline


| Phase | Component | Dependency |
|---|---|---|
| 0 | Project setup | — |
| 1 | `ingest.py` | Phase 0 |
| 2 | `filter.py` | Phase 1 |
| 3 | `prompt_builder.py` | Phase 2 |
| 4 | `llm_client.py` | Phase 3 |
| 5 | `display.py` | Phase 4 |
| 6 | `app.py` | Phases 1–5 |
| 7 | End-to-end testing | Phase 6 |
| 8 | Documentation | Phase 7 |