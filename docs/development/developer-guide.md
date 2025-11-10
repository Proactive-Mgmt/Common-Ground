# Developer Guide

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Node.js 18+ (for Azure Functions Core Tools)
- Azure Functions Core Tools v4
- Docker (optional, for containerized deployments)

### Development Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd cg-hopescalesurvey
```

2. **Install Python dependencies**
```bash
uv pip install -r requirements.txt
playwright install chromium
```

3. **Install Azure Functions Core Tools**
```bash
npm install -g azure-functions-core-tools@4
```

4. **Set up environment variables**
```bash
# Create .env file (do not commit)
export PRACTICEFUSION_USERNAME="your_username"
export PRACTICEFUSION_PASSWORD="your_password"
export STORAGE_ACCOUNT_CONNECTION_STRING="your_connection_string"
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_CAMPAIGN_SID="your_campaign_sid"
export TWILIO_SURVEY_LINK="https://your-survey-link.com"
export PTMLOG_CONSOLE="1"  # Pretty console logs
export HEADLESS="FALSE"  # Show browser
export DEBUG_HTML="TRUE"  # Save HTML snapshots
```

## Project Structure

```
cg-hopescalesurvey/
├── src/
│   ├── main.py                      # Main sync script
│   ├── models.py                    # Pydantic models
│   ├── practice_fusion_utils.py     # Practice Fusion integration
│   ├── appointments_table_utils.py  # Azure Table Storage
│   ├── twilio_utils.py              # Twilio SMS
│   ├── callharbor_utils.py          # CallHarbor MFA
│   ├── storage_state_persistence_utils.py  # Playwright session
│   └── shared/
│       └── ptmlog.py                # Logging configuration
├── AzureFunction/
│   ├── serve/
│   │   ├── function.json            # Function configuration
│   │   ├── form.html                # Survey form template
│   │   ├── invalid.html             # Error page template
│   │   └── GetTableRow.ps1          # PowerShell function code
│   └── submit/
│       ├── function.json
│       ├── success.html
│       └── UpdateTableRow.ps1
├── docker/
│   └── practicefusion/
│       └── Dockerfile               # Container image
├── docs/                            # Documentation
├── requirements.txt                 # Python dependencies
└── README.md                        # Project overview
```

## Code Standards

### Python

#### Logging

**Always use `structlog` via `ptmlog.get_logger()`**:

```python
from shared import ptmlog

logger = ptmlog.get_logger()

# Structured logging
logger.info('appointment.synced', 
    patient_name=appointment.patient_name,
    appointment_time=appointment.appointment_time
)

# Exception logging
try:
    risky_operation()
except Exception as e:
    logger.exception('operation.failed', 
        error=str(e),
        error_type=type(e).__name__
    )
```

#### Procedure Decorator

Use `@ptmlog.procedure()` for main functions:

```python
@ptmlog.procedure('cg_hope_scale_sync_appointments')
def sync_appointments():
    # Automatically logs:
    # - procedure_id: 'cg_hope_scale_sync_appointments'
    # - run_id: UUID for each execution
    # - run_status: 'started', 'succeeded', 'failed'
    # - run_arguments: Input parameters
    # - run_return_value: Output (on success)
    pass
```

#### Type Hints

Always include type hints:

```python
def create_appointment(
    patient_name: str,
    appointment_time: datetime,
) -> None:
    pass
```

#### Pydantic Models

Use Pydantic for data validation:

```python
from pydantic import BaseModel
from datetime import date, datetime

class PracticeFusionAppointment(BaseModel):
    patient_name: str
    patient_dob: date
    patient_phone: str
    appointment_time: datetime
    appointment_status: str
    provider: str
    type: str
```

### PowerShell (Azure Functions)

#### Error Handling

Always use try-catch:

```powershell
try {
    $result = Get-TableRow -id $id
    return $result
} catch {
    Write-Host "Error: $_"
    return $null
}
```

#### Logging

Use `Write-Host` for structured logs:

```powershell
Write-Host "appointment.retrieved" -CustomProperty @{
    appointment_id = $id
    status = "success"
}
```

## Testing

### Local Testing

#### Sync Script

```bash
# Run sync script
python src/main.py

# With specific date
TARGET_DATE="2025-01-15" python src/main.py

# With debug HTML
DEBUG_HTML="TRUE" HEADLESS="FALSE" python src/main.py
```

#### Azure Functions

```bash
# Start functions locally
cd AzureFunction
func start

# Test serve endpoint
curl "http://localhost:7071/api/serve?id=test-id"

# Test submit endpoint
curl -X POST "http://localhost:7071/api/submit" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "id=test-id&field1=value1"
```

### Debugging

#### Enable Debug HTML

Set `DEBUG_HTML=TRUE` to save HTML snapshots:

```bash
DEBUG_HTML="TRUE" python src/main.py
```

HTML files will be saved in `./screenshots/` directory:
- `00_initial_login_page.html`
- `00_after_login_click.html`
- `00_mfa_page.html`
- `02_schedule_url_loaded.html`
- `03_schedule_page_{date}.html`

#### Enable Browser Window

Set `HEADLESS=FALSE` to see browser:

```bash
HEADLESS="FALSE" python src/main.py
```

#### Pretty Console Logs

Set `PTMLOG_CONSOLE=1` for colored console output:

```bash
PTMLOG_CONSOLE="1" python src/main.py
```

## Common Tasks

### Add New Provider

1. Update `ALLOWED_PROVIDERS` environment variable:
```bash
export ALLOWED_PROVIDERS="BHUC COMMON GROUND, NEW PROVIDER"
```

2. Verify provider name matches exactly in Practice Fusion

### Modify Survey Form

1. Edit `AzureFunction/serve/form.html`
2. Test locally with `func start`
3. Deploy to Azure

### Change Survey Message

1. Edit `src/twilio_utils.py`:
```python
message_body = (
    f"Hi {patient_name.title()}, your new message here. "
    f"Survey link: {link}"
)
```

2. Test locally
3. Deploy updated script

### Add New Appointment Filter

1. Edit `src/main.py`:
```python
filtered_appointments = [
    appointment
    for appointment in pf_appointments
    if appointment.type == 'CLINICIAN'
    and appointment.appointment_status == 'Seen'
    and appointment.provider == 'NEW PROVIDER'  # Add filter
]
```

2. Test locally
3. Deploy updated script

## Troubleshooting

### Playwright Issues

**Problem**: Timeout waiting for schedule page

**Solution**:
- Increase wait time in `practice_fusion_utils.py`
- Check network connectivity
- Enable `DEBUG_HTML=TRUE` to inspect HTML

**Problem**: Login fails

**Solution**:
- Verify credentials
- Check for MFA requirements
- Enable `DEBUG_HTML=TRUE` to see login page HTML
- Check CallHarbor MFA integration

### Azure Table Storage

**Problem**: Duplicate key errors

**Solution**: This is expected behavior - appointment already exists. The script logs and continues.

**Problem**: Query returns no results

**Solution**:
- Check `ALLOWED_PROVIDERS` matches provider names exactly
- Verify filter syntax in `appointments_table_utils.py`
- Check table name is "appointments"

### Twilio

**Problem**: SMS not sent

**Solution**:
- Verify phone number format (E.164: +1234567890)
- Check Twilio account balance
- Verify `TWILIO_CAMPAIGN_SID` is correct
- Check Twilio logs in dashboard

**Problem**: Message SID missing

**Solution**:
- Check Twilio API response
- Verify `TWILIO_AUTH_TOKEN` is correct
- Check Twilio account status

## Best Practices

1. **Always use structured logging**: Use `ptmlog.get_logger()` for all logs
2. **Handle exceptions**: Use try-catch with `logger.exception()`
3. **Type hints**: Include type hints on all functions
4. **Pydantic models**: Use Pydantic for data validation
5. **Environment variables**: Never hardcode secrets
6. **Error handling**: Continue processing on individual failures
7. **Testing**: Test locally before deploying
8. **Documentation**: Update docs when making changes

## Git Workflow

1. Create feature branch from `main`
2. Make changes with proper logging
3. Test locally
4. Commit with descriptive messages
5. Push and create pull request
6. Review and merge

## Deployment Checklist

Before deploying:

- [ ] Code tested locally
- [ ] Environment variables configured
- [ ] Logging includes all necessary context
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

