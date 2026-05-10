# Context

- uv based python app
- cli (non interaactive), and TUI versions + streamlit WebUI version too
- modular (not monolythic)
- make use of daatclass o pydantic classes
- persistence: save all in data.yaml file
- implement test, aim for 75% test coverage
- always ruff checks (you can use ruff check --fix) and ruff format

folders:
- source in src/
- tests in test/
- documentation in docs/

We can use for example:
from skyfield.api import Loader, wgs84, Star
from streamlit_folium import st_folium

Make a  README.md

Update AGENTS.md as necesarry with your key desicions, strategies,...


# Task

- make an  app that will pick a point on earth in the Atlantic ocean, a date time (during the day, dayligh conditions, so not night!) --> Real Position (Lat, Lon)
- error parameter, like 5 nmi
- pick a random point, Estimated position (DR), at error from real position, any random direction

- from Real Position, calculate the _real sextant reading_ for:

the Sun, Moon (if visible) (Lower Limb), and some stars (only visible ones)

NAVPAC_STAR_INDEX = {
    "Polaris": 0,
    "Vega": 49,
    "Sirius": 18,
    "Arcturus": 37,
    "Canopus": 17,
    "Rigel": 11,
    "Procyon": 20,
    "Betelgeuse": 16,
    "Altair": 51,
    "Aldebaran": 10,
    "Deneb": 53,
    "Fomalhaut": 56,
    "Regulus": 26,
    "Antares": 42,
}

RADIOS_CUERPOS_KM = {
    "Sol": 695700.0,
    "Luna": 1737.4,
}

assume He Height of Eye= 10 ft

Angles and positions stored as float, entered as DD.MMSS or DD.MMmm (handle conversion to/from float). Always represented as float, DD.MMSS and DD.MMmm.


For each reading, now, think as a navigator, we believe we are at estimated position, and take 3 of these these body sights reading and do sight reduction: Using almanach, calculate Alpha (nmi A/T away/Towards) and Azimuth Zn.

Now with 3 sight reductions (or n>1), implement a solve_fix_least_squares that will calculate a FIX position using the least_squares method and return a FIX position

Tell the error in nmi from Fix to real position.

the Streamlit app can show all the data, several st.dataframes with all the data, and represent a map with the LOPs, Real position, Estimated position, and FIX, and show error measure in nmi

