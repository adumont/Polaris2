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

# Architecture

src/polaris2/
├── config.py        # Constants: NAVPAC star index, body radii, bounds, defaults
├── models.py        # Pydantic: Position, SextantReading, SightReduction, Fix, Scenario
├── utils/
│   ├── angles.py    # DD.MMSS <-> DD.MMmm <-> float deg conversions
│   └── io.py        # YAML save/load for Scenario
├── core/
│   ├── scenario.py  # Random Atlantic pos, daylight datetime, DR at error
│   ├── almanac.py   # Skyfield: body alt/az via observer=earth+latlon
│   ├── sight.py     # Hs = raw sextant alt + dip + SD → Ho = Skyfield geometric alt
│   └── reduction.py # Hc, Zn, intercept=Ho-Hc, iterative LSQ fix
├── cli/
│   └── app.py       # argparse entry point
├── tui/             # placeholder
└── webui/
    └── app.py       # Streamlit: dataframes + folium map

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
