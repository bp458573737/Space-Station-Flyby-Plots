"""
Propagate TLE with skyfield library and return Az/El
"""

from datetime import datetime, timedelta
from pathlib import Path
from skyfield.api import EarthSatellite
from skyfield.api import load, wgs84
from skyfield.api import N, E
from skyfield.api import utc
import pandas as pd
import matplotlib.pyplot as plt
import os


def clear_plt_folder():
    """Self-clearing mechanism for the temp plot folder so images don't accumulate"""
    plt_root = "./static/plots_temp/"  # cwd is 'app/'
    if os.path.isdir(plt_root):
        for plt in os.listdir(plt_root):
            os.remove(Path(plt_root + plt))
    else:
        os.mkdir(plt_root)


def generate_skyfield_predicts(
    tle: list, station: dict, days: float, sc: str, min_el: float
) -> list:
    # Set pandas to not warn about chained assignment, it's ok in this case which it cannot discern
    pd.options.mode.chained_assignment = None  # default='warn'

    # Time array: from now until n days at 1 sec intervals
    secs = int(days * 24 * 60 * 60)  # total seconds in propagation interval
    step_sec = 1.0  # time step size
    now = datetime.utcnow()
    now = now.replace(microsecond=0).replace(
        tzinfo=utc
    )  # utc obj is from skyfield, but could also use datetime.timezone.utc

    # Set up station:
    station_sf = wgs84.latlon(station["coords"][0] * N, station["coords"][1] * E)

    # Set up Skyfield sat-object from TLE
    ts = load.timescale()
    satellite = EarthSatellite(tle[1], tle[2], tle[0], ts)

    # Build station to sat vector object which will be propagated via time-steps
    stn_to_sat_vec = satellite - station_sf

    # Start/End times of entire span to feed into visibility search:
    datetimes = (now, now + timedelta(seconds=secs))
    timescales = ts.from_datetimes(datetimes)

    # Search for passes in time-range and capture start/end TimeScales of each one:
    times, events = satellite.find_events(station_sf, timescales[0], timescales[-1], altitude_degrees=min_el)
    passes = list()
    for idx, elem in enumerate(zip(times, events)):
        if elem[1] != 1 and (idx + 1) % 3 == 0 and idx != 0:
            # For every third-index, ignore out middle event (max el), and record events 1 and 3 (rise and set)
            # Event idx: 0=Rise above min_el, 1=Max el, 2=Set below min_el
            passes.append((times[idx-2], times[idx]))
    # print(f"pass times: {passes}")

    pass_count = len(passes)
    if pass_count == 0:
        print("- No passes in the specified time range!")
        return ["*** No passes in the specified time range! ***"]

    # Propagate for each individual pass:
    plt_lst = []    # list to be returned to controller
    clear_plt_folder()
    print(f"- Creating {pass_count} plots")

    for idx, flyby_times in enumerate(passes):
        # Create set of timescale objects at high resolution which will seed a dataframe for data:
        # - First need to convert existing start/end timescales to datetime, then add time delta, convert back
        fb_start_dt = flyby_times[0].utc_datetime()
        fb_end_dt = flyby_times[1].utc_datetime()
        fb_datetimes = list()
        step = 0
        step_size = timedelta(seconds=step_sec)
        steps = int((fb_end_dt - fb_start_dt) / step_size)

        while step <= steps:
            fb_datetimes.append(fb_start_dt + step*step_size)
            step += 1

        fb_timescales = ts.from_datetimes(fb_datetimes)

        # Set up dataframe with time-series and fill columns with vectorized functions:
        prop_data = pd.DataFrame(fb_datetimes, columns=["datetime"])

        # - get list of sat-stn vectors at time instances. This is essentially the propagator
        topo_list = stn_to_sat_vec.at(fb_timescales)

        # - convert to elevations, azimuths:
        el, az, dist = topo_list.altaz()
        prop_data["el_deg"] = el.degrees
        prop_data["az_deg"] = az.degrees

        # Plot: Use PANDAS package for plotting, based on matplotlib
        font_sz = 8
        plt.style.use("dark_background")

        plt.rc("font", size=font_sz)  # controls default text sizes

        # Make the plot. Below returns a matplotlib.axes.AxesSubplot object
        prop_data.plot(
            x="az_deg",
            y="el_deg",
            style=".",
            figsize=(5, 3),
            legend=False,
            # title=f'{sc} from {station["name"]}: Pass {idx + 1}',
            fontsize=font_sz,
            zorder=0,
            ms=4,  # marker size
        )

        # Better title adjustments:
        plt.title(f'{sc}, {station["name"]}: Pass {idx + 1}', fontsize=10, fontweight='bold')

        plt.subplots_adjust(bottom=0.26)    # provide margin for start/end time label

        # Plot a horizontal line to mark the user's min elevation cut-off:
        plt.axhline(min_el, linestyle="dashed", color="white")

        xtic_locs = [0, 90, 180, 270, 360]
        xtic_labels = ["North", "East", "South", "West", "North"]
        plt.xticks(xtic_locs, xtic_labels)
        plt.ylabel("Elevation (deg)")
        plt.xlabel("Azimuth (deg)")
        plt.ylim(0, 90)
        plt.xlim(0, 360)
        plt.rc("font", size=font_sz)  # controls default text sizes

        # Set up Start/End text box:
        start_time = prop_data["datetime"].iloc[0].replace(tzinfo=None, microsecond=0)
        end_time = prop_data["datetime"].iloc[-1].replace(tzinfo=None, microsecond=0)
        txt_str = f"Start: {start_time}    |    End: {end_time} UTC"

        # - these are matplotlib.patch.Patch properties
        bbox_props = dict(boxstyle="round", facecolor="white", alpha=0.5)
        plt.text(
            plt.xlim()[1] * 0.04,
            plt.ylim()[1] * -0.35,
            txt_str,
            fontsize=font_sz,
            bbox=bbox_props,
        )

        # Add direction arrow:
        # - arrow tail coords:
        arrow_y = prop_data["el_deg"].max()
        arrow_tail_x = prop_data[prop_data["el_deg"] == arrow_y]["az_deg"].item()

        # - arrow dir:
        arrow_x_idx = prop_data["el_deg"].idxmax()
        if arrow_x_idx != 0:
            sign = (
                arrow_tail_x - prop_data.loc[arrow_x_idx - 1]["az_deg"]
            )  # if sign +ve, arrow ->, else <-
        else:
            # Pass has started AT the max elevation at the beginning of propagation
            sign = (
                prop_data.loc[arrow_x_idx + 1]["az_deg"] - arrow_tail_x
            )  # if sign +ve, arrow ->, else <-

        # - arrow head coords:
        arr_len = 10 * (sign / abs(sign))
        arr_width = 1.5
        plt.arrow(
            arrow_tail_x,
            arrow_y + 3,
            arr_len,
            0,
            overhang=0.1,
            width=arr_width,
            head_width=4 * arr_width,
            color="white",
        )

        # Make plot files
        # - using the Path module here so that slashes get treated properly on Windows or Unix servers
        # - name them something unique to work with browser caching (same names with different data won't reload)
        plt_name = f'{sc}_{station["name"]}_{datetime.now().microsecond}_{min_el}'
        plt_path = Path(f"./static/plots_temp/{plt_name}.png")
        plt.savefig(plt_path, dpi=175)

        # Format the relative path relative to the template that will display it, eg. './plots_temp/<img>'
        plt_lst.append(f"./plots_temp/{plt_path.name}")

    plt.close("all")
    return plt_lst
