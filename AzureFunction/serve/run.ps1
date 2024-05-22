param($Request, $TriggerMetadata)

# . .serve\GetTableRow.ps1
. .\serve\GetTableRow.ps1


$id = $Request.Query.id

$htmlPath = "$PSScriptRoot\form.html"
$htmlContent = Get-Content $htmlPath -Raw

$PartitionKey = '2'
$RowKey = '1234123412'

$Row = Get-TableRow  -PartitionKey $PartitionKey -RowKey $RowKey  

Write-Host $Row

$patientName = $Row["patientName"]
$patientDOB = $Row["patientDOB"]



Write-Host  $Row["patientName"]  
Write-Host $Row["patientDOB"]



# Call the function



# Inject the hidden field with the GUID into the HTML content
$htmlContent = $htmlContent -replace '</form>', "<input type='hidden' name='id' value='$id' /></form>"

$htmlContent = $htmlContent -replace '<ClientName>', "<div class='text-gray-600' id='client-name'>$patientName</div>"

$htmlContent = $htmlContent -replace '<ClientDOB>', "<div class='text-gray-600' id='client-dob'>$patientDOB</div>"
# <div class='text-gray-600' id='client-name'>CARR Malik</div>


Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode  = [System.Net.HttpStatusCode]::OK
        ContentType = "text/html"
        Body        = $htmlContent
    })


# function Get-ClientData {
#     param (
         
#         [string]$PartitionKey,
#         [string]$RowKey
#     )
#     $Row = Get-TableRow  -PartitionKey $PartitionKey -RowKey $RowKey  

#     $paramHashtable[$patientName] 
#     $clientData["patientName"] = $Row["patientName"]
#     $clientData["patientDOB"] = $Row["patientDOB"]
  
#     Write-Host "Ok."


# }