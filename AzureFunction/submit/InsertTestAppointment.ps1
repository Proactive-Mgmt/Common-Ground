Import-Module AzTable

$ConnectionString = '==>REPLACED==>=***REMOVED***;EndpointSuffix=core.windows.net'
$TableName = 'appointments'

# Create the storage context
$ctx = New-AzStorageContext -ConnectionString $ConnectionString

# Get the storage table
$StorageTable = Get-AzStorageTable -Name $TableName -Context $ctx

# Define test row data
# Generate a new GUID for RowKey
$RowKey = [guid]::NewGuid().ToString()
# PartitionKey is the last character of the RowKey
$PartitionKey = $RowKey[-1]
$TestRow = @{
    PartitionKey = $PartitionKey
    RowKey = $RowKey
    patientName = 'Test Patient'
    appointmentDate = '2025-07-10T15:30:00Z'
    status = 'Scheduled'
    notes = 'Inserted by InsertTestAppointment.ps1'
}

# Insert the test row
Add-AzTableRow -Table $StorageTable.CloudTable `
    -PartitionKey $PartitionKey `
    -RowKey $RowKey `
    -property @{'patientName'='Test Patient';'appointmentDate'='2025-07-10T15:30:00Z';'status'='Scheduled';'notes'='Inserted by InsertTestAppointment.ps1'}

Write-Host "Inserted appointment. RowKey: $RowKey PartitionKey: $PartitionKey"