"""Allow running the GUI as a module: python -m gdrive_download.gui"""

import sys
from PyQt5.QtWidgets import QApplication

from gdrive_download.gui.main_window import MainWindow


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Google Drive Tools")
    app.setOrganizationName("GivingTuesday")
    app.setOrganizationDomain("givingtuesday.org")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
