param($Request, $TriggerMetadata)
# . .\serve\GetTableRow.ps1
. "$PSScriptRoot\GetTableRow.ps1"


$RowKey = $Request.Query.id 
$PartitionKey = $RowKey[-1]

$Row = Validate-Row -PartitionKey $PartitionKey -RowKey $RowKey  
if ($Row -eq 2) {
    
    $htmlPath = "$PSScriptRoot\form.html"
    $htmlContent = Get-Content $htmlPath -Raw
    $htmlContent = $htmlContent -replace '</form>', "<input type='hidden' name='id' value='$RowKey' /></form>"
    
    Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
            StatusCode  = [System.Net.HttpStatusCode]::OK
            ContentType = "text/html"
            Body        = $htmlContent
        })
}
else {

    Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
            StatusCode  = [System.Net.HttpStatusCode]::OK
            ContentType = "text/plain"
            Body        = "Invalid Id or survey has been answered. Thank you!"  
        })

}