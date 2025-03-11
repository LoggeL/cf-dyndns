# Cloudflare Dynamic DNS Updater

A Python script that automatically updates your Cloudflare DNS records with your current public IP address. This is useful if you have a dynamic IP address but want to maintain a consistent domain name that points to your home server, NAS, or other services.

## Features

- Automatically detects your current public IP address
- Updates your Cloudflare DNS record only when your IP changes
- Configurable check intervals
- Detailed logging
- Runs as a background process
- Supports both proxied and unproxied DNS records
- Can automatically discover your DNS record ID based on domain name
- Secure authentication using Cloudflare API tokens

## Requirements

- Python 3.6+
- A Cloudflare account with:
  - A domain name
  - API access (API Token)
  - An existing DNS record to update

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/cf-dyndns.git
   cd cf-dyndns
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create your `.env` file by copying the example:

   ```
   copy .env.example .env
   ```

4. Edit the `.env` file with your Cloudflare credentials and configuration.

## Configuration

Edit the `.env` file with your specific details:

```
# Cloudflare API credentials
CLOUDFLARE_API_TOKEN=your-api-token

# Cloudflare zone and record IDs
ZONE_ID=your-zone-id
# DNS_RECORD_ID is optional if you provide DOMAIN_NAME
# DNS_RECORD_ID=your-dns-record-id

# Domain configuration
DOMAIN_NAME=your-domain.com
RECORD_TYPE=A
TTL=3600
PROXIED=true

# Script settings
CHECK_INTERVAL=300  # Check every 5 minutes (in seconds)
```

### About Cloudflare API Tokens

This script uses Cloudflare's API Token authentication method, which is more secure than the older Global API Key method. To create a token:

1. Log in to your Cloudflare dashboard
2. Navigate to "Profile" > "API Tokens"
3. Click "Create Token"
4. Use the "Edit Zone DNS" template or create a custom token with the following permissions:
   - Zone > DNS > Edit permissions
   - Include the specific zone you want to update

### Finding Your Cloudflare Zone ID

**Zone ID**: Log into your Cloudflare dashboard, select your domain, and the Zone ID is displayed in the "Overview" tab's API section.

### About DNS Record ID

There are two ways to specify which DNS record should be updated:

1. **Automatic Discovery**: Simply provide your `DOMAIN_NAME` and `RECORD_TYPE` in the `.env` file, and the script will automatically find the corresponding DNS record ID for you.

2. **Manual Specification**: If you have multiple records with the same name and type, or if you prefer to explicitly specify which record to update, you can set the `DNS_RECORD_ID` in your `.env` file. You can find this ID in your Cloudflare dashboard by going to the DNS tab and clicking on the record you want to update.

## Usage

Run the script:

```
python cf_dyndns.py
```

The script will:

1. Check your current public IP address
2. Compare it with your Cloudflare DNS record
3. Update the record if they differ
4. Wait for the specified interval before checking again
5. Log all activities to both console and a log file

## Setting Up as a Windows Service

To run this script as a background service on Windows:

1. Create a batch file `start_cf_dyndns.bat`:

   ```batch
   @echo off
   cd /d %~dp0
   python cf_dyndns.py
   ```

2. Create a scheduled task:
   - Open Task Scheduler
   - Create a new task
   - Set it to run with highest privileges
   - Configure it to run on startup
   - Add a new action to start the batch file
   - Set it to restart if it fails

## Troubleshooting

Check the `cf_dyndns.log` file for detailed error messages.

Common issues:

- Incorrect API token or insufficient permissions
- Incorrect Zone ID or DNS Record ID
- Network connectivity problems
- Multiple DNS records with the same name (in this case, specify DNS_RECORD_ID manually)

## License

This project is licensed under the MIT License.
