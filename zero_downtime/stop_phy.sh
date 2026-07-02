#!/bin/bash

echo "========================================="
echo "PHYSICAL REPLICATION - STOP/RESET"
echo "========================================="
echo "1. Stop only (preserve data)"
echo "2. Stop + Reset (delete all data)"
echo "0. Exit"
read -p "Enter choice: " choice

case $choice in
    1)
        echo "🛑 Stopping physical containers..."
        docker compose -f docker-compose.physical.yml down 2>/dev/null
        docker rm -f zero_downtime_physical_primary zero_downtime_physical_standby 2>/dev/null
        echo "✅ Stopped. Data preserved."
        echo "   Start: ./run_physical.sh → option 1"
        ;;
    2)
        echo "🗑️  Resetting physical lab..."
        read -p "Delete all data? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            docker compose -f docker-compose.physical.yml down -v 2>/dev/null
            docker volume rm zero_downtime_physical_primary_data zero_downtime_physical_standby_data 2>/dev/null
            echo "✅ Reset complete. All data deleted."
            echo "   Start fresh: ./run_physical.sh → option 1"
        else
            echo "Cancelled."
        fi
        ;;
    0)
        echo "Exiting..."
        ;;
    *)
        echo "Invalid option"
        ;;
esac