import sys
from prepare_replenishment import prepare_replenishment
from populate_production import populate_production
from sync_shiphero import sync_shiphero

# Command line instructions

    # Preparing replenishment worksheet
    # Get fresh data with % python main.py prepare_replenishment
    # Use cached data with % python main.py prepare_replenishment --use-cache_stock_levels --use-cache_sales

    # Pushing draft purchase orders from replenishment worksheet to Production Airtable base
    # python main.py populate_production

    # Sync purchase order data with ShipHero
    # work in progress

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <task>")
        print("Tasks: prepare_replenishment, populate_production")
        sys.exit(1)

    task = sys.argv[1]
    use_cache_stock_levels = '--use-cache-stock-levels' in sys.argv
    use_cache_sales = '--use-cache-sales' in sys.argv

    if task == "prepare_replenishment":
        prepare_replenishment(use_cache_stock_levels, use_cache_sales)
    elif task == "populate_production":
        populate_production()
    elif task == "sync_shiphero":
        sync_shiphero()
    
    else:
        print(f"Unknown task: {task}")
        print("Tasks: prepare_replenishment, populate_production")
        sys.exit(1)

if __name__ == "__main__":
    main()