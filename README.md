# Satellite-Flyby-Plots

## About 
Satellite-Flyby-Plots is a minimalist web app to compute and display the trajectory of space-station flybys as viewed from select places on earth. It is built mainly in Python using the Bottle micro framework for a RESTful API/backend, html-templating, and matplotlib for visualizations. The astrodynamics is taken care of using the OREKIT library (native Java) with it's Python wrapper. 

The latest spacecraft trajectories are pulled from Space Track at run-time and propagated by OREKIT's TLE propagator. 

## Usage
Because the OREKIT python wrapper and the associated helpers are only available through Conda, this must be run from an Anaconda/Conda/miniconda environment (no pip). 
To create the environemnt from the included requirements.txt:

```py
conda create --name <your_env> --file requirements.txt
```

Or, if you have the other dependencies already in some Conda env, you can add just OREKIT via
```py
conda activate <your_env>
conda install -c conda-forge OREKIT
```

The app entry point is app.py and, as configured, will host on the local IP:PORT of 127.0.0.1:8080

## Screenshots
![Main](https://i.postimg.cc/j5Wx86fP/Main.png)
![plots1](https://i.postimg.cc/L5LHSHNs/plots1.png)
![plots2](https://i.postimg.cc/pTg239Q7/plots2.png)
