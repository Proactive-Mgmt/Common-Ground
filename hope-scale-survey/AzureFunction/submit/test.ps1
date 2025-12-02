. .\UpdateTableRow.ps1
# Define the parameters
$PartitionKey = '2'
$RowKey = '1234123412'
# Call the function
Get-TableRow  -PartitionKey $PartitionKey -RowKey $RowKey  
Write-Host "Ok."


