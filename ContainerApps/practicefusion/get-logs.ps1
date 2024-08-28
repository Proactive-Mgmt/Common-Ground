#!/bin/pwsh

$SUBSCRIPTION_ID    = '95257f24-41c8-4dc2-8657-18f74be4cfcb'
$IMAGE              = 'practicefusion'
$RESOURE_GROUP_NAME = 'HopeScaleSurvey'

az account set --subscription $SUBSCRIPTION_ID &&
az containerapp logs show --name $IMAGE --container $IMAGE --resource-group $RESOURE_GROUP_NAME