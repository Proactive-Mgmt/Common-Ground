param($Request, $TriggerMetadata)

function LoadHtmlForm {
    $htmlPath =  "$PSScriptRoot\form.html"
    $htmlContent = Get-Content $htmlPath -Raw
    return $htmlContent
}

function ProcessFormData {
    param($formData)
    $parsedData = [System.Web.HttpUtility]::ParseQueryString($formData)
    foreach ($key in $parsedData.AllKeys) {
        Write-Output "$key = $($parsedData[$key])"
    }
}

$method = $Request.Method

if ($method -eq 'GET') {
    $responseBody = LoadHtmlForm
    Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode = [System.Net.HttpStatusCode]::OK
        ContentType = "text/html"
        Body = $responseBody
    })
} elseif ($method -eq 'POST') {
    if ($Request.Headers.'Content-Type' -contains 'application/x-www-form-urlencoded') {
        $formData = [System.Text.Encoding]::UTF8.GetString($Request.Body)
        ProcessFormData -formData $formData
        Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
            StatusCode = [System.Net.HttpStatusCode]::OK
            ContentType = "text/plain"
            Body = "Form data processed successfully"
        })
    } else {
        Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
            StatusCode = [System.Net.HttpStatusCode]::UnsupportedMediaType
            ContentType = "text/plain"
            Body = "Unsupported Media Type"
        })
    }
}