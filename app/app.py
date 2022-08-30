# After installing OREKIT via 'conda install -c conda-forge orekit',
# put the 'orekit.zip' data file into the project folder

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
from propagate_orekit import generate_predicts
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

    plt_lst = generate_skyfield_predicts(tle, station, days, sc_name)
    print("- Done!")

    args = ["plots.tpl", locations_dict.keys(), spacecraft_dict.keys(), plt_lst]
    return template("main_view.tpl", content=args)


@route("/generating")
def generating():
    """ Simple waiting page with spinner while propagation takes place. Will flesh this out with Alpine"""
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
    """Logs into spacetrack.org and downloads the latest TLE based on the input NORAD ID"""
    cred_file = 'spacetrack_login.txt'
    uri_base = "https://www.space-track.org"
    request_login = "/ajaxauth/login"

    # Fetch login credentials:
    with open(cred_file, 'r') as f:
        creds = f.readlines()
    site_cred = {'identity': creds[0].strip(), 'password': creds[1].strip()}

    # The API below is set to return a '3le': First line label, followed by TLE lines
    api_url = f"https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/{norad_id}/" \
              f"orderby/OBJECT_ID asc/limit/2/format/3le/emptyresult/show"

    with requests.Session() as session:
        # Log in:
        resp = session.post(uri_base + request_login, data=site_cred)

        # Request TLE:
        resp = session.get(api_url)
        resp = resp.text.split('\n')
        tle = [resp[0].strip(), resp[1].strip(), resp[2].strip()]
        print(f'- Found TLE for {resp[0].strip()}')
        session.close()
    return tle


if __name__ == "__main__":
    # --- Settings ---
    # Dev or production?
    # - If true, runs reloader, which watches for file changes and restarts the server, plus debug messages
    # dev = True
    dev = False

    app = Bottle()
    # app.run(host='localhost', port=8080)

    debug(dev)
    run(
        reloader=dev
    )  # watches for file changes, so server restarts not required in dev
