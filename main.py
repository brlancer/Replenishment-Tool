import sys
from prepare_replenishment import prepare_replenishment
from populate_airtable_production import populate_airtable_production

def run_prepare_replenishment():
    prepare_replenishment()

def run_populate_production():
    populate_airtable_production()

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <task>")
        print("Tasks: prepare_replenishment, populate_airtable")
        sys.exit(1)

    task = sys.argv[1]

    if task == "prepare_replenishment":
        run_prepare_replenishment()
    elif task == "populate_airtable":
        run_populate_production()
    
    else:
        print(f"Unknown task: {task}")
        print("Tasks: prepare_replenishment, populate_airtable")
        sys.exit(1)

if __name__ == "__main__":
    main()