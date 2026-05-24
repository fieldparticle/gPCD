import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyReportCode.FLIP_VELOCITY_DIAGNOSTIC import FLIP_VELOCITY_DIAGNOSTIC


if __name__ == "__main__":
    output = FLIP_VELOCITY_DIAGNOSTIC().run()
    print(f"Wrote {output}")
