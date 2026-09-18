from datetime import datetime

"""Launch the futureRunning dashboard."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    if os.environ.get("DISPLAY"):
        from futurerunning.gui import launch_gui
        launch_gui()
    else:
        from futurerunning.web import launch_web
        launch_web()