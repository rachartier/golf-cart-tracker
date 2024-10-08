#!/bin/sh
set -e # Exit on error

echo "=== App Updater ==="
echo ""

echo "[?] Fetching the latest version of docker-compose.yml ..."
if ! curl -s -o docker-compose.yml https://raw.githubusercontent.com/rachartier/golf-cart-tracker/refs/heads/main/docker-compose.yml; then
    echo "[-] Failed to fetch the latest version of docker-compose.yml"
    exit 1
fi
echo "[+] Successfully fetched the latest version of docker-compose.yml"

echo "[?] Bringing down the app and api containers ..."
if ! docker compose down; then
    echo "[-] Failed to bring down the app and api containers"
    exit 1
fi
echo "[+] Successfully brought down the app and api containers"

echo "[?] Pulling the latest images for the app and api containers ..."
if ! docker compose pull; then
    echo "[-] Failed to pull the latest images for the app and api containers"
    exit 1
fi
echo "[+] Successfully pulled the latest images for the app and api containers"

echo "[?] Daemonizing the app and api containers ..."
if ! docker compose up -d; then
    echo "[-] Failed to daemonize the app and api containers"
    exit 1
fi
echo "[+] Successfully daemonized the app and api containers"

echo "[+] Successfully updated the app and api containers"
