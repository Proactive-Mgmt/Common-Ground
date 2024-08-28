#!/bin/pwsh
param(
    [Parameter(Mandatory=$false, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$IMAGE    = 'practicefusion'
$ACR_NAME = 'commongroundcr.azurecr.io'

docker build -t "$ACR_NAME/$IMAGE" . &&
docker run --rm -it "$ACR_NAME/$IMAGE" @Arguments