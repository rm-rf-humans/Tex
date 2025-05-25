import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QToolBar, QAction, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
                             QToolBox, QPushButton, QLabel, QSpinBox, QLineEdit,
                             QTextEdit, QSplitter, QFileDialog, QMessageBox, QGroupBox,
                             QFormLayout, QComboBox)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPixmap
from pylatex import Document, TikZ, Command
from pylatex.tikz import TikZNode, TikZDraw
from logic.gates import Gates


class GateItem(QGraphicsRectItem):
    """Custom graphics item for logic gates"""
    
    def __init__(self, gate_type, x, y, inputs="nn"):
        super().__init__()
        self.gate_type = gate_type
        self.inputs = inputs
        self.setRect(0, 0, 80, 60)
        self.setPos(x, y)
        
        # Make it movable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Style
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setBrush(QBrush(QColor(255, 255, 255)))
        
        # Add text label
        self.text_item = QGraphicsTextItem(gate_type, self)
        self.text_item.setPos(10, 20)
        self.text_item.setFont(QFont("Arial", 10, QFont.Bold))
        
    def get_tikz_code(self):
        """Generate TikZ code for this gate using PyLaTeX"""
        gate = Gates()
        gate.set_position(self.pos().x() / 50, -self.pos().y() / 50)  # Scale for TikZ
        gate.set_inputs(self.inputs)
        return gate.get_gate(self.gate_type)
    
    def get_pylatex_node(self, node_name=""):
        """Generate PyLaTeX node for this gate"""
        gate = Gates()
        gate.set_position(self.pos().x() / 50, -self.pos().y() / 50)
        gate.set_inputs(self.inputs)
        return gate.get_pylatex_node(self.gate_type, node_name=node_name)


class WireItem(QGraphicsItem):
    """Custom graphics item for wires/connections"""
    
    def __init__(self, start_point, end_point):
        super().__init__()
        self.start_point = start_point
        self.end_point = end_point
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
    def boundingRect(self):
        return QRectF(self.start_point, self.end_point).normalized()
        
    def paint(self, painter, option, widget):
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(self.start_point, self.end_point)
        
    def get_tikz_code(self):
        """Generate TikZ code for this wire"""
        x1, y1 = self.start_point.x() / 50, -self.start_point.y() / 50
        x2, y2 = self.end_point.x() / 50, -self.end_point.y() / 50
        return f"\\draw ({x1:.2f}, {y1:.2f}) -- ({x2:.2f}, {y2:.2f});"
    
    def get_pylatex_draw(self):
        """Generate PyLaTeX draw command for this wire"""
        x1, y1 = self.start_point.x() / 50, -self.start_point.y() / 50
        x2, y2 = self.end_point.x() / 50, -self.end_point.y() / 50
        return TikZDraw([f"({x1:.2f}, {y1:.2f})", '--', f"({x2:.2f}, {y2:.2f})"])


class CircuitCanvas(QGraphicsView):
    """Main canvas for drawing circuits"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Set up the view
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Drawing state
        self.current_tool = "select"
        self.drawing_wire = False
        self.wire_start = None
        
        # Set scene size
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        
    def set_tool(self, tool):
        """Set the current drawing tool"""
        self.current_tool = tool
        if tool == "select":
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
    
    def mousePressEvent(self, event):
        if self.current_tool == "select":
            super().mousePressEvent(event)
        elif self.current_tool == "wire":
            scene_pos = self.mapToScene(event.pos())
            if not self.drawing_wire:
                self.wire_start = scene_pos
                self.drawing_wire = True
            else:
                # Complete the wire
                wire = WireItem(self.wire_start, scene_pos)
                self.scene.addItem(wire)
                self.drawing_wire = False
                self.wire_start = None
        elif self.current_tool in ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"]:
            scene_pos = self.mapToScene(event.pos())
            gate = GateItem(self.current_tool, scene_pos.x(), scene_pos.y())
            self.scene.addItem(gate)
    
    def get_all_tikz_code(self):
        """Generate TikZ code for all items in the scene"""
        tikz_code = []
        tikz_code.append("\\begin{tikzpicture}[circuit logic US]")
        
        for item in self.scene.items():
            if isinstance(item, GateItem):
                tikz_code.append(item.get_tikz_code())
            elif isinstance(item, WireItem):
                tikz_code.append(item.get_tikz_code())
        
        tikz_code.append("\\end{tikzpicture}")
        return "\n".join(tikz_code)
    
    def get_pylatex_tikz(self):
        """Generate PyLaTeX TikZ object for all items in the scene"""
        tikz = TikZ(options=['circuit logic US'])
        
        # Add all gates
        for item in self.scene.items():
            if isinstance(item, GateItem):
                node = item.get_pylatex_node()
                tikz.append(node)
            elif isinstance(item, WireItem):
                draw = item.get_pylatex_draw()
                tikz.append(draw)
        
        return tikz
    
    def generate_complete_document(self):
        """Generate a complete LaTeX document with the circuit"""
        doc = Document(geometry_options={"margin": "1in"})
        
        # Add required packages
        doc.packages.append(Command('usepackage', 'circuitikz'))
        
        with doc.create(TikZ(options=['circuit logic US'])) as tikz:
            # Add all gates and wires
            for item in self.scene.items():
                if isinstance(item, GateItem):
                    node = item.get_pylatex_node()
                    tikz.append(node)
                elif isinstance(item, WireItem):
                    draw = item.get_pylatex_draw()
                    tikz.append(draw)
        
        return doc


class ToolPanel(QWidget):
    """Tool panel with gate selection and properties"""
    
    tool_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Selection tools
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(lambda: self.tool_selected.emit("select"))
        tools_layout.addWidget(select_btn)
        
        wire_btn = QPushButton("Wire")
        wire_btn.clicked.connect(lambda: self.tool_selected.emit("wire"))
        tools_layout.addWidget(wire_btn)
        
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        # Logic gates
        gates_group = QGroupBox("Logic Gates")
        gates_layout = QVBoxLayout()
        
        gate_types = ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"]
        for gate in gate_types:
            btn = QPushButton(gate)
            btn.clicked.connect(lambda checked, g=gate: self.tool_selected.emit(g))
            gates_layout.addWidget(btn)
        
        gates_group.setLayout(gates_layout)
        layout.addWidget(gates_group)
        
        # Properties
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()
        
        self.inputs_combo = QComboBox()
        self.inputs_combo.addItems(["n", "nn", "nnn", "nnnn"])
        props_layout.addRow("Inputs:", self.inputs_combo)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        layout.addStretch()
        self.setLayout(layout)


class CodeViewer(QWidget):
    """Panel to view and edit generated TikZ code"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Label
        label = QLabel("Generated TikZ Code:")
        layout.addWidget(label)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(self.text_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        update_btn = QPushButton("Update Code")
        update_btn.clicked.connect(self.update_code_requested)
        btn_layout.addWidget(update_btn)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf_requested)
        btn_layout.addWidget(export_pdf_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def update_code_requested(self):
        """Signal to update the code from the canvas"""
        pass  # Will be connected to main window
        
    def export_pdf_requested(self):
        """Signal to export PDF from the canvas"""
        pass  # Will be connected to main window
        
    def copy_to_clipboard(self):
        """Copy code to clipboard"""
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        
    def set_code(self, code):
        """Set the displayed code"""
        self.text_edit.setText(code)


class LaTeXCircuitDesigner(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("LaTeX Circuit Designer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        
        # Tool panel
        self.tool_panel = ToolPanel()
        self.tool_panel.setMaximumWidth(200)
        splitter.addWidget(self.tool_panel)
        
        # Canvas
        self.canvas = CircuitCanvas()
        splitter.addWidget(self.canvas)
        
        # Code viewer
        self.code_viewer = CodeViewer()
        self.code_viewer.setMaximumWidth(350)
        splitter.addWidget(self.code_viewer)
        
        # Set splitter proportions
        splitter.setSizes([200, 650, 350])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_circuit)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_circuit)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_circuit)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('Export TikZ', self)
        export_action.triggered.connect(self.export_tikz)
        file_menu.addAction(export_action)
        
        export_pdf_action = QAction('Export PDF', self)
        export_pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_action)
        
        export_tex_action = QAction('Export Complete Document', self)
        export_tex_action.triggered.connect(self.export_complete_document)
        file_menu.addAction(export_tex_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        delete_action = QAction('Delete', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.tool_panel.tool_selected.connect(self.canvas.set_tool)
        self.code_viewer.export_pdf_requested = self.export_pdf
        
    def new_circuit(self):
        """Create a new circuit"""
        self.canvas.scene.clear()
        self.update_code()
        
    def open_circuit(self):
        """Open a circuit file"""
        # Placeholder - would implement file loading
        QMessageBox.information(self, "Info", "Open functionality not yet implemented")
        
    def save_circuit(self):
        """Save the current circuit"""
        # Placeholder - would implement file saving
        QMessageBox.information(self, "Info", "Save functionality not yet implemented")
        
    def export_tikz(self):
        """Export TikZ code to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export TikZ Code", "", "LaTeX Files (*.tex);;All Files (*)"
        )
        if filename:
            try:
                code = self.canvas.get_all_tikz_code()
                with open(filename, 'w') as f:
                    f.write(code)
                QMessageBox.information(self, "Success", f"TikZ code exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def export_pdf(self):
        """Export circuit as PDF using PyLaTeX"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if filename:
            try:
                doc = self.canvas.generate_complete_document()
                doc.generate_pdf(filename.replace('.pdf', ''), clean_tex=False)
                QMessageBox.information(self, "Success", f"PDF exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")
    
    def export_complete_document(self):
        """Export complete LaTeX document"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Complete Document", "", "LaTeX Files (*.tex);;All Files (*)"
        )
        if filename:
            try:
                doc = self.canvas.generate_complete_document()
                doc.generate_tex(filename.replace('.tex', ''))
                QMessageBox.information(self, "Success", f"Complete document exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export document: {str(e)}")
                
    def delete_selected(self):
        """Delete selected items"""
        selected_items = self.canvas.scene.selectedItems()
        for item in selected_items:
            self.canvas.scene.removeItem(item)
        self.update_code()
        
    def update_code(self):
        """Update the displayed TikZ code"""
        code = self.canvas.get_all_tikz_code()
        self.code_viewer.set_code(code)


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("LaTeX Circuit Designer")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = LaTeXCircuitDesigner()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
