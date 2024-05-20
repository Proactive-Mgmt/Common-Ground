. .\UpdateTableRow.ps1
# Define the parameters
$PartitionKey = '2'
$RowKey = '1234123412'
$PropertiesToUpdate = @{
    'Field1' = 'Updated '
    'Field2' = 'Updated  too155'
}

# Call the function
Update-TableRow -PartitionKey $PartitionKey -RowKey $RowKey -PropertiesToUpdate $PropertiesToUpdate
Write-Host "Update completed successfully."


