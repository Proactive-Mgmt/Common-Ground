param($Request, $TriggerMetadata)

$htmlPath    = "$PSScriptRoot\form.html"
$htmlContent = Get-Content $htmlPath -Raw

Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
    StatusCode = [System.Net.HttpStatusCode]::OK
    ContentType = "text/html"
    Body = $htmlContent
})