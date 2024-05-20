
Import-Module AzTable

function Update-TableRow {
    param (
     
        [string]$PartitionKey,
        [string]$RowKey,
        [hashtable]$PropertiesToUpdate
    )

    $ErrorActionPreference = 'stop'
    $ConnectionString = '==>REPLACED==>=***REMOVED***;EndpointSuffix=core.windows.net'
    $TableName = 'appointments'


    # Create the storage context
    $ctx = New-AzStorageContext -ConnectionString $ConnectionString

    # Get the storage table
    $StorageTable = Get-AzStorageTable -Name $TableName -Context $ctx

    # Retrieve the existing row
    $ExistingRow = Get-AzTableRow -Table $StorageTable.CloudTable -PartitionKey $PartitionKey -RowKey $RowKey

    # Ensure $ExistingRow is not null
    if ($null -eq $ExistingRow) {
        Write-Error "The specified row does not exist."
        return
    }

    # Update or add the row properties
    foreach ($property in $PropertiesToUpdate.Keys) {
        if ($ExistingRow.PSObject.Properties[$property]) {
            # Update existing property
            $ExistingRow.PSObject.Properties[$property].Value = $PropertiesToUpdate[$property]
        } else {
            # Add new property
            $ExistingRow | Add-Member -MemberType NoteProperty -Name $property -Value $PropertiesToUpdate[$property]
        }
    }

    # Save the updated row back to the table
    Update-AzTableRow -Table $StorageTable.CloudTable -Entity $ExistingRow
    Write-Host "ok"
}

