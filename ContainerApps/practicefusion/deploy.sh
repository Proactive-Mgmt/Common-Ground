# Build the Docker image
docker build -t practicefusion .

# Tag the image for your ACR
docker tag practicefusion commongroundcr.azurecr.io/practicefusion:latest

# Log in to your ACR
az acr login --name commongroundcr

# Push the image to ACR
docker push commongroundcr.azurecr.io/practicefusion:latest