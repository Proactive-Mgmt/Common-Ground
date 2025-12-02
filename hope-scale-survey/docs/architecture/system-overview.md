# System Architecture Overview

## System Context

The Common Ground Hope Scale Survey system automates the distribution of patient satisfaction surveys by:

1. Syncing appointments from Practice Fusion EHR
2. Storing appointment data in Azure Table Storage
3. Sending personalized survey links via Twilio SMS
4. Serving survey forms via Azure Functions

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      External Systems                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Practice Fusion │  Azure Storage  │      Twilio SMS         │
│      (EHR)      │  (Table Store)  │   (Messaging Service)   │
└────────┬────────┴────────┬────────┴───────────┬─────────────┘
         │                  │                    │
         │                  │                    │
┌────────▼──────────────────▼──────────────────────▼────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐      ┌──────────────────────┐       │
│  │   Sync Script     │      │   Azure Functions    │       │
│  │   (main.py)       │      │   (PowerShell)       │       │
│  │                   │      │                      │       │
│  │  - sync_          │      │  - /api/serve        │       │
│  │    appointments() │      │  - /api/submit       │       │
│  │  - send_surveys() │      │                      │       │
│  └─────────┬─────────┘      └──────────┬───────────┘       │
│            │                           │                    │
│            └───────────┬─────────────────┘                    │
│                      │                                      │
│  ┌───────────────────▼───────────────────┐                 │
│  │         Shared Utilities               │                 │
│  │  - practice_fusion_utils.py            │                 │
│  │  - appointments_table_utils.py         │                 │
│  │  - twilio_utils.py                     │                 │
│  │  - shared/ptmlog.py                    │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Sync Script (`src/main.py`)

**Purpose**: Orchestrates appointment synchronization and survey distribution.

**Procedures**:
- `sync_appointments()`: Retrieves and stores appointments from Practice Fusion
- `send_surveys()`: Sends SMS surveys to patients with unsent appointments

**Dependencies**:
- `practice_fusion_utils`: Browser automation and HTML parsing
- `appointments_table_utils`: Azure Table Storage operations
- `twilio_utils`: SMS messaging

### 2. Practice Fusion Integration (`src/practice_fusion_utils.py`)

**Purpose**: Automated browser interaction with Practice Fusion EHR.

**Key Functions**:
- `login()`: Authenticates with Practice Fusion (handles MFA via CallHarbor)
- `get_appointments()`: Retrieves appointments for specified dates
- `parse_schedule_page()`: Extracts appointment data from HTML

**Technology**:
- Playwright for browser automation
- BeautifulSoup4 for HTML parsing
- Storage state persistence for session management

**Flow**:
1. Launch headless Chromium browser
2. Load saved storage state (if available)
3. Navigate to login page
4. Handle MFA if required (via CallHarbor)
5. Navigate to schedule page
6. Set date using UI navigation
7. Click "Print" to get structured HTML
8. Parse HTML to extract appointment data

### 3. Azure Table Storage (`src/appointments_table_utils.py`)

**Purpose**: Manages appointment data persistence.

**Key Functions**:
- `create_new_appointment()`: Creates new appointment entity (raises `ResourceExistsError` if duplicate)
- `get_appointments()`: Queries appointments that need surveys sent
- `update_appointment()`: Updates appointment with survey send timestamp and message SID

**Data Model**:
- **PartitionKey**: Last character of row key (for distribution)
- **RowKey**: MD5 hash of `patient_dob + patient_name + patient_phone + appointment_time`
- **Properties**:
  - `patientName`: Patient full name
  - `patientDOB`: Date of birth (YYYY-MM-DD)
  - `patientPhone`: Phone number (digits only)
  - `appointmentTime`: Appointment datetime (YYYY-MM-DDTHH:MM)
  - `appointmentStatus`: Status (e.g., "Seen")
  - `provider`: Provider name
  - `type`: Appointment type (e.g., "CLINICIAN")
  - `sentOn`: UTC timestamp when survey was sent (empty string if not sent)
  - `message_sid`: Twilio message SID (empty string if not sent)

**Query Filter**:
```
appointmentStatus eq 'Seen' 
and (provider eq 'BHUC COMMON GROUND' or provider eq '...')
and type eq 'CLINICIAN' 
and sentOn eq ''
```

### 4. Twilio Integration (`src/twilio_utils.py`)

**Purpose**: Sends SMS surveys to patients.

**Key Functions**:
- `send_survey()`: Sends personalized SMS with survey link

**Message Format**:
```
Hi {PatientName}, thank you for visiting us! 
We hope your recent appointment today was helpful. 
Please take a moment to share your feedback anonymously in our short survey. 
Your input helps us improve our services. 
Tap {SurveyLink}&id={AppointmentId} to start. 
Thank you!
```

### 5. Azure Functions

**Purpose**: HTTP endpoints for survey form serving and submission handling.

#### `/api/serve` (GET/POST)

**Purpose**: Serves survey form HTML.

**Parameters**:
- `id` (query string): Appointment row key

**Behavior**:
1. Query Azure Table Storage for appointment by `id`
2. If found: Return survey form HTML with appointment data
3. If not found: Return invalid appointment HTML

**Files**:
- `AzureFunction/serve/form.html`: Survey form template
- `AzureFunction/serve/invalid.html`: Error page template
- `AzureFunction/serve/GetTableRow.ps1`: PowerShell function code

#### `/api/submit` (POST)

**Purpose**: Handles survey form submissions.

**Behavior**:
1. Parse form data from request body
2. Update appointment entity in Azure Table Storage
3. Return success page

**Files**:
- `AzureFunction/submit/UpdateTableRow.ps1`: PowerShell function code
- `AzureFunction/submit/success.html`: Success page template

## Data Flow

### Appointment Sync Flow

```
1. Sync Script starts
   ↓
2. Get target date (from TARGET_DATE env var or today)
   ↓
3. Practice Fusion Utils:
   - Launch Playwright browser
   - Login to Practice Fusion
   - Navigate to schedule page
   - Set date
   - Extract appointment HTML
   - Parse appointments
   ↓
4. Filter appointments:
   - type == 'CLINICIAN'
   - appointment_status == 'Seen'
   ↓
5. For each appointment:
   - Calculate row key (MD5 hash)
   - Create entity in Azure Table Storage
   - Skip if ResourceExistsError (duplicate)
```

### Survey Distribution Flow

```
1. Sync Script calls send_surveys()
   ↓
2. Query Azure Table Storage:
   - appointmentStatus == 'Seen'
   - provider in ALLOWED_PROVIDERS
   - type == 'CLINICIAN'
   - sentOn == '' (not yet sent)
   ↓
3. For each appointment:
   - Send SMS via Twilio with survey link
   - Update appointment:
     * sentOn = current UTC timestamp
     * message_sid = Twilio message SID
```

### Survey Submission Flow

```
1. Patient receives SMS with survey link
   ↓
2. Patient clicks link: /api/serve?id={appointment_id}
   ↓
3. Azure Function queries table for appointment
   ↓
4. If found: Return form.html with appointment data
   If not found: Return invalid.html
   ↓
5. Patient completes form and submits
   ↓
6. POST to /api/submit with form data
   ↓
7. Azure Function updates appointment entity
   ↓
8. Return success.html
```

## Technology Stack

### Core Technologies

- **Python 3.13**: Application language
- **Playwright**: Browser automation
- **Azure Data Tables**: NoSQL storage
- **Twilio REST API**: SMS messaging
- **PowerShell Azure Functions**: HTTP endpoints

### Libraries

- **structlog**: Structured logging with procedure tracking
- **Pydantic**: Data validation and models
- **BeautifulSoup4**: HTML parsing
- **azure-data-tables**: Azure Table Storage client
- **twilio**: Twilio REST API client
- **playwright**: Browser automation framework

### Infrastructure

- **Azure Functions**: Serverless compute (PowerShell runtime)
- **Azure Storage Account**: Table Storage service
- **Azure Container Registry**: Docker image storage
- **Twilio Messaging Service**: SMS delivery

## Security Considerations

1. **Credentials**: Stored as environment variables (never in code)
2. **Authentication**: Practice Fusion login with MFA support
3. **Data Privacy**: Patient data stored in Azure Table Storage (encrypted at rest)
4. **SMS**: Twilio handles secure message delivery
5. **Function Auth**: Azure Functions use function-level authentication

## Observability

### Logging

All procedures use `structlog` with automatic context tracking:

```python
@ptmlog.procedure('cg_hope_scale_sync_appointments')
def sync_appointments():
    # Logs include:
    # - procedure_id: 'cg_hope_scale_sync_appointments'
    # - run_id: UUID for each execution
    # - run_status: 'started', 'succeeded', 'failed'
    # - run_arguments: Input parameters
    # - run_return_value: Output (on success)
```

### Log Output

**Development** (PTMLOG_CONSOLE=1):
- Pretty console output with colors
- Timestamps in HH:MM:SS.microseconds format

**Production** (default):
- JSON Lines format
- ISO 8601 timestamps (UTC)
- Exception tracebacks included

### Key Metrics

- Appointment sync success rate
- Survey send success rate
- Duplicate appointment detection
- Twilio message delivery status
- Azure Function invocation counts

## Error Handling

### Sync Script

- **Playwright timeouts**: Retry with exponential backoff
- **Login failures**: Save HTML snapshot for debugging
- **Duplicate appointments**: Log and continue (expected behavior)
- **Twilio errors**: Log exception and continue processing other appointments

### Azure Functions

- **Missing appointment ID**: Return invalid.html
- **Table storage errors**: Return 500 with error message
- **Form validation**: Client-side validation in HTML

## Scalability

### Current Limitations

- Sync script runs as single process (sequential appointment processing)
- Azure Functions: Consumption plan (auto-scales)
- Azure Table Storage: Partitioned by last character of row key

### Future Enhancements

- Parallel appointment processing
- Batch Twilio API calls
- Azure Functions Premium plan for VNet integration
- Azure Monitor alerts for failures

