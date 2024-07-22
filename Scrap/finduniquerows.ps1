# Define file paths
$fusionAppointmentsPath = "Scrap/fusionAppointments.csv"
$mcrahopeAppointmentsPath = "Scrap/mcrahopeappointments.csv"
$outputJsonPath = "Scrap/missingAppointments.json"

# Import CSV files
$fusionAppointments = Import-Csv -Path $fusionAppointmentsPath
$mcrahopeAppointments = Import-Csv -Path $mcrahopeAppointmentsPath

# Convert mcrahope appointments to a hash table for quick lookup by patient name
$mcrahopeAppointmentsHash = @{}
foreach ($appointment in $mcrahopeAppointments) {
    $mcrahopeAppointmentsHash[$appointment.patientName] = $true
}

# Find appointments in fusionAppointments that are not in mcrahopeAppointments based on patient name
$missingAppointments = @()
foreach ($appointment in $fusionAppointments) {
    if (-not $mcrahopeAppointmentsHash.ContainsKey($appointment.Patient)) {
        # Convert appointment time to the desired format
        $appointmentTime = [datetime]::ParseExact($appointment.AppointmentTime, "M/d/yyyy H:mm", $null).ToString("yyyy-MM-ddTHH:mm")
        
        $missingAppointments += [PSCustomObject]@{
            patientName       = $appointment.Patient
            patientDOB        = $appointment.DOB
            patientPhone      = $appointment.MobilePhone
            appointmentTime   = $appointmentTime
            appointmentStatus = $appointment.AppointmentStatus
            provider          = $appointment.SeenBy
            type              = $appointment.AppointmentType
        }
    }
}

# Convert missing appointments to JSON and save to file
$missingAppointments | ConvertTo-Json -Depth 3 | Set-Content -Path $outputJsonPath