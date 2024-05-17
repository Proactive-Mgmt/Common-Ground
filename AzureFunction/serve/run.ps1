param($Request, $TriggerMetadata)

# Retrieve the id parameter from the request
$id = $Request.Query.id

$htmlPath = "$PSScriptRoot\form.html"
$htmlContent = Get-Content $htmlPath -Raw

 
# Inject the hidden field with the GUID into the HTML content
$htmlContent = $htmlContent -replace '</form>', "<input type='hidden' name='id' value='$id' /></form>"



Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode  = [System.Net.HttpStatusCode]::OK
        ContentType = "text/html"
        Body        = $htmlContent
    })