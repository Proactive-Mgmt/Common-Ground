# Azure Functions API Reference

## Overview

The Common Ground Hope Scale Survey system exposes two HTTP endpoints via Azure Functions:

1. **GET/POST `/api/serve`**: Serves the survey form HTML
2. **POST `/api/submit`**: Handles survey form submissions

Both functions use PowerShell runtime and require function-level authentication by default.

## Authentication

All endpoints require a function key in the query string:

```
https://cg-hopescalesurvey.azurewebsites.net/api/serve?id={id}&code={function-key}
```

### Get Function Keys

```bash
az functionapp function keys list \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --function-name serve
```

## Endpoints

### GET/POST `/api/serve`

Serves the survey form HTML for a specific appointment.

#### Request

**URL**: `https://cg-hopescalesurvey.azurewebsites.net/api/serve`

**Method**: `GET` or `POST`

**Query Parameters**:
- `id` (required): Appointment row key (UUID format)
- `code` (required): Function key for authentication

**Example**:
```bash
curl "https://cg-hopescalesurvey.azurewebsites.net/api/serve?id=123e4567-e89b-12d3-a456-426614174000&code={function-key}"
```

#### Response

**Success (200 OK)**:
- Content-Type: `text/html`
- Body: Survey form HTML with appointment data pre-filled

**Error (200 OK with error page)**:
- Content-Type: `text/html`
- Body: Invalid appointment HTML page

#### Behavior

1. Extracts `id` from query string
2. Queries Azure Table Storage for appointment with matching `RowKey`
3. If found: Returns `form.html` with appointment data
4. If not found: Returns `invalid.html`

#### Example Response (Success)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Hope Scale Survey</title>
</head>
<body>
    <h1>Your feedback matters!</h1>
    <form action="/api/submit" method="post">
        <input type="hidden" name="id" value="123e4567-e89b-12d3-a456-426614174000">
        <!-- Survey questions -->
    </form>
</body>
</html>
```

### POST `/api/submit`

Handles survey form submissions and updates the appointment record.

#### Request

**URL**: `https://cg-hopescalesurvey.azurewebsites.net/api/submit`

**Method**: `POST`

**Headers**:
- `Content-Type: application/x-www-form-urlencoded`

**Body** (form data):
- `id` (required): Appointment row key
- Additional survey response fields (varies by form)

**Example**:
```bash
curl -X POST "https://cg-hopescalesurvey.azurewebsites.net/api/submit?code={function-key}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "id=123e4567-e89b-12d3-a456-426614174000&question1=value1&question2=value2"
```

#### Response

**Success (200 OK)**:
- Content-Type: `text/html`
- Body: Success page HTML

**Error (500 Internal Server Error)**:
- Content-Type: `text/html` or `application/json`
- Body: Error message

#### Behavior

1. Parses form data from request body
2. Extracts appointment `id`
3. Updates appointment entity in Azure Table Storage with survey responses
4. Returns success page HTML

#### Example Response (Success)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Thank You</title>
</head>
<body>
    <h1>Thank you for your feedback!</h1>
    <p>Your response has been recorded.</p>
</body>
</html>
```

## Error Handling

### Missing Appointment ID

**Request**: `/api/serve` without `id` parameter

**Response**: 400 Bad Request or invalid.html page

### Invalid Appointment ID

**Request**: `/api/serve?id=invalid-id`

**Response**: 200 OK with `invalid.html` page

### Table Storage Errors

**Request**: Any endpoint when Azure Table Storage is unavailable

**Response**: 500 Internal Server Error with error details

## Rate Limiting

Azure Functions Consumption plan includes:
- 1 million free requests per month
- Rate limits based on plan tier
- Automatic scaling based on load

## CORS

If frontend integration is needed, configure CORS:

```bash
az functionapp cors add \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --allowed-origins "https://your-frontend.com"
```

## Testing

### Local Testing

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

### Production Testing

```bash
# Get function key
FUNCTION_KEY=$(az functionapp function keys list \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey \
  --function-name serve \
  --query "default" -o tsv)

# Test serve endpoint
curl "https://cg-hopescalesurvey.azurewebsites.net/api/serve?id=test-id&code=$FUNCTION_KEY"
```

## Monitoring

### Application Insights

View function execution metrics in Azure Portal:
- Request count
- Response time
- Error rate
- HTTP status codes

### Logs

View function logs:
```bash
az webapp log tail \
  --resource-group rg-common-ground \
  --name cg-hopescalesurvey
```

## Best Practices

1. **Use HTTPS**: Always use HTTPS in production
2. **Validate Input**: Validate `id` parameter format (UUID)
3. **Error Handling**: Return user-friendly error pages
4. **Logging**: Log all requests and errors for debugging
5. **Security**: Keep function keys secure, rotate regularly
6. **CORS**: Configure CORS only for trusted origins
7. **Rate Limiting**: Monitor usage and upgrade plan if needed

