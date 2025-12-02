# Docker Deployment Guide

## Overview

The sync script (`src/main.py`) can be deployed as a Docker container for scheduled execution in Azure Container Instances, Azure Container Apps, or any container orchestration platform.

## Build Image

### Local Build

```bash
docker build -f docker/practicefusion/Dockerfile -t practicefusion .
```

### Build with Azure Container Registry

```bash
# Build
docker build -f docker/practicefusion/Dockerfile -t practicefusion .

# Tag for ACR
docker tag practicefusion commongroundcr.azurecr.io/practicefusion:latest

# Login to ACR
az acr login --name commongroundcr

# Push
docker push commongroundcr.azurecr.io/practicefusion:latest
```

## Dockerfile Details

The Dockerfile (`docker/practicefusion/Dockerfile`) includes:

1. **Base Image**: Python 3.13-slim
2. **uv Installation**: Fast Python package manager
3. **Playwright**: Browser automation with Chromium
4. **Dependencies**: Installed from `requirements.txt`
5. **Source Code**: Copied from `src/` directory

## Environment Variables

Set these when running the container:

```bash
docker run -e PRACTICEFUSION_USERNAME="user" \
  -e PRACTICEFUSION_PASSWORD="pass" \
  -e STORAGE_ACCOUNT_CONNECTION_STRING="..." \
  -e TWILIO_ACCOUNT_SID="..." \
  -e TWILIO_AUTH_TOKEN="..." \
  -e TWILIO_CAMPAIGN_SID="..." \
  -e TWILIO_SURVEY_LINK="..." \
  practicefusion
```

Or use `.env` file:

```bash
docker run --env-file .env practicefusion
```

## Azure Container Instances

### Create Container Instance

```bash
az container create \
  --resource-group rg-common-ground \
  --name ci-hope-scale-sync \
  --image commongroundcr.azurecr.io/practicefusion:latest \
  --registry-login-server commongroundcr.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --environment-variables \
    PRACTICEFUSION_USERNAME="..." \
    PRACTICEFUSION_PASSWORD="..." \
    STORAGE_ACCOUNT_CONNECTION_STRING="..." \
    TWILIO_ACCOUNT_SID="..." \
    TWILIO_AUTH_TOKEN="..." \
    TWILIO_CAMPAIGN_SID="..." \
    TWILIO_SURVEY_LINK="..." \
  --restart-policy OnFailure
```

### Run on Schedule

Use Azure Logic Apps or Azure Container Apps with scheduled triggers.

## Azure Container Apps

### Create Container App

```bash
az containerapp create \
  --name ca-hope-scale-sync \
  --resource-group rg-common-ground \
  --image commongroundcr.azurecr.io/practicefusion:latest \
  --registry-server commongroundcr.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --env-vars \
    PRACTICEFUSION_USERNAME="..." \
    PRACTICEFUSION_PASSWORD="..." \
    STORAGE_ACCOUNT_CONNECTION_STRING="..." \
    TWILIO_ACCOUNT_SID="..." \
    TWILIO_AUTH_TOKEN="..." \
    TWILIO_CAMPAIGN_SID="..." \
    TWILIO_SURVEY_LINK="..." \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 0 \
  --max-replicas 1
```

### Add Scheduled Job

```bash
az containerapp job create \
  --name job-hope-scale-sync \
  --resource-group rg-common-ground \
  --trigger-type Schedule \
  --schedule "0 9 * * *" \
  --container-image-command "python /app/src/main.py" \
  --container-image-args "" \
  --cpu 1.0 \
  --memory 2.0Gi \
  --replica-timeout 1800 \
  --replica-retry-limit 1 \
  --replica-completion-count 1 \
  --parallelism 1
```

## Secrets Management

### Azure Key Vault

Store secrets in Key Vault and reference in container:

```bash
# Store secrets
az keyvault secret set --vault-name kv-common-ground --name PracticeFusionUsername --value "..."
az keyvault secret set --vault-name kv-common-ground --name PracticeFusionPassword --value "..."
az keyvault secret set --vault-name kv-common-ground --name StorageConnectionString --value "..."

# Reference in Container App
az containerapp update \
  --name ca-hope-scale-sync \
  --resource-group rg-common-ground \
  --set-env-vars \
    PRACTICEFUSION_USERNAME="@Microsoft.KeyVault(SecretUri=https://kv-common-ground.vault.azure.net/secrets/PracticeFusionUsername/)" \
    PRACTICEFUSION_PASSWORD="@Microsoft.KeyVault(SecretUri=https://kv-common-ground.vault.azure.net/secrets/PracticeFusionPassword/)"
```

## Monitoring

### View Logs

```bash
# Container Instances
az container logs \
  --resource-group rg-common-ground \
  --name ci-hope-scale-sync

# Container Apps
az containerapp logs show \
  --name ca-hope-scale-sync \
  --resource-group rg-common-ground \
  --follow
```

### Application Insights

Enable Application Insights for structured logging:

```bash
az containerapp update \
  --name ca-hope-scale-sync \
  --resource-group rg-common-ground \
  --set-env-vars \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."
```

## Troubleshooting

### Container Fails to Start

- Check environment variables are set correctly
- Verify image exists in registry
- Check container logs for errors

### Playwright Issues

- Ensure Chromium is installed: `playwright install chromium`
- Check headless mode: Set `HEADLESS=TRUE` for server environments
- Verify storage state persistence if using saved sessions

### Timeout Issues

- Increase container timeout settings
- Check network connectivity to Practice Fusion
- Verify Azure Storage connectivity

## Best Practices

1. **Use Key Vault**: Store secrets in Azure Key Vault
2. **Tag Images**: Use semantic versioning for image tags
3. **Health Checks**: Implement health check endpoints (if HTTP)
4. **Resource Limits**: Set appropriate CPU/memory limits
5. **Restart Policy**: Use `OnFailure` for scheduled jobs
6. **Logging**: Ensure logs go to stdout/stderr for Azure Monitor
7. **Retry Logic**: Implement retry logic for external API calls

## Production Checklist

- [ ] Image built and pushed to ACR
- [ ] Environment variables configured
- [ ] Secrets stored in Key Vault
- [ ] Container App/Instance created
- [ ] Scheduled job configured (if needed)
- [ ] Monitoring enabled (Application Insights)
- [ ] Logs accessible
- [ ] Resource limits set appropriately
- [ ] Restart policy configured
- [ ] Backup strategy in place

