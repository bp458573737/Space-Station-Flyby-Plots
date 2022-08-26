# sat_pass_demo

## About 
sat_pass_demo is a simple web app to compute and display the trajectory of space-station flybys as viewed from select places on earth. It is built mainly in Python using the Bottle micro framework for a RESTful API/backend, html-templating, and matplotlib for visualizations. The astrodynamics is taken care of using the OREKIT library (native Java) with it's Python wrapper. 

The latest spacecraft trajectories are pulled from Space Track at run-time and propagated by OREKIT's TLE propagator. 
