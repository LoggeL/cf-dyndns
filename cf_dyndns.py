#!/usr/bin/env python3
"""
Cloudflare Dynamic DNS Updater

This script automatically updates a Cloudflare DNS record with your current public IP address.
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("cf_dyndns.log")],
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Cloudflare API settings
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ZONE_ID = os.getenv("ZONE_ID")
DNS_RECORD_ID = os.getenv("DNS_RECORD_ID")
DOMAIN_NAME = os.getenv("DOMAIN_NAME")
RECORD_TYPE = os.getenv("RECORD_TYPE", "A")
TTL = int(os.getenv("TTL", "3600"))
PROXIED = os.getenv("PROXIED", "false").lower() == "true"
CHECK_INTERVAL = int(
    os.getenv("CHECK_INTERVAL", "300")
)  # Check every 5 minutes by default


def get_current_ip():
    """Get the current public IP address."""
    try:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to get IP: {response.status_code}")
    except Exception as e:
        logger.error(f"Error getting current IP: {str(e)}")
        raise


def get_dns_record_id(zone_id, domain_name, record_type="A"):
    """
    Get the DNS record ID for a specific domain name and record type.

    Args:
        zone_id (str): The Cloudflare Zone ID
        domain_name (str): The domain name to look for
        record_type (str): The DNS record type (default: A)

    Returns:
        str: The DNS record ID if found, None otherwise
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Add parameters to filter the results
    params = {"name": domain_name, "type": record_type}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            if (
                result.get("success")
                and result.get("result")
                and len(result["result"]) > 0
            ):
                # Return the ID of the first matching record
                record_id = result["result"][0]["id"]
                logger.info(f"Found DNS record ID for {domain_name}: {record_id}")
                return record_id
            else:
                logger.error(
                    f"No DNS records found for {domain_name} of type {record_type}"
                )
                return None
        else:
            logger.error(
                f"Failed to get DNS records: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Error getting DNS record ID: {str(e)}")
        return None


def get_cloudflare_dns_record():
    """Get the current Cloudflare DNS record."""
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{DNS_RECORD_ID}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"Failed to get DNS record: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Error getting Cloudflare DNS record: {str(e)}")
        return None


def update_cloudflare_dns_record(current_ip):
    """Update Cloudflare DNS record with the current IP."""
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{DNS_RECORD_ID}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "type": RECORD_TYPE,
        "name": DOMAIN_NAME,
        "content": current_ip,
        "ttl": TTL,
        "proxied": PROXIED,
    }

    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully updated DNS record to {current_ip}")
                return True
            else:
                logger.error(f"API returned success=false: {result}")
                return False
        else:
            logger.error(
                f"Failed to update DNS record: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error updating Cloudflare DNS record: {str(e)}")
        return False


def check_and_update():
    """Check current IP and update Cloudflare if needed."""
    try:
        # Get current public IP
        current_ip = get_current_ip()
        logger.info(f"Current public IP: {current_ip}")

        # Get current DNS record
        dns_record = get_cloudflare_dns_record()
        if not dns_record:
            logger.error("Failed to retrieve DNS record. Skipping update.")
            return

        # Extract current IP from DNS record
        cf_ip = dns_record.get("result", {}).get("content")
        logger.info(f"Current Cloudflare DNS record IP: {cf_ip}")

        # Update if IPs don't match
        if current_ip != cf_ip:
            logger.info(
                f"IP address has changed from {cf_ip} to {current_ip}. Updating..."
            )
            if update_cloudflare_dns_record(current_ip):
                logger.info("DNS record updated successfully")
            else:
                logger.error("Failed to update DNS record")
        else:
            logger.info("IP address unchanged. No update needed.")

    except Exception as e:
        logger.error(f"Error in check_and_update: {str(e)}")


def main():
    """Main function to run the script."""
    logger.info("Starting Cloudflare Dynamic DNS updater")

    # Check if all required environment variables are set
    missing_vars = []
    for var in [
        "CLOUDFLARE_API_TOKEN",
        "ZONE_ID",
    ]:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please check your .env file and try again")
        return

    # If DNS_RECORD_ID is not provided, try to get it automatically
    global DNS_RECORD_ID
    if not DNS_RECORD_ID:
        if not DOMAIN_NAME:
            logger.error(
                "Both DNS_RECORD_ID and DOMAIN_NAME are missing. At least one is required."
            )
            return

        logger.info(
            f"DNS_RECORD_ID not provided. Attempting to find it automatically for {DOMAIN_NAME}..."
        )
        DNS_RECORD_ID = get_dns_record_id(ZONE_ID, DOMAIN_NAME, RECORD_TYPE)

        if not DNS_RECORD_ID:
            logger.error(
                f"Could not find DNS record ID for {DOMAIN_NAME}. Please provide it manually in .env file."
            )
            return
        else:
            logger.info(f"Using DNS record ID: {DNS_RECORD_ID}")

    logger.info(f"Will check for IP changes every {CHECK_INTERVAL} seconds")

    try:
        while True:
            check_and_update()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
