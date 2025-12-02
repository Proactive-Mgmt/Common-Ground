. .\GetTableRow.ps1
# Define the parameters
$PartitionKey = '5'
$RowKey = '57c6a2ab-3bfd-6283-6e8c-1ca1cfee16a4'
# Call the function
$Row = Validate-Row -PartitionKey $PartitionKey -RowKey $RowKey  
Write-Host $Row 


