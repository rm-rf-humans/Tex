import sys
import os
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QToolBar, QAction, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
                             QToolBox, QPushButton, QLabel, QSpinBox, QLineEdit,
                             QTextEdit, QSplitter, QFileDialog, QMessageBox, QGroupBox,
                             QFormLayout, QComboBox, QGraphicsEllipseItem, QGraphicsPolygonItem,
                             QGraphicsPathItem)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPixmap, QPolygonF, QPainterPath
from pylatex import Document, TikZ, Command
from pylatex.tikz import TikZNode, TikZDraw


class ConnectionPoint(QGraphicsEllipseItem):
    """Visual connection point for gate inputs/outputs"""
    
    def __init__(self, parent_gate, point_type, index, x, y):
        super().__init__(-3, -3, 6, 6)  # Small circle
        self.parent_gate = parent_gate
        self.point_type = point_type  # 'input' or 'output'
        self.index = index
        self.setPos(x, y)
        self.setParentItem(parent_gate)
        
        # Style
        self.setPen(QPen(QColor(100, 100, 100), 1))
        self.setBrush(QBrush(QColor(200, 200, 200)))
        
        # Make it hoverable
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        # Connected wires
        self.connected_wires = []
        
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(255, 100, 100)))
        self.setPen(QPen(QColor(255, 0, 0), 2))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(200, 200, 200)))
        self.setPen(QPen(QColor(100, 100, 100), 1))
        super().hoverLeaveEvent(event)
    
    def get_scene_pos(self):
        """Get the absolute scene position of this connection point"""
        return self.mapToScene(self.boundingRect().center())
    
    def add_wire(self, wire):
        """Add a wire connected to this point"""
        self.connected_wires.append(wire)
    
    def remove_wire(self, wire):
        """Remove a wire from this point"""
        if wire in self.connected_wires:
            self.connected_wires.remove(wire)


class GateItem(QGraphicsItem):
    """Custom graphics item for logic gates with proper shapes"""
    
    def __init__(self, gate_type, x, y, inputs=2):
        super().__init__()
        self.gate_type = gate_type
        self.num_inputs = inputs
        self.setPos(x, y)
        
        # Make it movable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Gate dimensions
        self.width = 80
        self.height = 60
        
        # Connection points
        self.input_points = []
        self.output_points = []
        
        self.create_connection_points()
        
    def create_connection_points(self):
        """Create input and output connection points"""
        # Clear existing points
        for point in self.input_points + self.output_points:
            if point.scene():
                point.scene().removeItem(point)
        
        self.input_points = []
        self.output_points = []
        
        # Create input points (left side)
        input_spacing = self.height / (self.num_inputs + 1)
        for i in range(self.num_inputs):
            y_pos = input_spacing * (i + 1) - self.height/2
            point = ConnectionPoint(self, 'input', i, -10, y_pos)
            self.input_points.append(point)
        
        # Create output point (right side)
        output_point = ConnectionPoint(self, 'output', 0, self.width + 10, 0)
        self.output_points.append(output_point)
    
    def boundingRect(self):
        return QRectF(-20, -self.height/2 - 10, self.width + 40, self.height + 20)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set pen and brush
        pen = QPen(QColor(0, 0, 0), 2)
        if self.isSelected():
            pen.setColor(QColor(255, 0, 0))
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        # Draw gate shape based on type
        if self.gate_type == "AND":
            self.draw_and_gate(painter)
        elif self.gate_type == "OR":
            self.draw_or_gate(painter)
        elif self.gate_type == "NOT":
            self.draw_not_gate(painter)
        elif self.gate_type == "NAND":
            self.draw_and_gate(painter)
            self.draw_negation_circle(painter, self.width, 0)
        elif self.gate_type == "NOR":
            self.draw_or_gate(painter)
            self.draw_negation_circle(painter, self.width, 0)
        elif self.gate_type == "XOR":
            self.draw_xor_gate(painter)
        elif self.gate_type == "XNOR":
            self.draw_xor_gate(painter)
            self.draw_negation_circle(painter, self.width, 0)
    
    def draw_and_gate(self, painter):
        """Draw AND gate shape"""
        path = QPainterPath()
        path.moveTo(0, -self.height/2)
        path.lineTo(self.width/2, -self.height/2)
        path.arcTo(self.width/2 - self.height/2, -self.height/2, self.height, self.height, 90, -180)
        path.lineTo(0, self.height/2)
        path.closeSubpath()
        painter.drawPath(path)
    
    def draw_or_gate(self, painter):
        """Draw OR gate shape"""
        path = QPainterPath()
        # Left curved side
        path.moveTo(0, -self.height/2)
        path.quadTo(self.width/4, -self.height/4, self.width/4, 0)
        path.quadTo(self.width/4, self.height/4, 0, self.height/2)
        # Right curved side
        path.quadTo(self.width/2, self.height/4, self.width, 0)
        path.quadTo(self.width/2, -self.height/4, 0, -self.height/2)
        painter.drawPath(path)
    
    def draw_xor_gate(self, painter):
        """Draw XOR gate shape"""
        # Draw OR gate
        self.draw_or_gate(painter)
        # Add extra arc on the left
        path = QPainterPath()
        path.moveTo(-8, -self.height/2)
        path.quadTo(-4, 0, -8, self.height/2)
        painter.drawPath(path)
    
    def draw_not_gate(self, painter):
        """Draw NOT gate shape (triangle with circle)"""
        # Triangle
        triangle = QPolygonF([
            QPointF(0, -self.height/2),
            QPointF(0, self.height/2),
            QPointF(self.width - 10, 0)
        ])
        painter.drawPolygon(triangle)
        
        # Negation circle
        self.draw_negation_circle(painter, self.width - 10, 0)
    
    def draw_negation_circle(self, painter, x, y):
        """Draw negation circle at specified position"""
        painter.drawEllipse(QPointF(x, y), 5, 5)
    
    def itemChange(self, change, value):
        """Handle item changes (like position changes)"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected wires when gate moves
            self.update_connected_wires()
        return super().itemChange(change, value)
    
    def update_connected_wires(self):
        """Update all wires connected to this gate"""
        for point in self.input_points + self.output_points:
            for wire in point.connected_wires:
                wire.update_position()
    
    def get_tikz_code(self):
        """Generate TikZ code for this gate"""
        x, y = self.pos().x() / 50, -self.pos().y() / 50
        
        # Map gate types to TikZ library names
        tikz_gates = {
            "AND": "and gate",
            "OR": "or gate", 
            "NOT": "not gate",
            "NAND": "nand gate",
            "NOR": "nor gate",
            "XOR": "xor gate",
            "XNOR": "xnor gate"
        }
        
        gate_name = tikz_gates.get(self.gate_type, "and gate")
        inputs_spec = f"inputs={self.num_inputs}" if self.num_inputs > 2 else ""
        
        return f"\\node[{gate_name}, {inputs_spec}] at ({x:.2f}, {y:.2f}) {{}};"


class WireItem(QGraphicsItem):
    """Custom graphics item for wires/connections between gates"""
    
    def __init__(self, start_point, end_point):
        super().__init__()
        self.start_connection = start_point  # ConnectionPoint object
        self.end_connection = end_point      # ConnectionPoint object
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Register with connection points
        if start_point:
            start_point.add_wire(self)
        if end_point:
            end_point.add_wire(self)
    
    def boundingRect(self):
        if not (self.start_connection and self.end_connection):
            return QRectF()
        
        start_pos = self.start_connection.get_scene_pos()
        end_pos = self.end_connection.get_scene_pos()
        return QRectF(start_pos, end_pos).normalized().adjusted(-2, -2, 2, 2)
    
    def paint(self, painter, option, widget):
        if not (self.start_connection and self.end_connection):
            return
            
        start_pos = self.mapFromScene(self.start_connection.get_scene_pos())
        end_pos = self.mapFromScene(self.end_connection.get_scene_pos())
        
        pen = QPen(QColor(0, 0, 0), 2)
        if self.isSelected():
            pen.setColor(QColor(255, 0, 0))
        painter.setPen(pen)
        painter.drawLine(start_pos, end_pos)
    
    def update_position(self):
        """Update wire position when connected gates move"""
        self.prepareGeometryChange()
        self.update()
    
    def get_tikz_code(self):
        """Generate TikZ code for this wire"""
        if not (self.start_connection and self.end_connection):
            return ""
            
        start_pos = self.start_connection.get_scene_pos()
        end_pos = self.end_connection.get_scene_pos()
        
        x1, y1 = start_pos.x() / 50, -start_pos.y() / 50
        x2, y2 = end_pos.x() / 50, -end_pos.y() / 50
        
        return f"\\draw ({x1:.2f}, {y1:.2f}) -- ({x2:.2f}, {y2:.2f});"


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
        self.connecting = False
        self.start_connection_point = None
        
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
            # Check if we clicked on a connection point
            item = self.itemAt(event.pos())
            if isinstance(item, ConnectionPoint):
                if not self.connecting:
                    # Start connection
                    self.start_connection_point = item
                    self.connecting = True
                else:
                    # Complete connection
                    if item != self.start_connection_point:
                        # Check if connection is valid (output to input or vice versa)
                        if self.is_valid_connection(self.start_connection_point, item):
                            wire = WireItem(self.start_connection_point, item)
                            self.scene.addItem(wire)
                    
                    self.connecting = False
                    self.start_connection_point = None
            else:
                # Cancel connection if clicking elsewhere
                self.connecting = False
                self.start_connection_point = None
                
        elif self.current_tool in ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"]:
            scene_pos = self.mapToScene(event.pos())
            inputs = 1 if self.current_tool == "NOT" else 2
            gate = GateItem(self.current_tool, scene_pos.x(), scene_pos.y(), inputs)
            self.scene.addItem(gate)
    
    def is_valid_connection(self, point1, point2):
        """Check if connection between two points is valid"""
        # Can't connect point to itself
        if point1 == point2:
            return False
        
        # Can't connect two points of the same type
        if point1.point_type == point2.point_type:
            return False
        
        # Can't connect points from the same gate
        if point1.parent_gate == point2.parent_gate:
            return False
        
        # Input points can only have one connection
        if point1.point_type == 'input' and len(point1.connected_wires) > 0:
            return False
        if point2.point_type == 'input' and len(point2.connected_wires) > 0:
            return False
        
        return True
    
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
    
    def generate_complete_document(self):
        """Generate a complete LaTeX document with the circuit"""
        doc = Document(geometry_options={"margin": "1in"})
        
        # Add required packages
        doc.packages.append(Command('usepackage', 'circuitikz'))
        
        with doc.create(TikZ(options=['circuit logic US'])) as tikz:
            # Add all gates and wires
            for item in self.scene.items():
                if isinstance(item, GateItem):
                    tikz.append(Command('node', 
                        options=[item.get_tikz_code().split('[')[1].split(']')[0]],
                        arguments=[f"({item.pos().x()/50:.2f}, {-item.pos().y()/50:.2f})"],
                        extra_arguments="{}"))
                elif isinstance(item, WireItem):
                    if item.start_connection and item.end_connection:
                        start_pos = item.start_connection.get_scene_pos()
                        end_pos = item.end_connection.get_scene_pos()
                        tikz.append(Command('draw',
                            arguments=[f"({start_pos.x()/50:.2f}, {-start_pos.y()/50:.2f}) -- ({end_pos.x()/50:.2f}, {-end_pos.y()/50:.2f})"]))
        
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
        self.inputs_combo.addItems(["2", "3", "4", "5"])
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
        
        # Auto-update code periodically
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_code)
        self.update_timer.start(1000)  # Update every second
        
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
        QMessageBox.information(self, "Info", "Open functionality not yet implemented")
        
    def save_circuit(self):
        """Save the current circuit"""
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
            # If it's a wire, remove it from connected points
            if isinstance(item, WireItem):
                if item.start_connection:
                    item.start_connection.remove_wire(item)
                if item.end_connection:
                    item.end_connection.remove_wire(item)
            
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
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = LaTeXCircuitDesigner()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
