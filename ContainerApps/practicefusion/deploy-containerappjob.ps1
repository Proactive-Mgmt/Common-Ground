#!/bin/pwsh

$SUBSCRIPTION_ID    = '95257f24-41c8-4dc2-8657-18f74be4cfcb'
$IMAGE              = 'practicefusion'
$ACR_NAME           = 'commongroundcr.azurecr.io'
$RESOURE_GROUP_NAME = 'HopeScaleSurvey'
$ENVIRONMENT_NAME   = 'environment-hopescalesurvey'

az account set --subscription $SUBSCRIPTION_ID &&
az containerapp job create `
    --name $IMAGE `
    --resource-group $RESOURE_GROUP_NAME `
    --environment $ENVIRONMENT_NAME `
    --trigger-type Schedule --cron-expression "0 * * * *" `
    --image "$ACR_NAME/$IMAGE" `
    --registry-server $ACR_NAME