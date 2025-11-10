#!/bin/bash
# Build the Docker image
# This script should be run from the project root directory

# Build the Docker image from the docker/practicefusion directory
docker build -f docker/practicefusion/Dockerfile -t practicefusion .

# Tag the image for your ACR
docker tag practicefusion commongroundcr.azurecr.io/practicefusion:latest

# Log in to your ACR
az acr login --name commongroundcr

# Push the image to ACR
docker push commongroundcr.azurecr.io/practicefusion:latest