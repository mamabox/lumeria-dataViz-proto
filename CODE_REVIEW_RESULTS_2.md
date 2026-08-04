# Code Review #2: streamlit_app/

Scope: everything in `streamlit_app/` **except** `views/video_sync.py`, `modules/video_exporter.py`, and `modules/video_exporter_pipe.py` — that cluster is on hold by request. This is a follow-up to `CODE_REVIEW_RESULTS.md`, reflecting the substantial refactor work done since (the `GameDataError`/`FirestoreConnectionError` error handling, the `get_loaded_data` consolidation, the `data_export.py` → `animation_exporter.py` split, level-aware map config/images/buildings, and various smaller cleanups).

## 1. Summary

This codebase is in noticeably better shape than the first pass. The duplication that dominated the first review is gone — `get_loaded_data` is now a genuine single source of truth, `data_loader.py` has proper error boundaries, and the module/view/component layering is clean and consistently followed. What's left is smaller-grained: a few stale or slightly wrong docstrings/comments, a couple of dead variables, one real architecture-doc violation (`firestore_client.py` claims "no Streamlit imports" but has one), and small naming/formatting inconsistencies. Nothing here is a functional bug on the scale of what the first review found.

## 2. Findings

### Correctness / accuracy

- **`data_loader.py:59`** — `level_number: str = challenge_list["levelNumber"]`. The type hint says `str`, but the actual JSON value is an `int` (confirmed: `example_game_data.json` has `"levelNumber": 1`). This hint is actively wrong, not just missing — worth fixing before it gets copied elsewhere as you add type hints, since `get_loaded_data` and `LEVELS`/`MAP_IMAGES` all depend on `f"level_{level_number}"` formatting correctly, which only works because the real runtime value is an int.
- **`modules/firestore_client.py:1-3`** — the module docstring says *"Pure Python — no Streamlit imports"*, but `get_firestore_client` does `import streamlit as st` inline (to read `st.secrets["firebase"]["credentials"]`). This is a real violation of the architecture rule this project is following everywhere else (modules don't import Streamlit) — worth either updating the docstring to be honest about the exception, or moving the "try Streamlit secrets" concern into the view layer and passing resolved credentials in.
- **`modules/map_builder.py:211`** — the comment `# One fewer cell than grid points in each direction` sits above a loop that iterates `range(cols)` / `range(rows)` directly — it doesn't do anything "one fewer" than anything. This looks like a leftover from an earlier version of the logic; as written it actively misleads a reader rather than helping, which is worse than no comment at all.
- **`modules/map_config.py:24-25`** — `get_map_config`'s docstring says `Returns: dict with 'coord' and 'extent' tuples`, but the actual returned keys are `coord` and `axis_range` — there's no `extent` key. Stale docstring from an earlier naming.

### Dead code

- **`modules/map_animation.py:62`** — `start_idx = len(fig.data)` inside `add_animated_traces` is assigned and never read again (the function uses `event_start`/`attempt_start` for actual indexing instead). Safe to delete.
- **`modules/animation_exporter.py:35`** — `for i, frame in enumerate(fig.frames):` — `i` is never used in the loop body (only `frame` is). Simplify to `for frame in fig.frames:`.
- **`components/sidebar.py:28-35`** — the commented-out level-selection block (`# level_name = st.sidebar.selectbox(...)`) is still sitting there. Flagged in the first review, still present.

### Readability / naming

- **`components/sidebar.py:12`** — `TEMP_DIR:str = os.path.join(...)` — missing space after the colon (`TEMP_DIR: str`), and inconsistent with the module's own `_BASE_DIR`/`_BUILDINGS_PATH`-style leading-underscore convention for module-private constants (in `data_loader.py`) — this one has no leading underscore despite being just as internal-only.
- **`views/home.py:52`** — `col_a, col_f, col_b, col_c, col_d, col_e = st.columns(6)` — the tuple-unpacking order (`a, f, b, c, d, e`) doesn't match the order the columns are actually used in below (`with col_a: ... with col_b: ... with col_c: ... with col_d: ... with col_e: ... with col_f:` — a literal alphabetical walk, `col_f` last). Whoever added the "Level" column inserted `col_f` out of position in the unpacking line but placed its `with` block correctly at the end — meaning the two orderings disagree with each other, which will confuse the next person who tries to reorder columns and trusts the unpacking line's position.
- **`views/about.py:78`** — `col_a, col_b, col_c,col_d = st.columns(4)` — missing space after the second comma.
- **`modules/map_config.py:16-26`** — `get_map_config`'s docstring uses an `Args:`/`Returns:` block style, while every other docstring in this codebase (and in this same file — the module docstring, `MapBounds`) uses plain prose. Not wrong, just the one place this codebase mixes docstring conventions.

### Minor logic / efficiency note

- **`views/firestore_test.py`** — the "Preview selected session" section (top of the page, always runs) and the "Load session" button handler each independently call `get_session_game_data(db, selected_id)` and `get_game_data_dict_from_dict(raw_data)` for the *same* `selected_id`. Clicking "Load session" re-fetches from Firestore and re-parses data that was already fetched and parsed a few lines above for the preview. Not a bug — it's a test/dev page — but worth knowing it's doing the Firestore round-trip and JSON parse twice per interaction.

### Solid / worth calling out positively

- `get_loaded_data` is now exactly the kind of single-responsibility, single-source-of-truth function a codebase like this should have — both callers (`sidebar.py`, `firestore_test.py`) trust it completely and can't drift apart the way the old duplicated dict-building code could.
- `GameDataError`/`FirestoreConnectionError` are a clean, consistent pattern: module raises a typed exception, view catches it and shows `st.error()` + `st.stop()`. Applied consistently at every call site that needed it.
- `VideoPlayer.__init__`'s `isOpened()` check, now mirrored in `animation_exporter.py`, is a good model of "check the OpenCV object actually opened before trusting it" — exactly the kind of defensive check this codebase was missing in the first review.
- Constant naming (`UPPER_SNAKE_CASE`), function naming (`snake_case`), class naming (`PascalCase`) are consistent across every file reviewed here, aside from the two comma/colon spacing nits above.

## 3. File-by-file quick reference

| File | Status |
|---|---|
| `app.py` | Clean. |
| `components/export.py` | Clean. |
| `components/sidebar.py` | Dead level-selection block still present; `TEMP_DIR` naming/spacing nit; `_save_upload`'s docstring says "for json and cv2" but sidebar.py itself never touches cv2 — that's a downstream consumer's concern, not this function's. |
| `modules/animation_exporter.py` | Unused loop variable `i`. Otherwise clean. |
| `modules/data_export.py` | Clean. |
| `modules/data_loader.py` | Wrong `level_number` type hint. `get_buildings_df`'s docstring doesn't mention the `level`/`building_number` columns it now depends on downstream — minor, not urgent. |
| `modules/firestore_client.py` | Docstring/architecture-rule mismatch (inline `streamlit` import). Broad `except Exception:` around the secrets read could mask unrelated bugs. |
| `modules/map_animation.py` | Unused `start_idx`. `add_playback_controls` has one comment line indented 3 spaces instead of 4 (cosmetic). Otherwise well organized. |
| `modules/map_builder.py` | Stale/misleading comment in `add_grid_labels`. Otherwise clean, good separation between the trace-building helpers. |
| `modules/map_config.py` | Stale `Returns:` docstring; inconsistent docstring style vs. rest of codebase. |
| `modules/map_styles.py` | Clean. |
| `modules/video_player.py` | Clean — a good model file. |
| `views/about.py` | Missing space after comma in column unpacking. Otherwise fine (mostly prose/markdown). |
| `views/animated_map.py` | Clean — all three prior findings resolved. |
| `views/firestore_test.py` | Clean, all four prior findings resolved. Minor: duplicate fetch+parse noted above. |
| `views/home.py` | Column unpacking order doesn't match usage order. |
| `views/static_map.py` | Clean. |

## 4. Suggested fixes (prioritized, easiest first)

1. Fix `level_number`'s type hint (`str` → `int`) in `data_loader.py`.
2. Remove the dead `start_idx` in `map_animation.py` and the unused loop variable `i` in `animation_exporter.py`.
3. Delete the commented-out level-selection block in `sidebar.py` (still pending from the first review).
4. Fix the two comma/colon spacing nits (`about.py`, `sidebar.py`'s `TEMP_DIR`).
5. Fix the stale comment in `map_builder.py`'s `add_grid_labels` and the stale `Returns:` docstring in `map_config.py`.
6. Reorder `home.py`'s column unpacking to match its usage order (or rename to make the mismatch impossible to miss).
7. Decide on `firestore_client.py`: either update its docstring to acknowledge the Streamlit-secrets exception, or move that concern out of the module to keep the "pure Python" claim true.
