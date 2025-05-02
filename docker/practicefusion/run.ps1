#!/bin/pwsh
. (Join-Path $PSScriptRoot ".." "functions.ps1")
BuildImage $PSScriptRoot -Force
$Config = GetConfig $PSScriptRoot
$Tag = GetCommitHash
$ImageName = "$($Config.IMAGE_NAME):$($Tag)"
docker run --rm -it --name practicefusion $ImageName