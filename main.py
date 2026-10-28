"""
PDF 工具箱主入口程序
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from gui import PDFToolboxWindow


def main():
    app = QApplication(sys.argv)
    window = PDFToolboxWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
