param($Request, $TriggerMetadata)

$Parameters = $Request.Query

foreach ($key in $Parameters.Keys) {
    Write-Host "$key = $($Parameters[$key])"
}

Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
    StatusCode = [System.Net.HttpStatusCode]::OK
    ContentType = "text/plain"
    Body = "Form data processed successfully"
})