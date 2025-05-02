function IsPendingChanges {
    $status = git status --porcelain
    if ($status) {
        return $true
    } else {
        return $false
    }
}

function GetCommitHash {
    return (git rev-parse --short HEAD)
}

function GetConfig {
    param (
        [Parameter(Mandatory=$true)] # Make the parameter mandatory
        [ValidateScript({
            # This script block runs to validate the parameter value ($_)
            if (Test-Path -Path $_ -PathType Container) {
                return $true # Validation succeeded
            } else {
                # Throw an error if validation fails
                throw "The path '$_' does not exist or is not a valid directory."
            }
        })]
        [string]$ContainerPath
    )

    $ConfigFile = Join-Path $ContainerPath "config.json"
    return Get-Content $ConfigFile | ConvertFrom-Json -AsHashtable
}

function GetFullImageName {
    param (
        [Parameter(Mandatory=$true)] # Make the parameter mandatory
        [ValidateScript({
            # This script block runs to validate the parameter value ($_)
            if (Test-Path -Path $_ -PathType Container) {
                return $true # Validation succeeded
            } else {
                # Throw an error if validation fails
                throw "The path '$_' does not exist or is not a valid directory."
            }
        })]
        [string]$ContainerPath
    )

    $Config = GetConfig $ContainerPath
    $IMAGE_NAME   = $Config.IMAGE_NAME
    $IMAGE_TAG    = GetCommitHash

    return "$($ACR_NAME)/$($IMAGE_NAME):$($IMAGE_TAG)"
}

function LoginToDocker {
    $ACR_NAME     = $env:ACR_NAME
    $ACR_USERNAME = $env:ACR_USERNAME
    $ACR_PASSWORD = $env:ACR_PASSWORD
    $ACR_PASSWORD | docker login $ACR_NAME -u $ACR_USERNAME --password-stdin
}

function BuildImage {
    param (
        [Parameter(Mandatory=$true)] # Make the parameter mandatory
        [ValidateScript({
            # This script block runs to validate the parameter value ($_)
            if (Test-Path -Path $_ -PathType Container) {
                return $true # Validation succeeded
            } else {
                # Throw an error if validation fails
                throw "The path '$_' does not exist or is not a valid directory."
            }
        })]
        [string]$ContainerPath,

        [switch]$Push,

        [switch]$Force
    )

    if ((IsPendingChanges) -and (-not $Force.IsPresent)) {
        Write-Error "Uncommitted changes detected. Please commit or stash your changes before deploying."
        exit 1
    }

    $ContainerDirectoryInfo = Get-Item -Path $ContainerPath # Use the validated parameter
    $ProjectRoot = $ContainerDirectoryInfo.Parent.Parent
    $DockerFile = Join-Path $ContainerPath "Dockerfile"

    $Config = GetConfig $ContainerPath
    $IMAGE_NAME = $Config.IMAGE_NAME 
    $CommitHash = GetCommitHash
    $TaggedImageName = "$($IMAGE_NAME):$($CommitHash)"

    # Build and push image
    LoginToDocker
    docker build --platform linux/amd64 -f $DockerFile -t $TaggedImageName $ProjectRoot.FullName
    if ($Push.IsPresent) {
        $ACR_NAME = $env:ACR_NAME
        $FullImageName = "$($ACR_NAME)/$($IMAGE_NAME):$($CommitHash)"
        docker tag $TaggedImageName $FullImageName
        docker push $FullImageName
    }
}

function UpdateContainerAppJob {
    param (
        [Parameter(Mandatory=$true)] # Make the parameter mandatory
        [ValidateScript({
            # This script block runs to validate the parameter value ($_)
            if (Test-Path -Path $_ -PathType Container) {
                return $true # Validation succeeded
            } else {
                # Throw an error if validation fails
                throw "The path '$_' does not exist or is not a valid directory."
            }
        })]
        [string]$ContainerPath
    )

    # The script follows these steps
    # 1. Update the container app job secrets.
    # 2. Update the container app job image, environment variables, and cron expression.

    $IMAGE_TAG = GetCommitHash

    # From Environment
    $ACR_NAME              = $env:ACR_NAME
    $AZURE_SUBSCRIPTION_ID = $env:AZURE_SUBSCRIPTION_ID

    # Config
    $ConfigFile = Join-Path $ContainerPath "config.json"
    $Config     = Get-Content $ConfigFile | ConvertFrom-Json -AsHashtable
    $IMAGE_NAME             = $Config.IMAGE_NAME
    $CONTAINER_APP_JOB_NAME = $Config.CONTAINER_APP_JOB_NAME
    $RESOURCE_GROUP_NAME    = $Config.RESOURCE_GROUP_NAME
    $CRON_EXPRESSION        = $Config.CRON_EXPRESSION
    $REPLICA_TIMEOUT        = $Config['REPLICA_TIMEOUT'] ?? '3600'

    # Calculated
    $FULL_IMAGE_NAME = "$($ACR_NAME)/$($IMAGE_NAME):$($IMAGE_TAG)"

    # For az containerapp job secret set
    $SECRET_SET_ARGS = @(
        "containerapp", "job", "secret", "set",
        "--name", $CONTAINER_APP_JOB_NAME,
        "--resource-group", $RESOURCE_GROUP_NAME,
        "--secrets"
    )
    foreach ($Secret in $Config.SECRETS.GetEnumerator()) {
        $SECRET_VALUE = Get-Item -Path "Env:$($Secret.Value)"
        $SECRET_SET_ARGS += "$($Secret.Key)=`"$($SECRET_VALUE.Value)`""
    }

    # For az containerapp job update
    $UPDATE_ARGS = @(
        "containerapp", "job", "update",
        "--name", $CONTAINER_APP_JOB_NAME,
        "--resource-group", $RESOURCE_GROUP_NAME,
        "--image", $FULL_IMAGE_NAME,
        "--cron-expression", "`"$CRON_EXPRESSION`"",
        "--replica-timeout", $REPLICA_TIMEOUT,
        "--replace-env-vars"
    )
    foreach ($EnvVar in $Config.ENV_VARS.GetEnumerator()) {
        if ($EnvVar.Value -like "secretref:*") {
            $UPDATE_ARGS += "$($EnvVar.Key)=$($EnvVar.Value)"
        }
        else {
            $UPDATE_ARGS += "$($EnvVar.Key)=`"$($EnvVar.Value)`""
        }
    }

    # Set az context
    az account set --subscription $AZURE_SUBSCRIPTION_ID

    # Update deployment
    Start-Process "az" -ArgumentList $SECRET_SET_ARGS -Wait -NoNewWindow
    Start-Process "az" -ArgumentList $UPDATE_ARGS -Wait -NoNewWindow
}

function UpdateContainerApp {
    param (
        [Parameter(Mandatory=$true)] # Make the parameter mandatory
        [ValidateScript({
            # This script block runs to validate the parameter value ($_)
            if (Test-Path -Path $_ -PathType Container) {
                return $true # Validation succeeded
            } else {
                # Throw an error if validation fails
                throw "The path '$_' does not exist or is not a valid directory."
            }
        })]
        [string]$ContainerPath
    )

    # The script follows these steps
    # 1. Update the container app job secrets.
    # 2. Update the container app job image, environment variables, and cron expression.

    $IMAGE_TAG = GetCommitHash

    # From Environment
    $ACR_NAME              = $env:ACR_NAME
    $AZURE_SUBSCRIPTION_ID = $env:AZURE_SUBSCRIPTION_ID

    # Config
    $ConfigFile = Join-Path $ContainerPath "config.json"
    $Config     = Get-Content $ConfigFile | ConvertFrom-Json -AsHashtable
    $IMAGE_NAME             = $Config.IMAGE_NAME
    $CONTAINER_APP_JOB_NAME = $Config.CONTAINER_APP_NAME
    $RESOURCE_GROUP_NAME    = $Config.RESOURCE_GROUP_NAME

    # Calculated
    $FULL_IMAGE_NAME = "$($ACR_NAME)/$($IMAGE_NAME):$($IMAGE_TAG)"

    # For az containerapp job secret set
    $SECRET_SET_ARGS = @(
        "containerapp", "secret", "set",
        "--name", $CONTAINER_APP_JOB_NAME,
        "--resource-group", $RESOURCE_GROUP_NAME,
        "--secrets"
    )
    foreach ($Secret in $Config.SECRETS.GetEnumerator()) {
        $SECRET_VALUE = Get-Item -Path "Env:$($Secret.Value)"
        $SECRET_SET_ARGS += "$($Secret.Key)=`"$($SECRET_VALUE.Value)`""
    }

    # For az containerapp job update
    $UPDATE_ARGS = @(
        "containerapp", "update",
        "--name", $CONTAINER_APP_JOB_NAME,
        "--resource-group", $RESOURCE_GROUP_NAME,
        "--image", $FULL_IMAGE_NAME,
        "--replace-env-vars"
    )
    foreach ($EnvVar in $Config.ENV_VARS.GetEnumerator()) {
        if ($EnvVar.Value -like "secretref:*") {
            $UPDATE_ARGS += "$($EnvVar.Key)=$($EnvVar.Value)"
        }
        else {
            $UPDATE_ARGS += "$($EnvVar.Key)=`"$($EnvVar.Value)`""
        }
    }

    # Set az context
    az account set --subscription $AZURE_SUBSCRIPTION_ID

    # Update deployment
    Start-Process "az" -ArgumentList $SECRET_SET_ARGS -Wait -NoNewWindow
    Start-Process "az" -ArgumentList $UPDATE_ARGS -Wait -NoNewWindow
}