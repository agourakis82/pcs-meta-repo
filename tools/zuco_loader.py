import sys
from pathlib import Path

# Add src to sys.path for direct execution without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pcs_toolbox.zuco import load_all  # noqa: E402

if __name__ == "__main__":
    load_all(write_outputs=True)
