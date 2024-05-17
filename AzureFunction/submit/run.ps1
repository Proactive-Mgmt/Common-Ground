param($Request, $TriggerMetadata)

$Parameters = $Request.Query

# foreach ($key in $Parameters.Keys) {
#     Write-Host "$key = $($Parameters[$key])"
# }
$paramHashtable = @{}

# Populate the hashtable with the query parameters
foreach ($key in $Parameters.Keys) {
    $paramHashtable[$key] = $Parameters[$key]
}
$jsonResponse = $paramHashtable | ConvertTo-Json
Write-Host  $jsonResponse
Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode  = [System.Net.HttpStatusCode]::OK
        ContentType = "application/json"#"text/plain"
        Body        = $jsonResponse #"Form data processed successfully"  + 
    })
