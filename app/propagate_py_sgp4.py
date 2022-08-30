"""
Propagate TLE with skyfield library and return Az/El
"""

from math import radians, pi
from skyfield.api import EarthSatellite
from skyfield.api import load, wgs84
from skyfield.api import N, S, E, W
from skyfield.api import utc, Time
import pandas as pd
import matplotlib.pyplot as plt
import time

# import plotly.express as px
from datetime import datetime, timedelta


def generate_skyfield_predicts(tle: list, station: dict, days: float, sc: str) -> list:
    # Set pandas to not warn about chained assignment, it's ok in this case which it cannot discern
    pd.options.mode.chained_assignment = None  # default='warn'

    # Time array: from now until n days at 1 sec intervals
    secs = int(days * 24 * 60 * 60)     # total seconds in propagation interval
    step_sec = 1.0                      # time step size
    now = datetime.utcnow()
    now = now.replace(microsecond=0).replace(tzinfo=utc)  # utc obj is from skyfield, but could also use datetime.timezone.utc
    
    # Set min elevation to filter out useless passes
    min_el = 5.0  # degrees

    # Set up station:
    station_sf = wgs84.latlon(station["coords"][0] * N, station["coords"][1] * E)

    # Set up Skyfield sat-object from TLE
    ts = load.timescale()
    satellite = EarthSatellite(tle[1], tle[2], tle[0], ts)

    # Build station to sat vector object which will be propagated via time-steps
    stn_to_sat_vec = satellite - station_sf

    print('- Starting propagation...')

    # Create list of timescale objects which will seed a dataframe for data:
    datetimes = [(now + timedelta(seconds=t)) for t in range(secs + 1)]
    timescales = ts.from_datetimes(datetimes)

    # Set up dataframe with time-series and fill columns with vectorized functions:
    prop_data = pd.DataFrame(datetimes, columns=['datetime'])

    # - get list of sat-stn vectors at time instances. This is essentially the propagator
    topo_list = stn_to_sat_vec.at(timescales)

    # - convert to elevations, azimuths:
    el, az, dist = topo_list.altaz()
    prop_data['el_deg'] = el.degrees
    prop_data['az_deg'] = az.degrees

    # Visibility filter: Cut everything that is below threshold
    # - add True/False map-column
    visible_data = prop_data[prop_data["el_deg"] > min_el]
    # - filter out the False
    if visible_data.shape[0] == 0:
        print("- No passes in the specified time range!")
        return ["*** No passes in the specified time range! ***"]

    visible_data.reset_index(inplace=True)

    # Find and label passes in the main dataframe:
    visible_data["time_delta"] = visible_data["datetime"].diff().dt.total_seconds()
    pass_start_indices = visible_data[visible_data["time_delta"] > step_sec].index
    if len(pass_start_indices) == 0:
        # then there is only one pass
        pass_start_indices = [visible_data.shape[0] - 1]

    # Plot: Use PANDAS package for plotting, based on matplotlib
    start_idx = 0
    font_sz = 10
    plt.style.use("dark_background")
    plt_lst = []

    print(f"- Creating {len(pass_start_indices)} plots")
    for idx, flyby in enumerate(pass_start_indices):
        if idx != 0:
            start_idx = pass_start_indices[idx - 1]
        plt.rc("font", size=font_sz)  # controls default text sizes


        # Make the plot. Below returns a matplotlib.axes.AxesSubplot object
        pass_data = visible_data.iloc[start_idx:flyby]
        pass_data.plot(
            x="az_deg",
            y="el_deg",
            style=".",
            figsize=(7, 5),
            legend=False,
            title=f'{sc} from {station["name"]}: Pass {idx + 1}',
            fontsize=font_sz,
            zorder=0,
            ms=2,               # marker size
        )

        xtic_locs = [0, 90, 180, 270, 360]
        xtic_labels = ["North", "East", "South", "West", "North"]
        plt.xticks(xtic_locs, xtic_labels)
        plt.ylabel("Elevation (deg)")
        plt.xlabel("Azimuth")
        plt.ylim(0, 90)
        plt.xlim(0, 360)
        plt.rc("font", size=font_sz)  # controls default text sizes

        # Set up Start/End text box:
        start_time = pass_data["datetime"].iloc[0].replace(tzinfo=None)
        end_time = pass_data["datetime"].iloc[-1].replace(tzinfo=None)
        txt_str = f'Start: {start_time}    |    End: {end_time} UTC'

        # - these are matplotlib.patch.Patch properties
        bbox_props = dict(boxstyle="round", facecolor="white", alpha=0.5)
        plt.text(
            plt.xlim()[1] * 0.08,
            plt.ylim()[1] * 0.92,
            txt_str,
            fontsize=font_sz,
            bbox=bbox_props,
        )

        # Add direction arrow:
        # - arrow tail coords:
        arrow_y = pass_data["el_deg"].max()
        arrow_tail_x = pass_data[pass_data["el_deg"] == arrow_y]["az_deg"].item()

        # - arrow dir:
        arrow_x_idx = pass_data["el_deg"].idxmax()
        if arrow_x_idx != 0:
            sign = (
                arrow_tail_x - pass_data.loc[arrow_x_idx - 1]["az_deg"]
            )  # if sign +ve, arrow ->, else <-
        else:
            # Pass has started AT the max elevation at the beginning of propagation
            sign = (
                pass_data.loc[arrow_x_idx + 1]["az_deg"] - arrow_tail_x
            )  # if sign +ve, arrow ->, else <-

        # - arrow head coords:
        arr_len = 10 * (sign / abs(sign))
        arr_width = 1.0
        plt.arrow(
            arrow_tail_x,
            arrow_y,
            arr_len,
            0,
            overhang=0.3,
            width=arr_width,
            head_width=4 * arr_width,
            color="white",
        )

        # Make plot files
        plt_path = f".\\static\\plots_temp\\plt_{idx}.png"
        plt.savefig(plt_path)

        # Format the relative path relative to template that will display it, eg. './plots_temp/<img>'
        plt_name = plt_path.split("\\static\\", 1)[-1]
        plt_lst.append(plt_name)

    plt.close("all")
    print(f"plt_lst from propagate: {plt_lst}")
    return plt_lst
