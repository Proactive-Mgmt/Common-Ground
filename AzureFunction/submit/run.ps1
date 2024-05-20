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
# Define the parameters
$PartitionKey = '2'
$RowKey = '1234123412'
$PropertiesToUpdate = @{
    'Field1' = 'Updated From the form 1 '
    'Field2' = 'Updated From the form 12'
}
# Call the function

. C:\Repos\cg-hopescalesurvey\cg-hopescalesurvey\AzureFunction\submit\UpdateTableRow.ps1

Update-TableRow -PartitionKey $PartitionKey -RowKey $RowKey -PropertiesToUpdate $PropertiesToUpdate
Write-Host "Update completed successfully."

$jsonResponse = $paramHashtable | ConvertTo-Json
Write-Host  $jsonResponse

Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode  = [System.Net.HttpStatusCode]::OK
        ContentType = "application/json"#"text/plain"
        Body        = $jsonResponse #"Form data processed successfully"  + 
    })
