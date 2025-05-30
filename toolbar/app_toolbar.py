from PyQt5.QtWidgets import QToolBar, QAction

class HorizontalActionsToolbar(QToolBar):
    def __init__(self, parent_window):
        super().__init__("Main Toolbar", parent_window)
        self.parent_window = parent_window
        self._create_actions()

    def _create_actions(self):
        self.select_action = QAction("Select", self.parent_window)
        self.select_action.setShortcut('Ctrl+A')
        self.select_action.triggered.connect(lambda: self.parent_window.canvas.set_tool("select"))
        self.addAction(self.select_action)

        self.wire_action = QAction("Wire", self.parent_window)
        self.wire_action.setShortcut('Ctrl+W') # Changed from Ctrl+w for consistency
        self.wire_action.triggered.connect(lambda: self.parent_window.canvas.set_tool("wire"))
        self.addAction(self.wire_action)

        self.addSeparator()

        self.new_action = QAction("New", self.parent_window)
        self.new_action.setShortcut('Ctrl+N')
        self.new_action.triggered.connect(self.parent_window.new_circuit)
        self.addAction(self.new_action)

        self.open_action = QAction("Open", self.parent_window)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.triggered.connect(self.parent_window.open_circuit)
        self.addAction(self.open_action)

        self.save_action = QAction("Save", self.parent_window)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.parent_window.save_circuit)
        self.addAction(self.save_action)

        self.addSeparator()

        self.export_tikz_action = QAction("Export TikZ", self.parent_window)
        self.export_tikz_action.triggered.connect(self.parent_window.export_tikz)
        self.addAction(self.export_tikz_action)

        self.export_pdf_action = QAction("Export PDF", self.parent_window)
        self.export_pdf_action.triggered.connect(self.parent_window.export_pdf)
        self.addAction(self.export_pdf_action)
        
        self.export_tex_action = QAction("Export .tex", self.parent_window)
        self.export_tex_action.triggered.connect(self.parent_window.export_complete_document)
        self.addAction(self.export_tex_action)

        self.addSeparator()

        self.delete_action = QAction("Delete", self.parent_window)
        self.delete_action.setShortcut('Delete') # Standard shortcut
        self.delete_action.triggered.connect(self.parent_window.delete_selected)
        self.addAction(self.delete_action)

        self.rotate_action = QAction("Rotate Gate", self.parent_window) # New Action
        self.rotate_action.setShortcut('Ctrl+R')
        self.addAction(self.rotate_action)