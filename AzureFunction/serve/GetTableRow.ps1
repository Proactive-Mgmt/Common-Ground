# Ensure the Az and Azure.Storage.Tables modules are imported
Import-Module AzTable

# Define a function named Get-TableRow
function Get-TableRow {
    param (
        [string]$PartitionKey, # Parameter: The partition key of the row to retrieve
        [string]$RowKey        # Parameter: The row key of the row to retrieve
    )

    $ErrorActionPreference = 'stop'  # Set error action preference to 'stop' to halt execution on error

    # Get connection string from environment variable
    $ConnectionString = $env:STORAGE_ACCOUNT_CONNECTION_STRING
    if (-not $ConnectionString) {
        Write-Error "STORAGE_ACCOUNT_CONNECTION_STRING environment variable is not set"
        return $null
    }
    $TableName = 'appointments'

    # Create the storage context using the connection string
    $ctx = New-AzStorageContext -ConnectionString $ConnectionString

    # Get the storage table using the context and table name
    $StorageTable = Get-AzStorageTable -Name $TableName -Context $ctx

    # Retrieve the existing row from the storage table using PartitionKey and RowKey
    $ExistingRow = Get-AzTableRow -Table $StorageTable.CloudTable -PartitionKey $PartitionKey -RowKey $RowKey

    # Check if the row exists
    if (-not $ExistingRow) {
        Write-Error "Row with PartitionKey '$PartitionKey' and RowKey '$RowKey' does not exist."
        return $null
    }

    # Access the properties of the row to extract patientName and patientDOB
    $patientName = $ExistingRow.patientName
    $patientDOB = $ExistingRow.patientDOB

    # Create a hashtable to store patient information
    $patientInfo = @{
        patientName = $patientName  # Store patientName in the hashtable
        patientDOB  = $patientDOB    # Store patientDOB in the hashtable
    }

    # Return the patient information hashtable
    return $patientInfo
}


function Validate-Row {
    param (
        [string]$PartitionKey, # Parameter: The partition key of the row to retrieve
        [string]$RowKey        # Parameter: The row key of the row to retrieve
    )

    $ErrorActionPreference = 'stop'  # Set error action preference to 'stop' to halt execution on error

    # Get connection string from environment variable
    $ConnectionString = $env:STORAGE_ACCOUNT_CONNECTION_STRING
    if (-not $ConnectionString) {
        Write-Error "STORAGE_ACCOUNT_CONNECTION_STRING environment variable is not set"
        return 3
    }
    $TableName = 'appointments'

    # Create the storage context using the connection string
    $ctx = New-AzStorageContext -ConnectionString $ConnectionString

    # Get the storage table using the context and table name
    $StorageTable = Get-AzStorageTable -Name $TableName -Context $ctx

    # Retrieve the existing row from the storage table using PartitionKey and RowKey
    # Retrieve the existing row from the storage table using PartitionKey and RowKey
    try {
        $ExistingRow = Get-AzTableRow -Table $StorageTable.CloudTable -PartitionKey $PartitionKey -RowKey $RowKey

        if ( $ExistingRow) {
            # Check if the surveyCompleted property exists
            if ( $ExistingRow.PSObject.Properties['surveyCompletedOn']) {
                # Access the properties of the row to extract surveyCompleted
                Write-Host "Survey Completed"
                return  1
            }
            else {
                Write-Host "Survey Not Completed"
                return  2
            }
        }
        else {
            Write-Host "Row with PartitionKey '$PartitionKey' and RowKey '$RowKey' does not exist."
            return  3
        }
    

    }
    catch {
        Write-Host "Error: Row with PartitionKey '$PartitionKey' and RowKey '$RowKey' does not exist."
        return  3
    }
}