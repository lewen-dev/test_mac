import sys
import resources_rc
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.win import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/johnson.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
