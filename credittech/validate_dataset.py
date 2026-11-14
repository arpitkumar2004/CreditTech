import sys
from src.validate_dataset import run_all_validation_checks

if __name__ == "__main__":
    d_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    run_all_validation_checks(data_dir=d_dir)

