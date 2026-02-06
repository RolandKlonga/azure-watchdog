# Azure Watchdog

A containerised Python network monitoring service that continuously checks internet connectivity and reports telemetry data to Azure Log Analytics using the HTTP Data Collector API.

## Architecture

The watchdog operates as a lightweight Docker container running a Python monitoring loop. It performs periodic connectivity checks against a public DNS server (8.8.8.8) and logs all events to Azure Log Analytics without relying on external Azure SDKs. The system implements direct REST API authentication using HMAC-SHA256 request signing.

## Security Implementation

### Request Signing with HMAC-SHA256

The `build_signature` function implements Azure's SharedKey authentication scheme, manually constructing and signing each API request to the HTTP Data Collector API. This approach eliminates dependency on the Azure SDK whilst maintaining secure authentication.

**Signature Construction Process:**

1. **Canonical String Creation**: The function constructs a canonical string-to-sign containing HTTP method, content length, content type, custom headers (`x-ms-date`), and resource path:
   ```
   POST\n{content_length}\napplication/json\nx-ms-date:{rfc1123date}\n/api/logs
   ```

2. **Key Decoding**: The Azure workspace primary key (provided as a Base64-encoded string) is decoded to raw bytes:
   ```python
   decoded_key = base64.b64decode(shared_key)
   ```

3. **HMAC-SHA256 Hashing**: The canonical string is hashed using HMAC with SHA256, using the decoded key:
   ```python
   hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256)
   ```

4. **Base64 Encoding**: The resulting hash is Base64-encoded and formatted as a SharedKey authorisation header:
   ```python
   authorization = "SharedKey {customer_id}:{encoded_hash}"
   ```

This signature is included in the `Authorization` header of each POST request to Azure, verifying both the sender's identity and the request's integrity.

## Configuration

The application requires three environment variables:

- **`AZURE_WORKSPACE_ID`**: Your Azure Log Analytics workspace identifier
- **`AZURE_PRIMARY_KEY`**: The primary or secondary shared key from your Log Analytics workspace
- **`DISCORD_WEBHOOK`**: (Optional) Discord webhook URL for instant outage notifications

## Deployment

Build and run the container with your credentials:

```bash
docker run -d \
  --name azure-watchdog \
  --restart unless-stopped \
  -e AZURE_WORKSPACE_ID="your-workspace-id" \
  -e AZURE_PRIMARY_KEY="your-primary-key" \
  -e DISCORD_WEBHOOK="https://discord.com/api/webhooks/..." \
  your-dockerhub-username/azure-watchdog:latest
```

## Monitoring Data

Logs are written to a custom table named `IronBridgeNetMon_CL` in your Log Analytics workspace.

### Sample KQL Query

Query the last 24 hours of connectivity events:

```kql
IronBridgeNetMon_CL
| where TimeGenerated > ago(24h)
| project TimeGenerated, Status_s, Details_s, Server_s
| order by TimeGenerated desc
```

View all outage events:

```kql
IronBridgeNetMon_CL
| where Status_s == "Outage"
| project TimeGenerated, Details_s, Server_s
| order by TimeGenerated desc
```

## Technical Details

- **Language**: Python 3
- **Dependencies**: `requests` (HTTP client)
- **Monitoring Interval**: 10 seconds
- **Connectivity Check**: ICMP ping to 8.8.8.8
- **Log Format**: JSON array with timestamp, status, details, and server identifier
- **Azure API Endpoint**: `https://{workspace-id}.ods.opinsights.azure.com/api/logs`
- **API Version**: 2016-04-01

## Event Types

- **Startup**: Service initialisation event
- **Outage**: Internet connectivity failure detected

## Licence

MIT
