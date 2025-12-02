# Common Ground Hope Scale Survey

> **⚠️ DEPRECATED: This repository has been migrated to GitHub**  
> This Bitbucket repository is no longer maintained.  
> **New Location:** https://github.com/proactive-mgmt/Common-Ground/tree/main/hope-scale-survey  
> Please update your remotes and submit all future issues/PRs to the GitHub repository.

---

Automated survey distribution system that syncs appointments from Practice Fusion EHR, stores them in Azure Table Storage, and sends patient surveys via Twilio SMS.

## Features

- **Automated Appointment Sync**: Retrieves appointments from Practice Fusion using Playwright browser automation
- **Azure Table Storage**: Stores appointment data with deduplication
- **SMS Survey Distribution**: Sends personalized survey links via Twilio
- **Azure Functions**: HTTP endpoints for serving survey forms and handling submissions
- **Structured Logging**: JSON logging with procedure tracking using structlog

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Azure account with:
  - Storage Account (Table Storage)
  - Function App
  - Container Registry (for Docker deployments)
- Twilio account with Messaging Service
- Practice Fusion credentials

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/proactive-mgmt/Common-Ground.git
cd Common-Ground/hope-scale-survey
```

2. **Install dependencies**
```bash
uv pip install -r requirements.txt
playwright install chromium
```

3. **Set environment variables**
```bash
export PRACTICEFUSION_USERNAME="your_username"
export PRACTICEFUSION_PASSWORD="your_password"
export STORAGE_ACCOUNT_CONNECTION_STRING="your_connection_string"
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_CAMPAIGN_SID="your_campaign_sid"
export TWILIO_SURVEY_LINK="https://your-survey-link.com"
export ALLOWED_PROVIDERS="BHUC COMMON GROUND"  # Optional, comma-separated
export TARGET_DATE="2025-01-15"  # Optional, defaults to today
export PTMLOG_CONSOLE="1"  # Optional, enables pretty console logging
export HEADLESS="FALSE"  # Optional, shows browser window
export DEBUG_HTML="TRUE"  # Optional, saves HTML snapshots
```

4. **Run the sync script**
```bash
python src/main.py
```

### Azure Functions Local Development

1. **Install Azure Functions Core Tools**
```bash
npm install -g azure-functions-core-tools@4
```

2. **Run functions locally**
```bash
cd AzureFunction
func start
```

3. **Test endpoints**
- GET/POST `http://localhost:7071/api/serve?id={appointment_id}`
- POST `http://localhost:7071/api/submit`

## Architecture

### System Overview

```
┌─────────────────┐
│ Practice Fusion │
│      (EHR)      │
└────────┬────────┘
         │
         │ Playwright Automation
         │
┌────────▼────────┐
│  Sync Script    │
│  (main.py)      │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼────────┐  ┌─────▼──────┐
│ Azure Table     │  │  Twilio    │
│   Storage       │  │   SMS      │
└────────┬────────┘  └────────────┘
         │
         │ Query appointments
         │
┌────────▼────────┐
│ Azure Functions │
│  - /api/serve   │
│  - /api/submit  │
└─────────────────┘
```

### Components

1. **Sync Script** (`src/main.py`)
   - Retrieves appointments from Practice Fusion
   - Filters by provider, type, and status
   - Stores in Azure Table Storage
   - Sends surveys via Twilio

2. **Azure Functions**
   - `/api/serve`: Serves survey form HTML
   - `/api/submit`: Handles form submissions and updates table

3. **Data Storage**
   - Azure Table Storage: Appointment records with deduplication
   - Row key: MD5 hash of patient details + appointment time
   - Partition key: Last character of row key

### Data Flow

1. **Appointment Sync** (`sync_appointments()`)
   - Login to Practice Fusion via Playwright
   - Navigate to schedule page for target date
   - Parse HTML to extract appointment data
   - Filter: `type == 'CLINICIAN'` and `appointment_status == 'Seen'`
   - Create entities in Azure Table Storage (skip duplicates)

2. **Survey Distribution** (`send_surveys()`)
   - Query appointments where `sentOn == ''`
   - Filter by `ALLOWED_PROVIDERS` environment variable
   - Send SMS via Twilio with personalized survey link
   - Update appointment with `sentOn` timestamp and `message_sid`

## Tech Stack

### Backend
- **Python 3.13**: Core language
- **Playwright**: Browser automation for Practice Fusion
- **Azure Data Tables**: Appointment storage
- **Twilio**: SMS messaging
- **structlog**: Structured logging with procedure tracking
- **Pydantic**: Data validation
- **BeautifulSoup4**: HTML parsing

### Infrastructure
- **Azure Functions**: Serverless HTTP endpoints (PowerShell)
- **Azure Container Registry**: Docker image storage
- **Azure Storage Account**: Table Storage

### Development Tools
- **uv**: Fast Python package manager
- **Docker**: Containerization for scheduled tasks

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PRACTICEFUSION_USERNAME` | Yes | Practice Fusion login username |
| `PRACTICEFUSION_PASSWORD` | Yes | Practice Fusion login password |
| `STORAGE_ACCOUNT_CONNECTION_STRING` | Yes | Azure Storage connection string |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio auth token |
| `TWILIO_CAMPAIGN_SID` | Yes | Twilio messaging service SID |
| `TWILIO_SURVEY_LINK` | Yes | Base survey URL (appends `&id={appointment_id}`) |
| `ALLOWED_PROVIDERS` | No | Comma-separated provider names (default: "BHUC COMMON GROUND") |
| `TARGET_DATE` | No | Date in YYYY-MM-DD format (default: today) |
| `PTMLOG_CONSOLE` | No | Set to "1" for pretty console logs (default: JSON) |
| `HEADLESS` | No | Set to "FALSE" to show browser (default: "TRUE") |
| `DEBUG_HTML` | No | Set to "TRUE" to save HTML snapshots (default: "FALSE") |

### Logging

The project uses `structlog` with procedure tracking. Each procedure execution includes:
- `procedure_id`: Unique identifier for the procedure
- `run_id`: UUID for each execution
- `run_status`: "started", "succeeded", or "failed"
- `run_arguments`: Input parameters
- `run_return_value`: Output (on success)

Logs are JSON by default. Set `PTMLOG_CONSOLE=1` for development.

## Deployment

### Azure Functions

See [docs/deployment/azure-functions.md](docs/deployment/azure-functions.md) for detailed deployment instructions.

Quick deploy:
```bash
cd AzureFunction
func azure functionapp publish cg-hopescalesurvey
```

### Scheduled Sync (Docker)

See [docs/deployment/docker.md](docs/deployment/docker.md) for container deployment.

Build and push:
```bash
docker build -f docker/practicefusion/Dockerfile -t practicefusion .
docker tag practicefusion commongroundcr.azurecr.io/practicefusion:latest
az acr login --name commongroundcr
docker push commongroundcr.azurecr.io/practicefusion:latest
```

## Documentation

- [Architecture Overview](docs/architecture/system-overview.md)
- [API Reference](docs/api/azure-functions.md)
- [Deployment Guide](docs/deployment/)
- [Developer Guide](docs/development/)
- [CHANGELOG](CHANGELOG.md)

## Contributing

### Development Workflow

1. Create feature branch from `main`
2. Make changes with proper logging
3. Test locally with `PTMLOG_CONSOLE=1`
4. Submit pull request

### Code Standards

- Use `structlog` for all logging (via `ptmlog.get_logger()`)
- Use `@ptmlog.procedure()` decorator for main functions
- Type hints on all functions
- Pydantic models for data structures
- Handle exceptions with `logger.exception()`

## Troubleshooting

### Playwright Issues

- **Timeout errors**: Increase wait times or check network connectivity
- **Login failures**: Verify credentials and check for MFA requirements
- **HTML parsing errors**: Enable `DEBUG_HTML=TRUE` to inspect saved HTML

### Azure Table Storage

- **Duplicate key errors**: Expected behavior - appointment already exists
- **Query returns no results**: Check `ALLOWED_PROVIDERS` filter matches provider names exactly

### Twilio

- **SMS not sent**: Verify phone number format (E.164) and Twilio account balance
- **Message SID missing**: Check Twilio API response

## License

[Add license information]

## Contact

- **Project**: Common Ground Hope Scale Survey
- **Repository**: https://github.com/proactive-mgmt/Common-Ground/tree/main/hope-scale-survey

