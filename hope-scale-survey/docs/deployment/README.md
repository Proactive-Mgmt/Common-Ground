# Deployment Guide

## Overview

The Common Ground Hope Scale Survey system can be deployed in multiple ways:

1. **Azure Functions**: HTTP endpoints for survey form serving
2. **Docker Container**: Scheduled sync script execution
3. **Local Development**: For testing and development

## Quick Links

- [Azure Functions Deployment](azure-functions.md)
- [Docker Deployment](docker.md)
- [Local Development](../development/developer-guide.md)

## Prerequisites

### Required

- Azure account with:
  - Storage Account (Table Storage)
  - Function App
  - Container Registry (for Docker deployments)
- Twilio account with Messaging Service
- Practice Fusion credentials

### Tools

- Azure CLI
- Azure Functions Core Tools (for local development)
- Docker (for containerized deployments)
- Python 3.13+ (for local development)

## Deployment Options

### Option 1: Azure Functions Only

Deploy only the HTTP endpoints for survey form serving.

**Use Case**: When sync script runs separately (e.g., scheduled container job)

**Steps**:
1. Deploy Azure Functions (see [azure-functions.md](azure-functions.md))
2. Configure application settings
3. Test endpoints

### Option 2: Docker Container

Deploy sync script as scheduled container job.

**Use Case**: Automated appointment sync and survey distribution

**Steps**:
1. Build Docker image (see [docker.md](docker.md))
2. Push to Azure Container Registry
3. Create Container App or Container Instance
4. Configure scheduled job

### Option 3: Full Stack

Deploy both Azure Functions and Docker container.

**Use Case**: Complete system deployment

**Steps**:
1. Deploy Azure Functions
2. Deploy Docker container
3. Configure scheduled job
4. Test end-to-end flow

## Environment Variables

### Required for Sync Script

| Variable | Description |
|----------|-------------|
| `PRACTICEFUSION_USERNAME` | Practice Fusion login username |
| `PRACTICEFUSION_PASSWORD` | Practice Fusion login password |
| `STORAGE_ACCOUNT_CONNECTION_STRING` | Azure Storage connection string |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_CAMPAIGN_SID` | Twilio messaging service SID |
| `TWILIO_SURVEY_LINK` | Base survey URL |

### Required for Azure Functions

| Variable | Description |
|----------|-------------|
| `STORAGE_ACCOUNT_CONNECTION_STRING` | Azure Storage connection string |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_PROVIDERS` | "BHUC COMMON GROUND" | Comma-separated provider names |
| `TARGET_DATE` | Today | Date in YYYY-MM-DD format |
| `PTMLOG_CONSOLE` | "0" | Set to "1" for pretty console logs |
| `HEADLESS` | "TRUE" | Set to "FALSE" to show browser |
| `DEBUG_HTML` | "FALSE" | Set to "TRUE" to save HTML snapshots |

## Security Best Practices

1. **Use Azure Key Vault**: Store secrets in Key Vault and reference in containers
2. **Function Keys**: Rotate function keys regularly
3. **CORS**: Configure CORS only for trusted origins
4. **HTTPS**: Always use HTTPS in production
5. **Network Security**: Use VNet integration for Container Apps (if needed)

## Monitoring

### Application Insights

Enable Application Insights for:
- Function execution metrics
- Container execution logs
- Error tracking
- Performance monitoring

### Log Analytics

Query logs in Azure Monitor:
- Function execution logs
- Container execution logs
- Structured JSON logs from sync script

## Troubleshooting

### Common Issues

1. **Function Not Found**: Verify function name matches folder name
2. **Storage Connection Errors**: Verify connection string is correct
3. **Container Fails to Start**: Check environment variables
4. **Playwright Timeouts**: Increase wait times or check network

See individual deployment guides for detailed troubleshooting.

## Rollback Procedures

### Azure Functions

```bash
az functionapp deployment list \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey

az functionapp deployment source sync \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey
```

### Docker Container

Redeploy previous image version:
```bash
docker tag commongroundcr.azurecr.io/practicefusion:previous-version \
  commongroundcr.azurecr.io/practicefusion:latest
docker push commongroundcr.azurecr.io/practicefusion:latest
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Secrets stored in Key Vault (if applicable)
- [ ] Azure Functions deployed and tested
- [ ] Docker container built and pushed
- [ ] Scheduled job configured
- [ ] Application Insights enabled
- [ ] Monitoring alerts configured
- [ ] CORS configured (if needed)
- [ ] Function keys secured
- [ ] Backup strategy in place
- [ ] Documentation updated

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [Developer Guide](../development/developer-guide.md)
- Check Azure Portal logs
- Review Application Insights metrics

