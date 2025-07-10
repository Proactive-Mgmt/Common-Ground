# Connection Variables
$storageAccountName = "hopescalesurvey9d6a"
$storage==>REPLACED==> = "***REMOVED***"
$tableName = "appointments"
$sqlServer = "CGSQL4"
$database = "CG_Reporting"
$table = "[dbo].[HopeSurveyAnswers]"
$username = "ReplicationUser"
$password = "***REMOVED***"

# Create Context
try {
    $context = New-AzStorageContext -StorageAccountName $storageAccountName -Storage==>REPLACED==> $storage==>REPLACED==>
    Write-Output "Context created successfully"
} catch {
    Write-Error "Error creating storage context: $_"
    exit
}

# Obtain reference table
try {
    $cloudTable = (Get-AzStorageTable -Name $tableName -Context $context).CloudTable
    Write-Output "Reference to the table obtained correctly."
} catch {
    Write-Error "Error obtaining table reference: $_"
    exit
}

# Obtain rows from table
try {
    $rows = Get-AzTableRow -Table $cloudTable
    Write-Output "Rows obtained correctly."
} catch {
    Write-Error "Error obtaining rows using Get-AzTableRow: $_"
    exit
}

# connection string
$connectionString = "Server=$sqlServer;Database=$database;User Id=$username;Password=$password;"

# Function to parse datetime if valid
function Parse-DateTime($dateString) {
    if ([string]::IsNullOrEmpty($dateString)) {
        return $null
    }
    try {
        return [datetime]::Parse($dateString).ToString("yyyy-MM-ddTHH:mm:ss")
    } catch {
        return $null
    }
}

# Function to parse date if valid
function Parse-Date($dateString) {
    if ([string]::IsNullOrEmpty($dateString)) {
        return $null
    }
    try {
        return [datetime]::Parse($dateString).ToString("yyyy-MM-dd")
    } catch {
        return $null
    }
}

# Function to escape single quotes
function Escape-SingleQuote($value) {
    return $value -replace "'", "''"
}

# Process each row from table
foreach ($row in $rows) {
    # Convert datetime into SQL datetime format if valid

    # Escape single quotes in each field
    $partitionKey = Escape-SingleQuote $row.PartitionKey
    $rowKey = Escape-SingleQuote $row.RowKey
    $timestamp = Escape-SingleQuote $row.Timestamp
    $appointmentStatus = Escape-SingleQuote $row.appointmentStatus 
    $appointmentTime = Parse-DateTime $row.appointmentTime  
    $messageSid = Escape-SingleQuote $row.Message_sid 
    $patientDOB = Parse-Date $row.patientDOB   
    $patientName = Escape-SingleQuote $row.patientName    
    $patientPhone = Escape-SingleQuote $row.patientPhone    
    $provider = Escape-SingleQuote $row.provider    
    $sentOn = Parse-DateTime $row.sentOn
    $type = Escape-SingleQuote $row.type   
    $AreThereAnyOtherCommentsYouWouldLikeToMake = Escape-SingleQuote $row.AreThereAnyOtherCommentsYouWouldLikeToMake
    $ContactSomeoneIfINeedSupportBefore = Escape-SingleQuote $row.ContactSomeoneIfINeedSupport_before  
    $ContactSomeoneIfINeedSupportAfter = Escape-SingleQuote $row.ContactSomeoneIfINeedSupport_after   
    $ExperienceOfSchedulingAnAppointment = Escape-SingleQuote $row.ExperienceOfSchedulingAnAppointment    
    $FindResourcesToHelpMeBefore = Escape-SingleQuote $row.FindResourcesToHelpMe_before    
    $FindResourcesToHelpMeAfter = Escape-SingleQuote $row.FindResourcesToHelpMe_after  
    $HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportantToMeBefore = Escape-SingleQuote $row.HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportanToMe_before
    $HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportantToMeAfter = Escape-SingleQuote $row.HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportanToMe_after
    $InformationClearly = Escape-SingleQuote $row.InformationClearly  
    $IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter = Escape-SingleQuote $row.IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter
    $IfYouDidNotFeelMoreHopeWhenYouLeft = Escape-SingleQuote $row.IfYouDidNotFeelMoreHopeWhenYouLeft

    $MeetTheGoalsThatISetForMyselfBefore = Escape-SingleQuote $row.MeetTheGoalsThatISetForMyself_before   
    $MeetTheGoalsThatISetForMyselfAfter = Escape-SingleQuote $row.MeetTheGoalsThatISetForMyself_after 
    $MoreHopeByVisit = Escape-SingleQuote $row.MoreHopeByVisit    
    $RecommendCommonGroundToFriendInNeed = Escape-SingleQuote $row.RecommendCommonGroundToFriendInNeed    
    $SatisfiedWithHelpReceived = Escape-SingleQuote $row.SatisfiedWithHelpReceived    
    $StaffFriendlyAndWelcoming = Escape-SingleQuote $row.StaffFriendlyAndWelcoming    
    $TryNewSolutionsToMyChallengesBefore = Escape-SingleQuote $row.TryNewSolutionsToMyChallenges_before    
    $TryNewSolutionsToMyChallengesAfter = Escape-SingleQuote $row.TryNewSolutionsToMyChallenges_after 
    $RateYourOverallExperience = Escape-SingleQuote $row.RateYourOverallExperience    
    $ReasonAppropriatelyAddressed = Escape-SingleQuote $row.ReasonAppropriatelyAddressed    
    $SurveyCompletedOn = Parse-DateTime $row.surveyCompletedOn    

    # Truncate free-text fields to 255 characters to prevent SQL truncation errors
    function Truncate-String255($value) {
        if ($null -eq $value) { return $null }
        if ($value -is [string] -and $value.Length -gt 255) {
            return $value.Substring(0,255)
        }
        return $value
    }

    $HowDidYouHearAboutBHUC = Escape-SingleQuote (Truncate-String255 $row.HowDidYouHearAboutBHUC)
    $AreThereAnyOtherCommentsYouWouldLikeToMake = Escape-SingleQuote (Truncate-String255 $row.AreThereAnyOtherCommentsYouWouldLikeToMake)
    $IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter = Escape-SingleQuote (Truncate-String255 $row.IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter)
    $IfYouDidNotFeelMoreHopeWhenYouLeft = Escape-SingleQuote (Truncate-String255 $row.IfYouDidNotFeelMoreHopeWhenYouLeft)
    $ExperienceOfSchedulingAnAppointment = Escape-SingleQuote (Truncate-String255 $row.ExperienceOfSchedulingAnAppointment)
    $PatientName = Escape-SingleQuote (Truncate-String255 $row.patientName)
    $Provider = Escape-SingleQuote (Truncate-String255 $row.provider)

    Write-Output ("DEBUG: RowKey = '{0}', HowDidYouHearAboutBHUC = '{1}'" -f $rowKey, $HowDidYouHearAboutBHUC)

    # SQL command
    $query = @"
IF NOT EXISTS (SELECT 1 FROM $table WHERE PartitionKey = '$partitionKey' AND RowKey = '$rowKey')
BEGIN
    INSERT INTO $table (
       [PartitionKey]
      ,[RowKey]
      ,[Timestamp]
      ,[AppointmentStatus]
      ,[AppointmentTime]
      ,[Message_sid]
      ,[PatientDOB]
      ,[PatientName]
      ,[PatientPhone]
      ,[Provider]
      ,[sentOn]
      ,[Type]
      ,[AreThereAnyOtherCommentsYouWouldLikeToMake]
      ,[ContactSomeoneIfINeedSupport_before]
      ,[ContactSomeoneIfINeedSupport_after]
      ,[ExperienceOfSchedulingAnAppointment]
      ,[FindResourcesToHelpMe_before]
      ,[FindResourcesToHelpMe_after]
      ,[HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportanToMe_before]
      ,[HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportanToMe_after]
      ,[InformationClearly]
      ,[IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter]
      ,[IfYouDidNotFeelMoreHopeWhenYouLeft]
      ,[MeetTheGoalsThatISetForMyself_before]
      ,[MeetTheGoalsThatISetForMyself_after]
      ,[MoreHopeByVisit]
      ,[RecommendCommonGroundToFriendInNeed]
      ,[SatisfiedWithHelpReceived]
      ,[StaffFriendlyAndWelcoming]
      ,[TryNewSolutionsToMyChallenges_before]
      ,[TryNewSolutionsToMyChallenges_after]
      ,[RateYourOverallExperience]
      ,[ReasonAppropriatelyAddressed]
      ,[SurveyCompletedOn]
      ,[HowDidYouHearAboutBHUC]
    )
    VALUES (
        '$partitionKey',
        '$rowKey',
        '$timestamp',
        '$appointmentStatus',        
        '$appointmentTime',        
        '$messageSid',        
        '$patientDOB',        
        '$patientName',     
        '$patientPhone',
        '$provider',        
        '$sentOn',     
        '$type',
        '$AreThereAnyOtherCommentsYouWouldLikeToMake',       
        '$ContactSomeoneIfINeedSupportBefore',
        '$ContactSomeoneIfINeedSupportAfter',
        '$ExperienceOfSchedulingAnAppointment',        
        '$FindResourcesToHelpMeBefore',
        '$FindResourcesToHelpMeAfter',
        '$HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportantToMeBefore',
        '$HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportantToMeAfter',
        '$InformationClearly',
        '$IfYouDidNotReceiveHelpThatYouExpectedWhatCouldWeHaveDoneBetter',
        '$IfYouDidNotFeelMoreHopeWhenYouLeft',
        '$MeetTheGoalsThatISetForMyselfBefore',
        '$MeetTheGoalsThatISetForMyselfAfter',
        '$MoreHopeByVisit',        
        '$RecommendCommonGroundToFriendInNeed',        
        '$SatisfiedWithHelpReceived',        
        '$StaffFriendlyAndWelcoming',        
        '$TryNewSolutionsToMyChallengesBefore',
        '$TryNewSolutionsToMyChallengesAfter',
        '$RateYourOverallExperience',      
        '$ReasonAppropriatelyAddressed',        
        '$SurveyCompletedOn',
        '$HowDidYouHearAboutBHUC'
    )
END
"@

    # SQL command execution
    try {
        Invoke-Sqlcmd -ConnectionString $connectionString -Query $query
        Write-Output "Row inserted successfully or already exists."
    } catch {
        Write-Error "Error executing SQL command: $_"
    }
}