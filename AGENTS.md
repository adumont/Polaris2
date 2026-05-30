# Context

- uv based python app, never bare `python`, always via `uv run`
- cli + TUI (textual) + Streamlit WebUI
- modular, not monolithic
- Pydantic models for all data
- YAML persistence (data.yaml)
- Test before handover
    - maintain existing tests, add new as needed
- Maintain README.md, AGENTS.md
- Language: only english!

## Testing and Code Quality

- pytest in tests/
- ruff for lint+format (run: `uv run ruff check --fix .` and `uv run ruff format`)
    - fix all errors, aim 0
- Coverage: min 90% overall, 80% per file. No exclusions in pyproject.toml.
- Run: `uv run pytest tests/ -v`
- Streamlit tests via AppTest

## Working on issue

Diagnose, prove cause. Fix, prove fixed.

## Commit

- Clean commit, single line (small) or multiline (massive)
- Never `git add .`, only touched files
- Never `--no-ff` on merges — fast-forward only

# Related projects

- **celnav-core** (sibling C:\Projects\celnav-core) — shared celestial nav library
  - config, models, ephemeris, almanac, sight, reduction, cartography, angles
  - Added via `[tool.uv.sources]` path dep in pyproject.toml
- **navpac-simulator** (future) — sibling app consuming celnav-core

# Deps

- Editable install: `uv sync` resolves celnav-core from local path

# Architecture

src/polaris2/
├── utils/
│   └── io.py        # YAML save/load for Scenario
├── core/
│   └── scenario.py  # Random Atlantic pos, daylight datetime, DR at error
├── cli/
│   └── app.py       # argparse entry point
├── tui/
│   └── app.py       # Textual TUI (placeholder)
└── webui/
    └── app.py       # Streamlit: dataframes + folium map

Core nav logic lives in **celnav-core** (import as `celnav_core.*`).

# Key decisions

- Skyfield 1.54 API: body.observe() requires observer = EARTH + wgs84.latlon()
- `body_alt_az(apparent=True)` passes `temperature_C=10, pressure_mbar=1010` — altitude WITH standard refraction
- `body_alt_az(apparent=False)` passes `temperature_C=10, pressure_mbar=0` — geometric altitude (no refraction)
- Ho = Skyfield geometric alt (center, no refraction) = same for ALL bodies
- Hc = Skyfield geometric alt at DR position (same `apparent=False` convention as Ho)
- For Sun/Moon: `hs = apparent_alt - dip - sd` = lower limb sextant reading
- For planets/stars: `hs = apparent_alt - dip` = center sextant reading (sd=0)
- `correction_total = dip + (geometric - apparent) + sd` = traditional Hs→Ho correction. Always satisfies `hs + corr = ho`
- Time display MUST show seconds (`%H:%M:%S Z`) in ALL UIs — random seconds in scenario generation cause 13"/sec altitude drift
- intercept = Ho - Hc (nmi). Positive = Toward body (in Zn direction)
- LSQ solver: A = [cos(Zn), sin(Zn)], b = intercept. Iterative with recomputed Hc
- Best bodies: 30-60 deg altitude range, fall back to lower/upper, min 2 bodies
- Sun + Moon primary daytime bodies; stars rarely visible in daylight
- Fix error via haversine formula, nautical miles
