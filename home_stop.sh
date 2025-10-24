#!/bin/bash
# home_stop.sh: Stop and remove Docker Swarm stack, containers, and perform cleanup

set -e

STACK_NAME="rpi_home"

# Check if stack exists before trying to remove it
if docker stack ls --format "table {{.Name}}" | grep -q "^${STACK_NAME}$"; then
    echo "Removing Docker stack: $STACK_NAME..."
    docker stack rm "$STACK_NAME"
    
    # Wait for services to be removed (with progress indicator)
    echo "Waiting for stack services to stop..."
    while docker stack ls --format "table {{.Name}}" | grep -q "^${STACK_NAME}$"; do
        echo -n "."
        sleep 2
    done
    echo ""
    echo "Stack $STACK_NAME removed successfully."
else
    echo "Stack $STACK_NAME is not running or doesn't exist."
fi

# Optional: Clean up unused Docker resources (networks, images, build cache)
echo ""
echo "🧹 Docker Resource Cleanup Options:"
echo "This will remove:"
echo "  • Unused Docker networks (not currently used by running containers)"
echo "  • Dangling/unused Docker images (saves disk space)"
echo "  • Build cache and temporary files"
echo "  • Stopped containers from previous runs"
echo ""
echo "This will NOT remove:"
echo "  ✅ Your data volumes (Nextcloud files, Home Assistant config, etc.)"
echo "  ✅ Currently running containers from other projects"
echo "  ✅ Images currently in use by running containers"
echo ""
read -p "Do you want to clean up unused Docker resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning up unused Docker resources..."
    docker system prune -f --volumes=false  # Preserve volumes but clean networks, containers, images
    echo "Docker cleanup completed."
fi

# Cleanup: Do NOT remove persistent data directories (volumes)
# Only remove stack and containers

# Optional: Remove automation cron jobs
echo ""
echo "🔄 Automation Cleanup Options:"
echo "This will remove:"
echo "  • Cron jobs that sync Nextcloud and Plex libraries every 10 minutes"
echo "  • Cron jobs that run Docker cleanup every 6 hours"
echo "  • Reboot jobs that run sync and cleanup after system restart"
echo ""
echo "This will NOT remove:"
echo "  ✅ Your media files or library metadata" 
echo "  ✅ Your data volumes (Nextcloud files, Home Assistant config, etc.)"
echo "  ✅ Currently running containers and their images"
echo "  ✅ Sync logs (you can still check logs/ directory)"
echo "  ✅ Cleanup logs (logs/scheduled-cleanup.log)"
echo "  ✅ The scripts themselves (tools/scheduled-sync.sh, tools/scheduled-cleanup.sh)"
echo ""
echo "Note: You can re-enable all automation by running './home_start.sh' again"
echo ""
read -p "Do you want to remove all automation cron jobs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing automation cron jobs..."
    crontab -r 2>/dev/null || echo "No cron jobs to remove"
    
    # Also clean up any existing systemd timers if they exist (legacy cleanup)
    if sudo systemctl is-enabled docker-cleanup.timer >/dev/null 2>&1; then
        echo "Also removing existing systemd cleanup timer..."
        sudo systemctl stop docker-cleanup.timer 2>/dev/null
        sudo systemctl disable docker-cleanup.timer 2>/dev/null
        sudo rm -f /etc/systemd/system/docker-cleanup.service /etc/systemd/system/docker-cleanup.timer 2>/dev/null
        sudo systemctl daemon-reload 2>/dev/null
        echo "Legacy systemd timer removed"
    fi
    
    echo "Automation jobs removed."
fi

echo ""
echo "Cleanup complete. Stack and containers removed. Persistent data (volumes) preserved."
echo ""
echo "📋 What was preserved:"
echo "  • Media library and all your video files"
echo "  • volumes/nextcloud/ (user files and database)"
echo "  • volumes/homeassistant/ (configuration and data)"
echo "  • volumes/plex/ (metadata and settings)"
echo "  • tools/.env file (your configuration settings)"
echo "  • logs/ (sync and error logs)"
echo "  • logs/scheduled-cleanup.log (cleanup logs, if automation was kept)"
echo ""
echo "🚀 To restart the services: Run './home_start.sh'"
