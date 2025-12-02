$FUNCTION_APP_NAME   = 'CG-HopeScaleSurvey'
$TENANT_ID       = 'b18c0a87-41b5-4a80-9fea-263143932ad8'
$SUBSCRIPTION_ID = '95257f24-41c8-4dc2-8657-18f74be4cfcb'

$AzAccount = (az account show | ConvertFrom-Json)

if($AzAccount.tenantId -ne $TENANT_ID)
{
    az login --tenant $TENANT_ID
    $AzAccount = (az account show | ConvertFrom-Json) # Refresh AzAccount info
}

if($AzAccount.id -ne $SUBSCRIPTION_ID)
{
    az account set --subscription $SUBSCRIPTION_ID
    $AzAccount = (az account show | ConvertFrom-Json) # Refresh AzAccount info
}

if($AzAccount.tenantId -ne $TENANT_ID -or $AzAccount.id -ne $SUBSCRIPTION_ID)
{
    throw "Failed to login to the correct tenant or subscription."
}

func azure functionapp publish $FUNCTION_APP_NAME