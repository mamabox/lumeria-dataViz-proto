# Code Review: streamlit_app/

Reviewed all 23 files (~2,600 lines) against `CODE_REVIEW_BRIEF.md` priorities. Review only — no changes made to the codebase.

## 1. Summary

The architecture (modules/views/components split) is followed reasonably well and most functions have docstrings and clear names — a solid foundation for a learning project. The main problems are (a) near-total duplication between the two video export modules, (b) one function living in the wrong module, (c) silent failure paths around `cv2`/`subprocess`, and (d) a couple of real bugs (not just style) hiding in view files that would surface the next time those code paths run.

## 2. Duplicates found

| # | Duplicate | Locations | Fix |
|---|---|---|---|
| 1 | `_render_map_to_array`, `_find_frame_index`, `_make_even`, `_get_video_frame` — byte-identical | `modules/video_exporter.py:35-64` vs `modules/video_exporter_pipe.py:29-58` | Extract into a shared `video_export_common.py`; both modules import from it. Only the ffmpeg invocation (temp-files vs pipe) should actually differ. |
| 2 | Main per-frame compositing loop (map caching, video fetch/resize, hstack/pad/crop) — near-identical ~40 lines | `modules/video_exporter.py:118-161` vs `modules/video_exporter_pipe.py:140-174` | Same as above — this is the bulk of both files. A shared generator that yields the composited frame could feed either the PNG-writer or the pipe-writer. |
| 3 | Trail trace styling built twice instead of reused | `modules/map_builder.py:128-139` (`add_trail`) vs `modules/map_animation.py:64-74` (inline in `add_animated_traces`) | Have `map_animation.py` call `map_builder.add_trail(fig, timeline_df)` instead of re-declaring the same `go.Scatter`. |
| 4 | "assemble `loaded_data` dict" shape hand-rolled 3 times | `components/sidebar.py:106-114` vs `views/firestore_test.py:120-128` | Extract a `build_loaded_data(...)` helper (likely in `data_loader.py`) so the dict shape only exists in one place. |
| 5 | "nearest index before time" reimplemented as manual loops instead of reusing `get_nearest_index_for_time` | `modules/data_loader.py:126-136` (canonical) vs `views/video_sync.py:113-120` (`on_time_jump`) and `views/video_sync.py:146-151` (slider lookup) | Both view-layer loops should call the existing module function. |
| 6 | Literal duplicate import line | `views/firestore_test.py:4-5` — `from modules.map_config import get_map_config, LEVELS` twice | Delete one. |
| 7 | Redundant re-imports of already-imported names inside function bodies | `modules/data_export.py:51-53` (cv2, numpy, go), `modules/map_animation.py:234` (go), `modules/map_builder.py:267` (EVENT_STYLES, ATTEMPT_COLORS) | Remove — all already imported at module top. |

`get_frame_snapshot` itself is correctly single-sourced in `map_animation.py`, per the brief's suspicion — that one's clean.

## 3. Separation issues

- **`export_animation_to_mp4` is in the wrong file.** `modules/data_export.py` is documented as "Export dataframes to downloadable formats," but this function (`data_export.py:40-85`) does video composition with `cv2.VideoWriter` — conceptually a sibling of `video_exporter.py`, not `dataframe_to_csv_bytes`. Move it to its own module (e.g. `animation_exporter.py`) or into `video_exporter.py`.
- **`components/sidebar.py` is doing module-level work.** `sidebar.py:97-118` orchestrates data loading, computes `target_building_id`, and manages a fairly involved session-state cache — that's app/data logic, not sidebar rendering. Per the brief's own architecture rules ("components = reusable Streamlit components"), this should be split: sidebar renders widgets and returns raw paths; a module function (e.g. `load_session_data(paths, map_config)`) builds the `loaded_data` dict. This would also fix duplicate #4 above.
- **`views/video_sync.py` reimplements lookup logic that belongs in `data_loader.py`** (duplicate #5) — a view should call modules, not recompute the same nearest-index search inline.
- **`views/video_sync.py` contains two full, overlapping export UIs** (`video_sync.py:172-202` and `video_sync.py:205-263`) — looks like leftover A/B comparison scaffolding (matches `video_exporter_pipe.py`'s stated "comparison" purpose) left in a page real users will see. Worth deciding: keep the PNG-vs-pipe comparison and delete the single "Export video" button, or vice versa.

## 4. File-by-file notes

### `modules/video_exporter.py` / `video_exporter_pipe.py`
- ~90% duplicated (see duplicates #1-2).
- `cv2.VideoCapture(video_path)` result is never checked with `.isOpened()` (`video_exporter.py:101`, `video_exporter_pipe.py:95`). If the video fails to open, `video_fps` is `0.0`, `_get_video_frame` computes `frame_index = int((t+offset)*0)` and `total = 0`, so the bounds check `frame_index >= total` is always true → every frame silently comes back `None` (renders as black frames) instead of raising a clear error. This is exactly the "silent failure" the brief calls out.
- `subprocess.run(..., stderr=subprocess.DEVNULL, check=True)` (`video_exporter.py:166-180`) discards ffmpeg's error output, so a `CalledProcessError` on failure carries no useful message.
- `video_exporter_pipe.py`'s `Popen` (`video_exporter_pipe.py:128-133`) also sends `stderr=DEVNULL` and never checks `proc.returncode` after `.wait()` — if ffmpeg dies mid-stream, the function returns as if it succeeded.

### `modules/data_loader.py`
- Clean, well-documented, no Streamlit imports — good adherence to the architecture.
- No error handling around `json.load` or the many `data["key"]` accesses (`data_loader.py:21-24` etc.) — a malformed uploaded JSON file (from the sidebar uploader) will raise a raw `KeyError`/`JSONDecodeError` with no `st.error` anywhere in the call chain, crashing the page with a Streamlit traceback.

### `components/sidebar.py`
- `_save_upload` (`sidebar.py:123-133`) writes to a relative `"temp_uploads"` path, inconsistent with the rest of the file which carefully resolves `_BASE_DIR` for every other path — uploads will land wherever Streamlit's current working directory happens to be, not `streamlit_app/temp_uploads`.
- See separation issue above re: data-loading logic embedded here.

### `views/video_sync.py`
- `OUTPUT_PATH` (`video_sync.py:175`) and `OUTPUT_PATH_PNG` (`video_sync.py:205`) are both `"/tmp/lumeria_combined.mp4"` — the same file. The first "Export video" button and the second row's "Export (PNG method)" button silently overwrite each other's output.
- The export `try/except` blocks (`video_sync.py:184-196`, `video_sync.py:215-230`) are the *only* place in the codebase with proper user-facing error handling — worth using as the template elsewhere.

### `views/animated_map.py`
- **Bug:** `video_bytes` is assigned only inside `if st.button("🎬 Export MP4"):` (`animated_map.py:50-54`), then read again in the separate `if "exported_video" in st.session_state:` block (`animated_map.py:56-62`). Once the download button has been rendered from a past run without the export button being clicked again on this run, `video_bytes` won't exist → `NameError`. Fix: use `st.session_state["exported_video"]` directly in the download button.
- Indentation is inconsistent inside that same block — 2-space then 3-space nesting instead of the file's 4-space convention (`animated_map.py:50-54`), a readability regression versus the rest of the codebase.
- `export_animation_to_mp4(fig, fps=export_fps)` has no try/except — an export failure here crashes the page (contrast with `video_sync.py`'s pattern).

### `views/firestore_test.py`
- Duplicate import line (`firestore_test.py:4-5`).
- `get_firestore_client(CREDS_PATH)` runs unguarded at module scope (`firestore_test.py:30`) — a missing/invalid credentials file crashes the whole page with a raw traceback rather than a friendly message.
- Duplicates the `loaded_data` dict-building logic from `sidebar.py` (see duplicates #4).
- Two commented-out `st.subheader(...)` lines (`firestore_test.py:47`, `firestore_test.py:61`) — dead code, should be removed or restored.

### `modules/map_animation.py` / `map_builder.py`
- Well organized with clear section header comments; good docstrings throughout.
- `map_animation.py`'s `get_frame_snapshot` re-imports `plotly.graph_objects as go` locally despite the module-level import — harmless but redundant.
- `map_builder.py`'s `build_event_timeline` locally re-imports names already imported at module top — same note.

### `modules/data_export.py`
- `export_animation_to_mp4`'s misplacement noted above; also has the same 3 redundant inline imports.
- No error handling around `cv2.VideoWriter` — if it fails to open (e.g. codec unavailable), `writer.write(img)` calls will silently no-op and produce an empty/corrupt file with no exception raised — another instance of the brief's flagged "silent failure" pattern.

### `modules/firestore_client.py`, `map_config.py`, `map_styles.py`, `video_player.py`, `components/export.py`
- These are the cleanest files in the codebase: single responsibility, no Streamlit imports where required, consistent docstrings, sensible constants. `VideoPlayer` in particular is a good model of frame-access error handling (`raise FileNotFoundError` if `cap.isOpened()` fails) — the video export modules should follow this same pattern instead of silently returning black/empty frames.

### `test_animation.py`, `test_export.py`, `test_map_builder.py`
- Not pytest tests — they're manual run-and-look scripts (call `.show()`, `print()`, no assertions) with hardcoded relative paths (`"defaults/example_game_data.json"`) that only work when run from `streamlit_app/`. Naming them `test_*.py` means pytest will try to collect them if anyone runs `pytest` over the repo, and collection will fail/error since they execute top-level code with paths relative to an assumed CWD. Recommend renaming (e.g. `manual_check_animation.py`) or moving to a `scripts/`/`examples/` folder, per the brief's naming-convention consistency ask.

## 5. Pattern review

**Good habits, worth reinforcing:**
- Docstrings are present on nearly every public module function, and most are genuinely explanatory (not just restating the signature).
- Style constants centralized in `map_styles.py` — exactly the "change once, updates everywhere" pattern the file's own docstring promises.
- `modules/` files mostly honor "no Streamlit imports" — verified none of them import `streamlit`.
- Section-header comments (`# ======== X ========`) make the larger files easy to navigate.

**Recurring bad habits:**
- **Copy-paste-first instinct for variants.** `video_exporter_pipe.py` was built by duplicating `video_exporter.py` wholesale rather than factoring out the shared 80%. Given the module's own docstring calls it "the pipe method (comparison)," this was likely deliberate for benchmarking, but it should be cleaned up once the comparison is settled.
- **Silent failure around external processes (cv2, ffmpeg).** This shows up in 3 separate places (video exporters, `data_export.py`'s VideoWriter) — worth a single fix pass rather than three.
- **View files sometimes re-deriving logic that already exists in a module** rather than importing it (`video_sync.py`'s nearest-time search, `firestore_test.py`'s data-dict assembly). This is the main architecture violation to watch for going forward.

## 6. Suggested refactors (prioritized, easiest first)

1. **Delete the duplicate import line** in `firestore_test.py` — 1-line fix.
2. **Fix the `video_bytes` NameError** in `animated_map.py` — use `st.session_state["exported_video"]` consistently; also fix the indentation there.
3. **Fix the `OUTPUT_PATH`/`OUTPUT_PATH_PNG` collision** in `video_sync.py`, and decide whether to keep both export UIs or just one.
4. **Remove the 3 redundant in-function re-imports** (`data_export.py`, `map_animation.py`, `map_builder.py`).
5. **Extract shared helpers from the two video exporters** into a common module — biggest duplication win, moderate effort since it touches both files carefully.
6. **Move `export_animation_to_mp4` out of `data_export.py`** into a video-focused module.
7. **Add `.isOpened()` checks and surface ffmpeg stderr** in both video exporters instead of swallowing failures.
8. **Extract a shared `build_loaded_data(...)` helper** used by both `sidebar.py` and `firestore_test.py`, and have `video_sync.py` call `get_nearest_index_for_time` instead of its two hand-rolled loops.
9. **Rename or relocate the `test_*.py` scripts** so pytest doesn't try (and fail) to collect them.
