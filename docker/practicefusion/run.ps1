#!/bin/pwsh
. (Join-Path $PSScriptRoot ".." "functions.ps1")
BuildImage $PSScriptRoot -Force
$Config = GetConfig $PSScriptRoot
$Tag = GetCommitHash
$ImageName = "$($Config.IMAGE_NAME):$($Tag)"
docker run --rm -it --name practicefusion `
    -e "STORAGE_ACCOUNT_CONNECTION_STRING=$($env:STORAGE_ACCOUNT_CONNECTION_STRING)" `
    -e "PRACTICEFUSION_USERNAME=$($env:PRACTICEFUSION_USERNAME)" `
    -e "PRACTICEFUSION_PASSWORD=$($env:PRACTICEFUSION_PASSWORD)" `
    -e "TWILIO_ACCOUNT_SID=$($env:TWILIO_ACCOUNT_SID)" `
    -e "TWILIO_AUTH_TOKEN=$($env:TWILIO_AUTH_TOKEN)" `
    -e "TWILIO_CAMPAIGN_SID=$($env:TWILIO_CAMPAIGN_SID)" `
    -e "TWILIO_SURVEY_LINK=$($env:TWILIO_SURVEY_LINK)" `
    -e "CALLHARBOR_USERNAME=$($env:CALLHARBOR_USERNAME)" `
    -e "CALLHARBOR_PASSWORD=$($env:CALLHARBOR_PASSWORD)" `
    -e "CALLHARBOR_MFA_SECRET=$($env:CALLHARBOR_MFA_SECRET)" `
    $ImageName