
param($Request, $TriggerMetadata)
# . C:\Repos\cg-hopescalesurvey\cg-hopescalesurvey\AzureFunction\submit\UpdateTableRow.ps1
# . .submit\UpdateTableRow.ps1
. .\submit\UpdateTableRow.ps1
$Parameters = $Request.Query

# foreach ($key in $Parameters.Keys) {
#     Write-Host "$key = $($Parameters[$key])"
# }
$paramHashtable = @{}

# Populate the hashtable with the query parameters
foreach ($key in $Parameters.Keys) {
    $paramHashtable[$key] = $Parameters[$key]
}

$RowKey = $Parameters["id"]
$PartitionKey = $RowKey[-1]
$paramHashtable.Remove("id") 
$paramHashtable.Remove("code") 
# Add the current date and time to the hashtable
$paramHashtable.Add("surveyCompletedOn", (Get-Date))
Write-Host $RowKey 


Write-Host  $paramHashtable
Update-TableRow -PartitionKey $PartitionKey -RowKey $RowKey -PropertiesToUpdate $paramHashtable
Write-Host "Update completed successfully."

$jsonResponse = $paramHashtable | ConvertTo-Json
Write-Host  $jsonResponse

Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode  = [System.Net.HttpStatusCode]::OK
        ContentType = "text/plain"
        Body        = "Form data processed successfully. Thank you!"  
    })
