# Context

- uv based python app
- cli + TUI (textual) + Streamlit WebUI
- modular, not monolithic
- Pydantic models for all data
- YAML persistence (data.yaml)
- Always test before you hand over your code as finished
    - when adding/modifying code, maintain existing tests and/or add new tests as needed
- Maintain the README.md (create if not there)
- Maintain the AGENTS.md

- Language: only english!

## Testing and Code Quality

- pytest in tests/
- ruff for lint+format (run: `uv run ruff check --fix .` and `uv run ruff format`)
    - fix all error even minor. we aim a 0 error. don't ignore
- Test Coverage target: minimum 90%
- Run: `uv run pytest tests/ -v`
- Cover streamlit tests using AppTest

## Commit

- Clean commit, can be single line (small commits) or multiline (when it's a massive change)
- Never do a "git add .", add only the files you have touched!

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
│   ├── sight.py     # Ho = apparent_alt + dip + SD (no double refraction)
│   └── reduction.py # Hc, Zn, intercept=Ho-Hc, iterative LSQ fix
├── cli/
│   └── app.py       # argparse entry point
├── tui/             # placeholder
└── webui/
    └── app.py       # Streamlit: dataframes + folium map

# Key decisions

- Skyfield 1.54 API: body.observe() requires observer = EARTH + wgs84.latlon()
- Ho: uses Skyfield's apparent alt (includes refraction) + dip + SD for Sun/Moon
- Hc: Skyfield apparent alt at DR position (no additional corrections)
- intercept = Ho - Hc (nmi). Positive = Toward body (in Zn direction)
- LSQ solver: A = [cos(Zn), sin(Zn)], b = intercept. Iterative with recomputed Hc
- Best bodies: 30-60 deg altitude range, fall back to lower/upper, min 2 bodies
- Sun + Moon are primary daytime bodies; stars rarely visible in daylight
- Fix error via haversine formula, in nautical miles

