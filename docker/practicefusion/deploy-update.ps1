#!/bin/pwsh
. (Join-Path $PSScriptRoot ".." "functions.ps1")
BuildImage $PSScriptRoot -Push
UpdateContainerAppJob $PSScriptRoot