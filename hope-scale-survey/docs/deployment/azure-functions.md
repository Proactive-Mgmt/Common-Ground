# Azure Functions Deployment Guide

## Prerequisites

- Azure account with Function App created
- Azure Functions Core Tools installed
- PowerShell 7+ (for local development)
- Azure CLI configured

## Local Development

### Install Azure Functions Core Tools

```bash
npm install -g azure-functions-core-tools@4
```

### Run Functions Locally

```bash
cd AzureFunction
func start
```

Functions will be available at:
- `http://localhost:7071/api/serve?id={appointment_id}`
- `http://localhost:7071/api/submit`

### Test Functions

```bash
# Test serve endpoint
curl "http://localhost:7071/api/serve?id=test-id"

# Test submit endpoint
curl -X POST "http://localhost:7071/api/submit" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "id=test-id&field1=value1"
```

## Deployment

### Method 1: Azure Functions Core Tools

```bash
cd AzureFunction
func azure functionapp publish cg-hopescalesurvey
```

### Method 2: Azure CLI

```bash
# Create Function App (if not exists)
az functionapp create \
  --resource-group rg-common-ground \
  --consumption-plan-location eastus \
  --runtime powershell \
  --runtime-version 7.4 \
  --functions-version 4 \
  --name cg-hopescalesurvey \
  --storage-account <storage-account-name>

# Deploy function code
cd AzureFunction
func azure functionapp publish cg-hopescalesurvey
```

### Method 3: GitHub Actions / CI/CD

See [.github/workflows/deploy-functions.yml](../.github/workflows/deploy-functions.yml) (if exists)

## Configuration

### Application Settings

Set these in Azure Portal → Function App → Configuration → Application settings:

| Setting | Value | Description |
|---------|-------|-------------|
| `STORAGE_ACCOUNT_CONNECTION_STRING` | `DefaultEndpointsProtocol=...` | Azure Storage connection string |
| `FUNCTIONS_WORKER_RUNTIME` | `powershell` | Function runtime |
| `FUNCTIONS_EXTENSION_VERSION` | `~4` | Functions extension version |
| `WEBSITE_TIME_ZONE` | `Eastern Standard Time` | Timezone for scheduled functions |

### Function-Specific Settings

#### Authentication

By default, functions use `authLevel: "function"` which requires a function key.

**Get function key**:
```bash
az functionapp function keys list \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --function-name serve
```

**Test with function key**:
```bash
curl "https://cg-hopescalesurvey.azurewebsites.net/api/serve?id=test-id&code={function-key}"
```

#### CORS (if needed)

```bash
az functionapp cors add \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --allowed-origins "https://your-frontend.com"
```

## Monitoring

### Application Insights

Enable Application Insights for detailed logging:

```bash
az monitor app-insights component create \
  --app cg-hopescalesurvey-insights \
  --location eastus \
  --resource-group rg-common-ground

az functionapp config appsettings set \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="{instrumentation-key}"
```

### Log Streaming

```bash
az webapp log tail \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey
```

### Metrics

View in Azure Portal:
- Function execution count
- Function execution duration
- HTTP status codes
- Error rate

## Troubleshooting

### Function Not Found

- Verify function name matches folder name
- Check `function.json` is valid JSON
- Ensure `run.ps1` exists and is executable

### Storage Connection Errors

- Verify `STORAGE_ACCOUNT_CONNECTION_STRING` is set correctly
- Check storage account is accessible
- Verify table name is "appointments"

### PowerShell Runtime Errors

- Check PowerShell version: `$PSVersionTable.PSVersion`
- Verify required modules are available
- Check function logs in Azure Portal

### Timeout Issues

- Increase function timeout in `host.json`:
```json
{
  "functionTimeout": "00:10:00"
}
```

## Rollback

### List Deployments

```bash
az functionapp deployment list \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey
```

### Rollback to Previous Version

```bash
az functionapp deployment source sync \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --manual-integration
```

Or redeploy previous commit:
```bash
git checkout <previous-commit>
cd AzureFunction
func azure functionapp publish cg-hopescalesurvey
```

## Best Practices

1. **Use Application Insights**: Enable for production monitoring
2. **Set Timeouts**: Configure appropriate timeouts in `host.json`
3. **Error Handling**: Implement try-catch in PowerShell functions
4. **Logging**: Use `Write-Host` for structured logs (JSON format)
5. **Secrets**: Store sensitive data in Key Vault references
6. **CORS**: Configure CORS for frontend integration
7. **Versioning**: Tag deployments with version numbers

## Production Checklist

- [ ] Application settings configured
- [ ] Storage connection string set
- [ ] Function keys secured
- [ ] Application Insights enabled
- [ ] CORS configured (if needed)
- [ ] Timeout settings appropriate
- [ ] Error handling implemented
- [ ] Monitoring alerts configured
- [ ] Backup strategy in place
- [ ] Documentation updated

