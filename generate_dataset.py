import sys
from src.generate_dataset import generate_all_datasets

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    generate_all_datasets(output_dir=out_dir)

