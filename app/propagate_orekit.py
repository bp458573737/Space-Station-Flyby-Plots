"""
Propagate TLE and return Az/El
"""

import orekit
from orekit.pyhelpers import setup_orekit_curdir, absolutedate_to_datetime

# from org.orekit.data import DataProvidersManager, ZipJarCrawler
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint
from org.orekit.time import (
    TimeScalesFactory,
    AbsoluteDate,
    # DateComponents,
    # TimeComponents,
)
from org.orekit.utils import IERSConventions, Constants
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator

# from java.io import File

from math import radians, pi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# import plotly.express as px
from datetime import datetime


def generate_predicts(tle: list, station: dict, days: float, sc: str) -> list:
    pd.options.mode.chained_assignment = None  # default='warn'

    vm = orekit.initVM()
    setup_orekit_curdir()
    print("- Orekit data imported")

    # Define an orbit w TLE:
    # tle = [
    #     "1 43113F 58056A   22235.00000000  .00000244  00000-0  17312-3 0 00001",
    #     "2 43113 099.3640 325.9479 0120768 236.1575 344.4719 13.94337540000086",
    # ]

    mytle = TLE(tle[0], tle[1])
    mytle.getDate()

    start = datetime.utcnow()
    start = start.replace(microsecond=0)
    # start_str = start.strftime("%Y-%m-%d.%H.%M.%S")

    initialDate = AbsoluteDate(
        start.year,
        start.month,
        start.day,
        start.hour,
        0,
        0.0,
        TimeScalesFactory.getUTC(),
    )
    step_sec = 1.0
    finalDate = initialDate.shiftedBy(60.0 * 60.0 * 24.0 * float(days))  # Units: sec.

    min_el = 10.0  # degrees

    # Define Earth
    ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
    earth = OneAxisEllipsoid(
        Constants.WGS84_EARTH_EQUATORIAL_RADIUS, Constants.WGS84_EARTH_FLATTENING, ITRF
    )

    # Set up station:
    latitude = radians(station["coords"][0])
    longitude = radians(station["coords"][1])
    altitude = 0.0
    station1 = GeodeticPoint(latitude, longitude, altitude)
    sta1Frame = TopocentricFrame(earth, station1, station["name"])

    # Set up Propagation
    inertialFrame = FramesFactory.getEME2000()
    propagator = TLEPropagator.selectExtrapolator(mytle)

    pvs = []
    extrapDate = initialDate

    print("- Propagating...")
    while extrapDate.compareTo(finalDate) <= 0.0:
        pv = propagator.getPVCoordinates(extrapDate, inertialFrame)
        pvs.append(pv)
        extrapDate = extrapDate.shiftedBy(step_sec)
    print("\t- propagating done")

    # - Set up dataframe to manage results
    prop_data = pd.DataFrame(data=pvs, columns=["pv"])

    prop_data["elevation"] = prop_data["pv"].apply(
        lambda x: sta1Frame.getElevation(x.getPosition(), inertialFrame, x.getDate())
        * 180.0
        / pi
    )

    # Visibility flag:
    prop_data["visible"] = prop_data["elevation"].apply(lambda x: x >= min_el)

    # Cut out data below min elevation threshold:
    visible_data = prop_data[prop_data.visible == True]
    if visible_data.shape[0] == 0:
        print("- No passes in time range")
        return ["No passes in time range"]

    visible_data.reset_index(inplace=True)

    visible_data["Position"] = visible_data["pv"].apply(lambda x: x.getPosition())
    visible_data["datetime"] = visible_data["pv"].apply(
        lambda x: absolutedate_to_datetime(x.getDate())
    )

    # Find and label passes in the main dataframe:
    visible_data["time_delta"] = visible_data["datetime"].diff().dt.total_seconds()
    pass_start_indices = visible_data[visible_data["time_delta"] > step_sec].index
    if len(pass_start_indices == 0):
        # then there is only one pass
        pass_start_indices = [visible_data.shape[0] - 1]

    visible_data["azimuth"] = visible_data["pv"].apply(
        lambda x: sta1Frame.getAzimuth(x.getPosition(), inertialFrame, x.getDate())
        * 180.0
        / pi
    )

    # Plot: Use PANDAS package for plotting, based on matplotlib
    start_idx = 0
    font_sz = 10
    plt.style.use("dark_background")
    plt_lst = []

    print("- Creating plots")
    for idx, flyby in enumerate(pass_start_indices):
        if idx != 0:
            start_idx = pass_start_indices[idx - 1]
        plt.rc("font", size=font_sz)  # controls default text sizes
        xtic_locs = [0, 90, 180, 270]

        # Make the plot. Below returns a matplotlib.axes.AxesSubplot object
        pass_data = visible_data.iloc[start_idx:flyby]
        pass_data.plot(
            x="azimuth",
            y="elevation",
            style=".",
            figsize=(7, 5),
            legend=False,
            title=f'{sc} from {station["name"]}: Pass {idx + 1}',
            fontsize=font_sz,
            zorder=0,
            ms=3,               # marker size
        )

        xtic_labels = ["North", "East", "South", "West"]
        plt.xticks(xtic_locs, xtic_labels)
        plt.ylabel("Elevation (deg)")
        plt.xlabel("Azimuth")
        plt.ylim(0, 90)
        plt.xlim(0, 360)
        plt.rc("font", size=font_sz)  # controls default text sizes

        # Set up Start/End text box:
        txt_str = f'Start: {pass_data["datetime"].iloc[0]}    |    End: {pass_data["datetime"].iloc[-1]} UTC'
        # - these are matplotlib.patch.Patch properties
        bbox_props = dict(boxstyle="round", facecolor="white", alpha=0.5)
        plt.text(
            plt.xlim()[1] * 0.08,
            plt.ylim()[1] * 0.95,
            txt_str,
            fontsize=font_sz,
            bbox=bbox_props,
        )

        # Add direction arrow:
        # - arrow tail coords:
        arrow_y = pass_data["elevation"].max()
        arrow_tail_x = pass_data[pass_data["elevation"] == arrow_y]["azimuth"].item()

        # - arrow dir:
        arrow_x_idx = pass_data["elevation"].idxmax()
        sign = (
            arrow_tail_x - pass_data.loc[arrow_x_idx - 1]["azimuth"]
        )  # if sign +ve, arrow ->, else <-

        # - arrow head coords:
        arr_len = 20 * (sign / abs(sign))
        arr_width = 1.0
        plt.arrow(
            arrow_tail_x,
            arrow_y,
            arr_len,
            0,
            overhang=0.3,
            width=arr_width,
            head_width=5 * arr_width,
            color="white",
        )

        # Make plot files
        plt_path = f".\\static\\plots_temp\\plt_{idx}.png"
        plt.savefig(plt_path)

        # Format the relative path relative to template that will display it, eg. './plots_temp/<img>'
        plt_name = plt_path.split("\\static\\", 1)[-1]
        plt_lst.append(plt_name)

    plt.close("all")

    return plt_lst
