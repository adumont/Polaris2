# Polaris2 — Expert Code Review

**Project:** Celestial navigation scenario generator and sight reduction simulator
**Reviewed:** 2026-05-11
**Scope:** All source files, tests, config, docs

---

## Overall Assessment

Well-structured, modular Python project with good separation of concerns, consistent patterns, and solid test coverage. The celestial navigation domain logic is sound. 24 findings below, ordered by severity.

---

## CRITICAL

### 1. `SextantReading.ho` does not include dip + SD corrections

**File:** `src/polaris2/core/sight.py:29-38`

```python
apparent_alt, _ = body_alt_az(body_name, dt, real_pos)
corr = dip_correction(he_ft)
if body_name in ("Sun", "Moon"):
    corr += semidiameter_deg(body_name)
return SextantReading(
    body_name=body_name,
    ho=apparent_alt,       # BUG: should be apparent_alt + corr
    ...
    correction_total=corr,
)
```

`ho` is set to raw `apparent_alt` from Skyfield; dip and SD are computed but never added. Per the README and AGENTS.md, `Ho = apparent_alt + dip + SD`. All downstream intercepts are wrong.

**Fix:** `ho=apparent_alt + corr`

### 2. `solve_fix_least_squares` uses wrong `ho` through the pipeline

**File:** `src/polaris2/core/reduction.py:47-54`

The LSQ solver iteratively recomputes `Hc` at the current estimated position, but uses `SightReduction.ho` stored from the real-position calculation. Since `ho` lacks dip+SD (bug #1), intercepts are doubly wrong.

**Fix:** Fix bug #1 first; verify LSQ receives corrected `ho`.

### 3. `compute_fix_error` mutates input and returns it

**File:** `src/polaris2/core/reduction.py:90-99`

```python
def compute_fix_error(fix: Fix, real_pos: Position) -> Fix:
    ...
    fix.error_nmi = c * 3440.065
    return fix
```

Mutates the passed-in `Fix` object as a side effect. Callers (`recompute_fix`) also use the return value, creating ambiguity. If a caller reuses a `Fix` object, the error field is silently overwritten.

**Fix:** Either mutate in-place and return `None`, or create a new `Fix` with the error set. Pick one pattern and stick to it.

---

## HIGH

### 4. DR error fallback uses uninitialized values

**File:** `src/polaris2/cli/app.py:61-66`

```python
for _attempt in range(20):
    dt, real_pos = random_daylight_datetime()
    dr = dr_position(real_pos, error_nmi)
    bodies = _select_best_bodies(dt, real_pos)
    if len(bodies) >= _MIN_BODIES_TARGET:
        break
```

If all 20 attempts fail (very unlikely but possible), `dt`, `real_pos`, `dr`, `bodies` are from the *last* failed attempt. Execution continues with <3 bodies and no explicit fallback.

**Fix:** Add an `else` clause after the loop with a hard fallback.

### 5. Duplicate Skyfield loader in `scenario.py` and `almanac.py`

Both files independently create:
```python
_CACHE_DIR = Path.home() / ".polaris2" / "skyfield"
_LOAD = Loader(str(_CACHE_DIR))
_EPHEMERIS = _LOAD("de421.bsp")
_TS = _LOAD.timescale()
_EARTH = _EPHEMERIS["earth"]
```

Ephemeris is loaded twice — wastes memory, slows startup. Stars are only loaded in `almanac.py`.

**Fix:** Create a shared `src/polaris2/core/ephemeris.py` that all modules import from.

### 6. Global mutable state for star cache

**File:** `src/polaris2/core/almanac.py:17`

```python
_STARS = None

def _get_stars():
    global _STARS
    if _STARS is None:
        ...
```

Module-level mutable state leaks between tests and is not thread-safe. Test at `test_almanac.py:13-17` works around it by monkeypatching `almanac._STARS` directly.

**Fix:** Use `functools.cache` or a class-level cache.

### 7. Import-time side effects (disk I/O, ephemeris loading)

**File:** `src/polaris2/core/scenario.py:10-15`, `src/polaris2/core/almanac.py:11-16`

Creating directories and loading ephemerides at **import time** violates the principle of least surprise. Running `import polaris2` writes to `~/.polaris2/skyfield/`.

**Fix:** Lazy initialization — load Skyfield resources on first use, not on import.

---

## MEDIUM

### 8. `body_alt_az` catches all exceptions silently

**File:** `src/polaris2/core/almanac.py:73`

```python
except Exception:
    pass
```

Makes debugging hard if a Skyfield API change or data issue arises.

**Fix:** Log the exception at minimum (`import logging`).

### 9. `_select_best_bodies` fallback complexity

**File:** `src/polaris2/cli/app.py:40-51`

The fallback from "best range" (30-60°) to extras uses set comprehensions to filter already-selected bodies. More readable as a single pass with priority scoring.

### 10. Hardcoded year 2026

**File:** `src/polaris2/core/scenario.py:35`

```python
base = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day - 1)
```

Creates a ticking time-bomb. Ephemeris `de421.bsp` covers ~1900-2050 so 2026 works, but should use `datetime.now().year` or be configurable.

### 11. Magic numbers duplicated and scattered

- `3440.065` (earth radius in nmi) appears in `scenario.py:49` and `reduction.py:98`
- `_MIN_BODIES = 2` in `reduction.py:9` but also `_MIN_BODIES_FOR_FIX = 2`, `_MIN_BODIES_TARGET = 3`, `_MAX_SELECT = 4` in `cli/app.py`
- `0.97` dip coefficient in `sight.py:10`
- Sun/Moon distances in `sight.py:18`

**Fix:** Centralize all constants in `config.py`.

### 12. `parse_angle` heuristic is fragile

**File:** `src/polaris2/utils/angles.py:50`

```python
if rest > 100.0:  # noqa: PLR2004
    return ddmmss_to_deg(value)
else:
    return ddmmmm_to_deg(value)
```

Could misclassify ambiguous values like `451059.0` (45°10'59" vs 45°10.59').

### 13. `_draw_lop` duplicates intercept position logic from `solve_fix_single`

**File:** `src/polaris2/webui/app.py:38-59`

The LOP line drawing recalculates the intercept position from scratch, duplicating the math in `solve_fix_single`. A shared helper would be cleaner.

### 14. No type annotations on `_get_stars`, `_skyfield_star` return types

**File:** `src/polaris2/core/almanac.py:20-32`

Skyfield's `Star` type is not annotated.

### 15. `_launcher.py` mutates `sys.argv`

**File:** `src/polaris2/webui/_launcher.py:9`

```python
sys.argv = ["streamlit", "run", str(app)]
```

Necessary for Streamlit but modifies global interpreter state. Should be documented with a comment.

### 16. `format_angle` default `fmt="dms"` is duplicated

Default appears in `format_angle` and `format_position`. Minor but inconsistent if changed in only one place.

---

## LOW

### 17. No `conftest.py` — 16 test files with no shared fixtures

Each test file that needs a datetime or position creates its own. A `conftest.py` with `@pytest.fixture` for `sample_dt`, `sample_scenario`, `sample_position` would reduce duplication.

### 18. `test_angles_edge.py` is only 12 lines — merge into `test_angles.py`

### 19. Tested private function `_select_best_bodies` via direct import

The underscore conventionally marks it private, but `test_cli_select.py` imports and tests it directly. Either make it public or test through `run_scenario`.

### 20. `test_webui.py` and `test_cli_main.py` spawn real subprocesses for main-guard tests

Spawn a new Python interpreter — slow and fragile. Consider using `AppTest` or `monkeypatch` instead.

### 21. No tests for `_draw_lop` in webui or `plot_chart` LOP/compass rendering details

Only existence-tested (returns a figure). Edge cases like empty selected bodies, single-body compass rose not covered.

### 22. `compute_fix_error` uses literal `3440.065` — should be named constant from `config.py`

### 23. Test class `TestSelectBestBodies` tests `_select_best_bodies` — naming mismatch with underscore prefix

### 24. `test_webui.py:test_main_guard_via_subprocess` imports `main` but only checks `print('ok')` — weak assertion

Only verifies the import doesn't crash, not that `main()` runs correctly.

---

## Test Coverage Analysis

| Metric | Value |
|--------|-------|
| Test files | 16 |
| Test code lines | ~2100 |
| Source code lines | ~700 |
| Ratio | 3:1 (good) |
| Every model tested | ✓ |
| Every public function has ≥1 test | ✓ |
| Edge cases covered | ✓ |
| Streamlit `AppTest` | ✓ |
| TUI headless test | ✓ |

**Gaps:**
- `plot_chart` LOP/compass rendering details (only existence-tested)
- `_draw_lop` in webui (not tested)
- Interactive CLI selection loop (not tested)
- `_sun_above_horizon` (not tested directly — tested through `random_daylight_datetime` fallback)

---

## Architecture Observations

**Strengths:**
- Clean modular layering: `config` → `models` → `utils` → `core` → `cli/tui/webui`
- Domain logic isolated in `core/` — no UI concerns leak in
- Pydantic models validate data at every boundary
- YAML persistence enables reproducibility
- No circular dependencies

**Weaknesses:**
- Duplicate Skyfield initialization (2 modules)
- Import-time side effects (ephemeris loading, directory creation)
- Global mutable state for star cache
- Missing shared constants (`EARTH_RADIUS_NMI`, etc.)
- `SextantReading.ho` missing dip/SD corrections (bug #1)
