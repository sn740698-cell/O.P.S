"""
O.P.S. 2.0 — Desktop Overlay Entrypoint
Initializes and launches the O.P.S. Native Floating Desktop Cockpit Daemon.
"""

import sys
import os
import signal
import logging
import argparse

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from desktop_overlay.window import FloatingCockpitWindow
from desktop_overlay.visibility_controller import CockpitVisibilityController

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("OPSDesktopOverlay.Main")


def main():
    parser = argparse.ArgumentParser(description="O.P.S. 2.0 Floating Desktop Cockpit Daemon")
    parser.add_argument("--frontend-url", default="http://localhost:3000/?mode=cockpit", help="URL of the Cockpit frontend")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="URL of the Django backend")
    parser.add_argument("--start-hidden", action="store_true", help="Start the cockpit hidden in background")
    args = parser.parse_args()

    logger.info("Initializing O.P.S. 2.0 Desktop Overlay System...")

    # Enable high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("O.P.S. Pop-up Cockpit")
    app.setQuitOnLastWindowClosed(False)

    # 1. Create native floating window
    window = FloatingCockpitWindow(frontend_url=args.frontend_url)

    # 2. Create visibility controller
    controller = CockpitVisibilityController(
        window=window,
        backend_url=args.backend_url
    )

    # 3. Start controller (hotkeys and HITL monitor)
    if not controller.start():
        logger.error("Failed to acquire single instance lock or start hotkeys. Exiting.")
        sys.exit(1)

    # Clean shutdown handler
    def cleanup():
        logger.info("Shutting down Desktop Cockpit Daemon...")
        controller.stop()

    app.aboutToQuit.connect(cleanup)

    # Signal handlers
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())

    # 4. Initial presentation
    if not args.start_hidden:
        controller.request_show()
    else:
        logger.info("Cockpit running in background.")

    logger.info("======================================================================")
    logger.info(" O.P.S. 2.0 DESKTOP COCKPIT OVERLAY IS ACTIVE AND READY               ")
    logger.info(" - Press [ Ctrl + Alt ]       : OPEN / SHOW Pop-up Cockpit            ")
    logger.info(" - Press [ Ctrl + Alt + Space ]: CLOSE / HIDE Pop-up Cockpit          ")
    logger.info("======================================================================")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
