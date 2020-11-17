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

## Initial pulldown of project

After initially cloning this project, this project depends on a submodule, CanonicalAutocorrelationAnalysis. This module must be initialized.

```
cd CanonicalAutocorrelationAnalysis
git submodule init
git submodule update

```

## Setting up mongo with docker

1. Ensure docker and docker-compose is installed and the daemon is running
2. Pull the latest mongo image
3. Configure a new volume for persisting mongo data
4. Duplicate the docker-compose yml file, ensuring it is configured to use the volume you created
5. Run the docker image using docker compose 

```
docker pull mongo
docker volume create sim-mongodb
docker-compose -f db.yml up

```
