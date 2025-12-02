# Changelog

All notable changes to the Common Ground Hope Scale Survey project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project documentation
- Architecture documentation with system diagrams
- Deployment guides for Azure Functions and Docker
- API reference documentation
- Developer guide with code standards
- CHANGELOG.md for version tracking

### Changed
- Improved README.md with quick start guide
- Enhanced logging documentation

## [1.0.0] - 2025-01-XX

### Added
- Initial release of Common Ground Hope Scale Survey system
- Appointment sync from Practice Fusion EHR
- Azure Table Storage integration
- Twilio SMS survey distribution
- Azure Functions for survey form serving
- Structured logging with structlog
- Procedure tracking with `@ptmlog.procedure()` decorator
- Playwright browser automation for Practice Fusion
- CallHarbor MFA integration
- Docker containerization support
- Provider filtering via `ALLOWED_PROVIDERS` environment variable
- HTML debugging with `DEBUG_HTML` environment variable
- Browser visibility control with `HEADLESS` environment variable

### Features
- **Appointment Sync**: Automated retrieval of appointments from Practice Fusion
  - Filters by type (`CLINICIAN`) and status (`Seen`)
  - Deduplication via MD5 hash of patient details + appointment time
  - Stores in Azure Table Storage

- **Survey Distribution**: Automated SMS survey sending
  - Queries appointments that need surveys sent
  - Filters by allowed providers
  - Sends personalized survey links via Twilio
  - Updates appointment records with send timestamp and message SID

- **Azure Functions**: HTTP endpoints for survey form
  - `/api/serve`: Serves survey form HTML with appointment data
  - `/api/submit`: Handles form submissions and updates table

- **Logging**: Structured JSON logging with procedure tracking
  - Automatic context tracking (procedure_id, run_id)
  - Pretty console output for development
  - JSON Lines format for production

### Technical Details
- Python 3.13
- Playwright for browser automation
- Azure Data Tables for storage
- Twilio REST API for SMS
- PowerShell Azure Functions for HTTP endpoints
- structlog for structured logging
- Pydantic for data validation
- BeautifulSoup4 for HTML parsing

### Known Issues
- Playwright timeouts may occur with slow network connections
- Duplicate appointment detection relies on exact patient details match
- Survey form requires function key authentication

### Security
- Credentials stored as environment variables
- Practice Fusion login with MFA support
- Azure Table Storage encryption at rest
- Twilio secure message delivery
- Function-level authentication for Azure Functions

## [0.1.0] - 2024-10-17

### Added
- Initial survey form changes
- Updated survey form text:
  - Introduction text: Removed "it" from sentence
  - First question: Spelled out "BHUC" as "Behavioral Health Urgent Care"
  - Second question: Spelled out "BHUC" as "the Behavioral Health Urgent Care"
  - Modal prompt: Updated phrasing to be more direct

### Changed
- Survey form HTML (`AzureFunction/serve/form.html`)
  - Updated introduction text
  - Updated question text
  - Updated modal prompt text

### Technical Details
- File Modified: `AzureFunction/serve/form.html`
- Git Commit: 36baad3
- Deployment: Azure Function App `cg-hopescalesurvey`

---

## Version History

- **1.0.0**: Full system release with all features
- **0.1.0**: Initial survey form changes

## Future Enhancements

- [ ] Parallel appointment processing
- [ ] Batch Twilio API calls
- [ ] Azure Monitor alerts for failures
- [ ] Automated testing suite
- [ ] CI/CD pipeline
- [ ] Health check endpoints
- [ ] Rate limiting for Azure Functions
- [ ] Survey response analytics
- [ ] Multi-language support
- [ ] Email survey option

