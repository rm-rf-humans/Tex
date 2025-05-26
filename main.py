import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

from logic.gates import LaTeXCircuitDesigner

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaTeX Circuit Suite")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add tabs
        self.tabs.addTab(LaTeXCircuitDesigner(), "Gates")

def main():
    app = QApplication(sys.argv)

    window = MainApp()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
