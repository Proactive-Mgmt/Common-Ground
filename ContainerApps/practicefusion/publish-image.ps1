#!/bin/pwsh

$IMAGE    = 'practicefusion'
$ACR_NAME = 'commongroundcr.azurecr.io'

docker login $ACR_NAME &&
docker build -t "$ACR_NAME/$IMAGE" . &&
docker push "$ACR_NAME/$IMAGE" 