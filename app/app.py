# The main app. Contains routes, smaller functions, and starts the server.
# - This app will present a UI in the browser to configure satellite flyby predicts for a location
# and specific satellite.
# - A 'generate' button will then call either a propagator from the OREKIT or Skyfield astrodynamics
# libraries, and the data will be plotted. The plots will appear on the main UI page below the inputs

import bottle
from bottle import (
    redirect,
    route,
    run,
    template,
    Bottle,
    get,
    request,
    static_file,
    debug,
    post,
)
from propagate_py_sgp4 import generate_skyfield_predicts
import requests

# Set up spacecraft and viewing location options:
# - lat/lon degs E
locations_dict = {
    "Karachi": [24.86, 67.01],
    "Lisbon": [38.736, -9.1426],
    "Ottawa": [45.334904, -75.724098],
    "San Francisco": [37.77, -122.431],
}

spacecraft_dict = {
    "International Space Station (USA)": 25544,
    "Tiangong (China)": 48274,
}


# --- Routes ---
@route("/")
def home():
    args = ["splash.tpl", locations_dict.keys(), spacecraft_dict.keys()]
    return template("main_view.tpl", content=args)


@get("/generate")
def generate():
    request_params = request.params.dict

    location = request_params["location"][0]
    station = {"name": location, "coords": locations_dict[location]}
    sc_name = request_params["spacecraft"][0]

    # Fetch TLE from spacetrack
    tle = fetch_tle(spacecraft_dict[sc_name])
    days = float(request_params["duration"][0])

    # Here is where you can toggle between propagation with Skyfield or OREKIT
    # - OREKIT:
    #   from propagate_orekit import generate_orekit_predicts
    #   plt_lst = generate_orekit_predicts(tle, station, days, sc_name)
    # - Skyfield:
    #   from propagate_py_sgp4 import generate_skyfield_predicts
    #   plt_lst = generate_skyfield_predicts(tle, station, days, sc_name)
    plt_lst = generate_skyfield_predicts(tle, station, days, sc_name)
    print("- Done!")

    args = ["plots.tpl", locations_dict.keys(), spacecraft_dict.keys(), plt_lst]
    return template("main_view.tpl", content=args)


@route("/generating")
def generating():
    """Simple waiting page with spinner while propagation takes place. Will flesh this out with Alpine"""
    args = ["spin.tpl", locations_dict.keys(), spacecraft_dict.keys()]
    return template("main_view.tpl", content=args)


# set up path to static files and artifacts. This allows for relative path to static
@route("<filepath:path>")
def server_static(filepath):
    """This function points relative paths to a certain directory. Allows for the following links to css, js, etc.:
    <link href="/assets/fonts/bootstrap-icons.css" rel="stylesheet">
    <link href="/assets/css/bootstrap.min.css" rel="stylesheet">
    <script src="/assets/javascript/bootstrap.bundle.min.js"></script>
    """
    return static_file(filepath, root="./static")


# --- End Routes ---


def fetch_tle(norad_id: str) -> list:
    with requests.Session() as session:
        # Make request to celestrak:
        # - this actually returns a 3LE, not a TLE
        api_url = (
            f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
        )

        # Request TLE:
        resp = session.get(api_url)
        resp = resp.text.split("\n")
        tle = [resp[0].strip(), resp[1].strip(), resp[2].strip()]
        print(f"- Found TLE for {resp[0].strip()}")
        session.close()
    return tle


# --- Settings ---
# Dev or production?
# - If true, runs reloader, which watches for file changes and restarts the server, plus debug messages
# dev = True
dev = False
if dev:
    debug(dev)


# Start the app: This should NOT be in a 'if __main__' section for production since the 'app' needs to be
# imported by the WGSI config file
# app = Bottle()
app = bottle.default_app()


# Production vs local dev: production env will have a dummy 'production.py' file
try:
    import production
except:
    # Below should NOT run in production
    # app.run(host='localhost', port=8080)  # use this to configure custom IP for local hosting. Optional line
    run(
        reloader=dev
    )  # watches for file changes, so server restarts not required in dev
