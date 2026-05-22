# Edge Cases — Restaurant Recommendation System


Edge cases are organised by the layer in which they originate, matching the architecture in `architecture.md`.


---


## Phase 0 — Project Setup


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E0.1 | `OPENAI_API_KEY` not set in environment | `llm_client.py` will raise an unguarded `KeyError` or `None`-type error | Raise a clear `EnvironmentError` with instructions in `_build_client()` |
| E0.2 | Python version < 3.9 | f-strings, type hints, and `dict` merge operators may fail silently or with cryptic errors | Document minimum Python version in README; check with `python --version` |
| E0.3 | No internet connection on first run | `datasets.load_dataset()` will hang or raise a `ConnectionError` | Catch and surface a human-readable message: "Could not download dataset. Check your internet connection." |


---


## Phase 1 — Data Ingestion (`ingest.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E1.1 | Dataset column names change in a future HuggingFace upload | All downstream filters silently operate on `NaN` columns | `_rename_if_present()` handles known variants; log a warning if canonical columns are missing after cleaning |
| E1.2 | `cost` field contains values like `"300-500"` or `"₹400"` | Regex extracts only the first number, which may misrepresent ranges | Use the lower bound of a range; document this assumption |
| E1.3 | `rating` field contains `"NEW"`, `"-"`, or `"0"` | Coercion produces `NaN` or `0.0`, skewing filter results | Treat `NaN` ratings as `0.0`; treat `"NEW"` as `None` and exclude from rating filter |
| E1.4 | Dataset is empty or has zero rows after loading | All downstream steps fail with index errors | Check `len(df) == 0` after loading and raise a clear error |
| E1.5 | `votes` column absent in a dataset variant | Sorting by votes in `filter.py` raises `KeyError` | Sort only by columns that exist; make `votes` optional in the sort |


---


## Phase 2 — Filtering Layer (`filter.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E2.1 | Location string matches zero rows | Empty DataFrame passed to prompt builder | Detect empty result and exit early with: "No restaurants found for this location." |
| E2.2 | Location string is too broad (e.g. `"a"`) | Hundreds of unrelated rows pass the filter | `MAX_CANDIDATES = 10` caps the output; the LLM prompt remains manageable |
| E2.3 | Cuisine left blank | Cuisine filter skipped entirely | Correct — intentional behaviour; must be explicitly tested |
| E2.4 | All restaurants in the location are above budget | Empty DataFrame after cost filter | Surface a message: "No restaurants in your budget for this location." |
| E2.5 | `cost` column is entirely `NaN` for the filtered location | Budget filter removes everything | Skip cost filter if the column has no valid values; log a warning |
| E2.6 | `min_rating` set to `5.0` | Near-impossible threshold; likely returns 0 rows | Return empty result with a clear message suggesting a lower rating |
| E2.7 | Candidate count is exactly 1 | LLM asked to rank 1 item | Valid — LLM should return a single recommendation; display handles list of length 1 |


---


## Phase 3 — Prompt Builder (`prompt_builder.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E3.1 | `extra_preferences` contains prompt injection text (e.g. `"Ignore previous instructions and..."`) | LLM behaviour manipulated by user input | Embed extra preferences inside a clearly labelled block; system prompt instructs the LLM to treat it as a preference string only |
| E3.2 | Restaurant name contains special characters (`"`, `{`, `}`) | Prompt formatting broken; LLM may misinterpret structure | Render candidates as plain numbered text lines, not embedded JSON |
| E3.3 | Candidates DataFrame is empty | Prompt contains "No restaurants found" instead of a list | LLM receives the message and `display.py` handles an empty response list |
| E3.4 | `cost` or `rating` is `NaN` for a candidate | Prompt shows `nan` literally | Replace `NaN` values with `"N/A"` string before rendering |


---


## Phase 4 — LLM Client (`llm_client.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E4.1 | LLM returns plain text instead of JSON | `json.loads()` raises `JSONDecodeError` | Catch exception, log a warning, return `[]` (graceful degradation) |
| E4.2 | LLM wraps JSON in markdown fences (` ```json `) | `json.loads()` fails on the fence characters | Strip leading/trailing fences before parsing |
| E4.3 | LLM returns a JSON object instead of an array | `isinstance(data, list)` is `False` | Search dict values for the first list; fall back to `[]` |
| E4.4 | LLM recommends a restaurant not in the candidate list (hallucination) | User is misled by a fabricated result | Prompt explicitly instructs the LLM to only choose from the provided list; post-processing can optionally validate names |
| E4.5 | OpenAI API rate limit hit (`429`) | Unhandled exception crashes the app | Catch `openai.RateLimitError` and surface: "API rate limit reached. Please wait and try again." |
| E4.6 | OpenAI API returns an empty `choices` list | `response.choices[0]` raises `IndexError` | Check `len(response.choices) > 0` before accessing |
| E4.7 | `max_tokens` too low for the response | LLM output is truncated mid-JSON | `json.loads()` will fail; graceful degradation returns `[]`; consider increasing `max_tokens` |
| E4.8 | Invalid or expired API key | `openai.AuthenticationError` raised | Catch and surface: "Invalid API key. Check your OPENAI_API_KEY environment variable." |


---


## Phase 5 — Display Layer (`display.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E5.1 | Recommendations list is empty | Nothing printed; user confused | Print: "No recommendations could be generated. Try broadening your preferences." |
| E5.2 | `cost_for_two` key is `null` / missing | `₹None` printed | Default to `"N/A"` if key is absent or `None` |
| E5.3 | `explanation` field is missing from a recommendation dict | `KeyError` crash | Use `.get("explanation", "")` with a safe default |
| E5.4 | Terminal does not support UTF-8 (e.g. older Windows consoles) | `─` divider and `₹` symbol render as `?` | Acceptable known limitation; document in README |


---


## Phase 6 — Orchestrator (`app.py`)


| # | Edge Case | Risk | Mitigation |
|---|---|---|---|
| E6.1 | User enters blank location | Required field missing | Detect empty string and exit with a clear message |
| E6.2 | User enters an invalid budget (e.g. `"cheap"`) | Filter skips budget or crashes | Re-prompt in a loop until a valid value is entered |
| E6.3 | User enters a non-numeric `min_rating` (e.g. `"good"`) | `float()` raises `ValueError` | Catch `ValueError`, default to `3.5`, and inform the user |
| E6.4 | User sends `Ctrl+C` (keyboard interrupt) mid-session | Unhandled `KeyboardInterrupt` prints a traceback | Wrap `main()` in a `try/except KeyboardInterrupt` and exit cleanly |
| E6.5 | Dataset takes > 60 s to load on a slow connection | User sees no feedback and assumes the app is frozen | Print a progress message before the load call |