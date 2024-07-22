docker login commongroundcr.azurecr.io
docker build -t commongroundcr.azurecr.io/practicefusion .
docker push commongroundcr.azurecr.io/practicefusion:latest