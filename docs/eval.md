# Evaluation Criteria — Per Phase


This document defines how to judge whether each phase from `implementation-plan.md` is complete and correct.


---


## Phase 0 — Project Setup


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F0.1 | Virtual environment created | `.venv/` directory exists; `which python` points inside it |
| F0.2 | All dependencies installed | `pip show openai datasets pandas` returns version info for all three |
| F0.3 | `src` is a Python package | `python -c "import src"` runs without `ModuleNotFoundError` |
| F0.4 | API key accessible | `python -c "import os; assert os.getenv('OPENAI_API_KEY')"` exits with code 0 |


### Exit Gate
```
python -c "import openai, datasets, pandas; print('OK')"
```
Must print `OK` with exit code 0.


---


## Phase 1 — Data Ingestion (`src/ingest.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F1.1 | Dataset loads without error | `load_zomato_dataset()` completes without raising an exception |
| F1.2 | Row count | Returned DataFrame has ≥ 10,000 rows |
| F1.3 | Canonical columns present | `df.columns` contains `name`, `location`, `cuisines`, `cost`, `rating` |
| F1.4 | Correct dtypes | `df['cost'].dtype == float64` and `df['rating'].dtype == float64` |
| F1.5 | No nulls in key fields | `df[['name','location']].isnull().sum().sum() == 0` |
| F1.6 | `BUDGET_BANDS` defined correctly | `BUDGET_BANDS['low'] == (0, 300)`, `BUDGET_BANDS['high'][0] == 701` |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E1.1 | `rating` = `"NEW"` handled | Rows with non-numeric ratings have `NaN` or `0.0`; no crash |
| E1.2 | `cost` = `"300-500"` handled | Only first numeric value extracted; no crash |


### Exit Gate
```python
df = load_zomato_dataset()
assert len(df) >= 10_000
assert {'name','location','cost','rating'}.issubset(df.columns)
assert df['cost'].dtype == 'float64'
```


---


## Phase 2 — Filtering Layer (`src/filter.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F2.1 | Location filter works | Results contain only rows where `location` contains the input string (case-insensitive) |
| F2.2 | Cuisine filter works | Results contain only rows where `cuisines` contains the input string |
| F2.3 | Cuisine blank → filter skipped | Passing `cuisine=""` returns results regardless of cuisine |
| F2.4 | Rating filter works | All returned rows have `rating >= min_rating` |
| F2.5 | Budget filter works | All returned rows have `cost` within the selected band |
| F2.6 | Result capped at 10 | `len(result) <= 10` always |
| F2.7 | Sorted by rating DESC | `result['rating'].is_monotonic_decreasing == True` (allowing ties) |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E2.1 | Non-existent location | Returns empty DataFrame, no exception |
| E2.2 | All rows exceed budget | Returns empty DataFrame, no exception |
| E2.3 | `min_rating = 5.0` | Returns empty DataFrame or only perfect-rated rows; no crash |


### Exit Gate
```python
result = filter_restaurants(df, "Bangalore", "medium", "Italian", 3.5, "")
assert len(result) <= 10
assert (result['rating'] >= 3.5).all()
```


---


## Phase 3 — Prompt Builder (`src/prompt_builder.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F3.1 | Prompt is a non-empty string | `isinstance(build_prompt(...), str) and len(...) > 0` |
| F3.2 | User preferences reflected | Prompt contains the location, budget, cuisine, and rating values passed in |
| F3.3 | All candidates listed | Number of numbered lines in prompt == number of rows in candidates DataFrame |
| F3.4 | JSON format instructions present | Prompt contains the keys `rank`, `name`, `cuisine`, `rating`, `cost_for_two`, `explanation` |
| F3.5 | Empty candidates handled | When DataFrame is empty, prompt contains a "no restaurants found" message |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E3.1 | `NaN` cost/rating → `"N/A"` | Prompt contains `"N/A"` instead of `"nan"` |
| E3.2 | `extra_preferences` with special chars | Prompt renders without breaking structure |


### Exit Gate
Manual inspection: print the prompt for a known input and confirm all 5 criteria above are visually satisfied.


---


## Phase 4 — LLM Client (`src/llm_client.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F4.1 | Returns a list | `isinstance(get_recommendations(prompt), list) == True` |
| F4.2 | List is non-empty for valid input | `len(result) >= 1` when candidates exist |
| F4.3 | Each item has required keys | Every dict contains `rank`, `name`, `cuisine`, `rating`, `cost_for_two`, `explanation` |
| F4.4 | Missing API key raises `EnvironmentError` | `EnvironmentError` raised with a descriptive message; no `AttributeError` or `KeyError` |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E4.1 | Markdown fences stripped | Passing ` ```json [...]``` ` to `_parse_response()` returns a valid list |
| E4.2 | Invalid JSON → empty list | `_parse_response("not json")` returns `[]`, no exception |
| E4.3 | Dict-wrapped array handled | `_parse_response('{"results": [...]}')` returns the inner list |
| E4.4 | Rate limit error surfaced cleanly | `openai.RateLimitError` caught and re-raised as a user-readable message |


### Exit Gate
```python
result = get_recommendations(sample_prompt)
assert isinstance(result, list)
assert all('explanation' in r for r in result)
```


---


## Phase 5 — Display Layer (`src/display.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F5.1 | Non-empty list renders without error | No exception raised; output printed to stdout |
| F5.2 | Each recommendation shows all fields | `name`, `cuisine`, `rating`, `cost_for_two`, `explanation` all appear in output |
| F5.3 | Empty list shows fallback message | Output contains "No recommendations" (or equivalent) |
| F5.4 | Rank numbers displayed | Output contains `#1`, `#2`, etc. |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E5.1 | `cost_for_two` is `None` | Displays `"N/A"` instead of `"₹None"` |
| E5.2 | `explanation` key missing | Displays empty string or `"N/A"`; no `KeyError` |


### Exit Gate
```python
mock = [{'rank':1,'name':'Test','cuisine':'Italian','rating':4.5,'cost_for_two':500,'explanation':'Great choice.'}]
display_recommendations(mock)  # must print without raising
display_recommendations([])    # must print fallback message
```


---


## Phase 6 — Orchestrator & CLI (`app.py`)


### Functional Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F6.1 | End-to-end run completes | `python app.py` with valid inputs prints recommendations and exits with code 0 |
| F6.2 | Blank location exits cleanly | App prints an error message and exits; no traceback |
| F6.3 | Invalid budget re-prompts | App does not crash; asks again until valid value entered |
| F6.4 | Invalid `min_rating` defaults to 3.5 | App continues with `3.5`; user informed of the default |
| F6.5 | Progress messages printed | At least "Loading dataset", "Filtering", "Generating" messages appear |


### Edge Case Criteria
| # | Criterion | Pass condition |
|---|---|---|
| E6.1 | `Ctrl+C` during input | App exits cleanly with no Python traceback shown to user |
| E6.2 | No candidates after filtering | App prints "No restaurants matched" and exits with code 0 |


### Exit Gate
Manual run with: `location=Bangalore`, `budget=medium`, `cuisine=Italian`, `min_rating=4.0` → recommendations printed, exit code 0.


---


## Phase 7 — End-to-End Testing


### Test Matrix


| Test | Input | Expected outcome | Pass? |
|---|---|---|---|
| T1 | Valid location + all filters | 3–5 ranked recommendations with explanations | ☐ |
| T2 | Non-existent location | "No restaurants matched" message, exit code 0 | ☐ |
| T3 | `min_rating=0.0`, broad location | Returns results; filters not over-restrictive | ☐ |
| T4 | `OPENAI_API_KEY` unset | Clear `EnvironmentError` message, no traceback | ☐ |
| T5 | LLM returns malformed JSON | "No recommendations" message, exit code 0 | ☐ |


### Performance Criteria
| # | Criterion | Target |
|---|---|---|
| P7.1 | Dataset load time (cold, with internet) | < 60 s |
| P7.2 | Dataset load time (warm cache) | < 5 s |
| P7.3 | LLM response time | < 15 s |
| P7.4 | Total wall-clock time (warm cache) | < 20 s |


### Exit Gate
All 5 test cases pass. All performance targets met on a warm cache run.


---


## Phase 8 — Documentation


### Criteria
| # | Criterion | Pass condition |
|---|---|---|
| F8.1 | README covers setup | `pip install`, `export OPENAI_API_KEY`, `python app.py` all documented |
| F8.2 | README shows example output | At least one sample recommendation block shown |
| F8.3 | Budget bands documented | Table with low/medium/high ranges present |
| F8.4 | `problemStatement.md` up to date | Reflects final scope with no stale references |
| F8.5 | `architecture.md` up to date | File structure matches what was actually built |


### Exit Gate
A reviewer unfamiliar with the project can follow the README and run the app successfully on the first attempt.