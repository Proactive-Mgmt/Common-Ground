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

        [switch]$Force
    )

    if ((IsPendingChanges) -and (-not $Force.IsPresent)) {
        Write-HOst "hey"
        Write-Error "Uncommitted changes detected. Please commit or stash your changes before deploying."
        exit 1
    }

    $IMAGE_TAG = GetCommitHash
    
    $ContainerDirectoryInfo = Get-Item -Path $ContainerPath # Use the validated parameter
    $ProjectRoot = $ContainerDirectoryInfo.Parent.Parent
    $ConfigFile = Join-Path $ContainerPath "config.json"
    $DockerFile = Join-Path $ContainerPath "Dockerfile"

    # From Environment
    $ACR_NAME              = $env:ACR_NAME
    $ACR_USERNAME          = $env:ACR_USERNAME
    $ACR_PASSWORD          = $env:ACR_PASSWORD

    # Config
    $Config = Get-Content $ConfigFile | ConvertFrom-Json -AsHashtable
    $IMAGE_NAME = $Config.IMAGE_NAME

    # Calculated
    $FULL_IMAGE_NAME = "$($ACR_NAME)/$($IMAGE_NAME):$($IMAGE_TAG)"


    # Build and push image
    $ACR_PASSWORD | docker login $ACR_NAME -u $ACR_USERNAME --password-stdin
    docker build --platform linux/amd64 -f $DockerFile -t $FULL_IMAGE_NAME $ProjectRoot.FullName
    docker push $FULL_IMAGE_NAME
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