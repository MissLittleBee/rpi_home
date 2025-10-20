#!/bin/bash

# Scheduled sync script - runs every 10 minutes
# This ensures both Jellyfin and Nextcloud stay in sync

# Get script directory and project root for proper path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/scheduled-sync.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Load configuration if available
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Wait for Docker containers to be ready after reboot
wait_for_containers() {
    local max_wait=300  # 5 minutes max wait
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if docker ps | grep -q "nextcloud" && docker ps | grep -q "jellyfin"; then
            log "Containers are ready"
            return 0
        fi
        log "Waiting for containers to start... (${wait_time}s)"
        sleep 10
        wait_time=$((wait_time + 10))
    done
    
    log "ERROR: Timeout waiting for containers"
    return 1
}

get_nextcloud_container() {
    docker ps --format "table {{.ID}}\t{{.Image}}" | grep "nextcloud" | awk '{print $1}' | head -1
}

# Quick Nextcloud scan (only new/changed files)
quick_nextcloud_scan() {
    local container_id=$(get_nextcloud_container)
    if [ -n "$container_id" ]; then
        log "Running quick Nextcloud sync..."
        docker exec -u www-data "$container_id" php /var/www/html/occ files:scan --shallow jeyjey 2>/dev/null
        log "Nextcloud quick sync completed"
    else
        log "ERROR: Nextcloud container not found"
    fi
}

# Jellyfin API library refresh (non-disruptive)
jellyfin_library_refresh() {
    local container_id=$(docker ps --format "table {{.ID}}\t{{.Image}}" | grep "jellyfin" | awk '{print $1}' | head -1)
    if [ -n "$container_id" ]; then
        log "Refreshing Jellyfin library via API..."
        # Try to refresh via API first (less disruptive)
        docker exec "$container_id" curl -s -X POST "http://localhost:8096/Library/Refresh" -H "Content-Type: application/json" &>/dev/null
        log "Jellyfin library refresh triggered"
    else
        log "ERROR: Jellyfin container not found"
    fi
}

log "Starting scheduled sync job"

# Wait for containers to be ready (important after reboot)
if ! wait_for_containers; then
    log "Sync aborted - containers not ready"
    exit 1
fi

quick_nextcloud_scan
sleep 2
jellyfin_library_refresh
log "Scheduled sync job completed"