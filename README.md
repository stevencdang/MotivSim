# MotivSim

Python 3.8.5

Required Python Packages:
numpy
scipy
matplotlib
pandas
pymongo
jupyterlab

Required system packages:
docker

This project relies on a dockerized mongodb instance

## Setting up mongo with docker

Once docker is installed and running, pull mongo image and run mongo docker image exposing default port

```
docker pull mongo
docker run -p 27017:27017 mongo

```
