import sys
import os
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QToolBar, QAction, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
                             QToolBox, QPushButton, QLabel, QSpinBox, QLineEdit,
                             QTextEdit, QSplitter, QFileDialog, QMessageBox, QGroupBox,
                             QFormLayout, QComboBox, QGraphicsEllipseItem, QGraphicsPolygonItem,
                             QGraphicsPathItem, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPixmap, QPolygonF, QPainterPath, QPainterPathStroker, QTransform
from pylatex import Document, TikZ, Command
from pylatex.tikz import TikZNode, TikZDraw


from rulers import RulerManager
from toolbar.app_toolbar import HorizontalActionsToolbar

class CircuitCanvas(QGraphicsView):
    """Enhanced canvas with better connection handling"""
    
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
        self.preview_wire = None
        
        # Set scene size
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        
        # Enable mouse tracking for preview wire
        self.setMouseTracking(True)

        self.shift_pressed = False
        self.shift_ctrl_pressed = False

        self.grid_size = 25  
        self.snap_to_grid_enabled = True  # Renamed to avoid conflict
        self.show_grid = True
        
        self.ruler_manager = RulerManager(self)
        self.rulers_enabled = True

    def drawBackground(self, painter, rect):
        """Draw grid background"""
        if self.show_grid:
            painter.setPen(QPen(QColor(200, 200, 200), 0.5))
            
            # Draw vertical lines
            left = int(rect.left()) - (int(rect.left()) % self.grid_size)
            top = int(rect.top()) - (int(rect.top()) % self.grid_size)
            
            lines = []
            x = left
            while x < rect.right():
                lines.append(QLineF(x, rect.top(), x, rect.bottom()))
                x += self.grid_size
                
            # Draw horizontal lines
            y = top
            while y < rect.bottom():
                lines.append(QLineF(rect.left(), y, rect.right(), y))
                y += self.grid_size
                
            painter.drawLines(lines)
        
        super().drawBackground(painter, rect)
        
    def snap_position_to_grid(self, pos):
        # First snap to grid if enabled
        if self.snap_to_grid_enabled:
            x = round(pos.x() / self.grid_size) * self.grid_size
            y = round(pos.y() / self.grid_size) * self.grid_size
            pos = QPointF(x, y)
        
        # Then snap to guides if enabled and ruler_manager exists
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            pos = self.ruler_manager.get_snap_position(pos)
        
        return pos

    def set_tool(self, tool):
        """Set the current drawing tool"""
        self.current_tool = tool
        if tool == "select":
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.cancel_connection()
        else:
            self.setDragMode(QGraphicsView.NoDrag)
    
    def cancel_connection(self):
        """Cancel current connection operation"""
        if self.connecting and self.preview_wire:
            self.scene.removeItem(self.preview_wire)
            self.preview_wire = None
        self.connecting = False
        self.start_connection_point = None
    
    def mousePressEvent(self, event):
        if self.current_tool == "select":
            super().mousePressEvent(event)
        elif self.current_tool == "wire":
            if event.button() == Qt.LeftButton:
                # Check if we clicked on a connection point or junction
                item = self.itemAt(event.pos())
                scene_pos = self.mapToScene(event.pos())
                
                if isinstance(item, (ConnectionPoint, JunctionPoint)):
                    if not self.connecting:
                        # Start connection
                        self.start_connection_point = item
                        self.connecting = True
                        # Create preview wire
                        initial_pos = item.get_scene_pos()
                        self.preview_wire = PreviewWire(item, initial_pos)
                        self.scene.addItem(self.preview_wire)
                    else:
                        # Complete connection
                        if item != self.start_connection_point:
                            if self.is_valid_connection(self.start_connection_point, item):
                                wire = WireItem(self.start_connection_point, item)
                                self.scene.addItem(wire)
                        
                        self.cancel_connection()
                elif self.connecting:
                    start_pos = self.start_connection_point.get_scene_pos()
                    # Create junction at mouse position
                    if self.shift_pressed:
                        dx = scene_pos.x() - start_pos.x()
                        dy = scene_pos.y() - start_pos.y()
                        if abs(dx) > abs(dy):
                            #temp_pos_for_x_snap = QPointF(scene_pos.x(), start_pos.y())
                            #snapped_temp_pos = self.snap_position_to_grid(temp_pos_for_x_snap)
                            final_junction_pos = QPointF(scene_pos.x(), start_pos.y())
                            if self.shift_ctrl_pressed:
                                final_junction_pos = self.snap_position_to_grid(final_junction_pos)

                        else:
                            #temp_pos_for_y_snap = QPointF(start_pos.x(), scene_pos.y())
                            #snapped_pos = self.snap_position_to_grid(scene_pos)
                            final_junction_pos = QPointF(start_pos.x(), scene_pos.y())                            
                            if self.shift_ctrl_pressed:
                                final_junction_pos = self.snap_position_to_grid(final_junction_pos)
                
                        junction = JunctionPoint(final_junction_pos.x(), final_junction_pos.y())
                    
                    # elif self.shift_ctrl_pressed:
                    #     # start_pos = self.start_connection_point.scenePos()
                    #     dx = scene_pos.x() - start_pos.x()
                    #     dy = scene_pos.y() - start_pos.y()
                    #     if abs(dx) > abs(dy):
                    #         junction_pos = QPointF(scene_pos.x(), start_pos.y())
                    #     else:
                    #         junction_pos = QPointF(start_pos.x(), scene_pos.y())
                        
                    #     junction_pos = self.snap_position_to_grid(junction_pos)
                    #     junction = JunctionPoint(junction_pos.x(), junction_pos.y())

                    else:
                        snapped_pos = scene_pos
                        junction = JunctionPoint(snapped_pos.x(), snapped_pos.y())
                            
                    self.scene.addItem(junction)
                    
                    # Connect start point to junction
                    wire1 = WireItem(self.start_connection_point, junction)
                    self.scene.addItem(wire1)
                    
                    # Start new connection from junction
                    self.start_connection_point = junction
                    if self.preview_wire:
                        self.scene.removeItem(self.preview_wire)
                    snapped_mouse_pos_for_preview = self.snap_position_to_grid(scene_pos)
                    self.preview_wire = PreviewWire(junction, snapped_mouse_pos_for_preview)
                    self.scene.addItem(self.preview_wire)
                else:
                    # Cancel connection if clicking elsewhere
                    self.cancel_connection()
            elif event.button() == Qt.RightButton:
                # Right click cancels connection
                self.cancel_connection()
        
        # Fixed: Gate placement logic moved out of wire tool block
        elif self.current_tool in ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"]:
            if event.button() == Qt.LeftButton:
                scene_pos = self.mapToScene(event.pos())
                # Snap to grid
                snapped_pos = self.snap_position_to_grid(scene_pos)
                inputs = 1 if self.current_tool == "NOT" else 2
                gate = GateItem(self.current_tool, snapped_pos.x(), snapped_pos.y(), inputs)
                self.scene.addItem(gate)

    def toggle_rulers(self):
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.toggle_rulers()
    
    def clear_guides(self):
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.clear_guides()
        
    def set_guide_snap_enabled(self, enabled):
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.set_guide_snap_enabled(enabled)

    # def toggle_grid_snap(self):
    #     """Toggle grid snapping on/off"""
    #     self.snap_to_grid_enabled = not self.snap_to_grid_enabled

    def toggle_grid_display(self):
        """Toggle grid display on/off"""
        self.show_grid = not self.show_grid
        self.viewport().update()

    def set_grid_size(self, size):
        """Set grid size"""
        self.grid_size = max(5, size)
        self.viewport().update()
    
    def mouseMoveEvent(self, event):
        if self.connecting and self.preview_wire:
            scene_pos = self.mapToScene(event.pos())
            
            # Check if shift is pressed for orthogonal routing
            if self.shift_pressed:
                start_pos = self.start_connection_point.get_scene_pos()
                
                # Calculate orthogonal position
                dx = scene_pos.x() - start_pos.x()
                dy = scene_pos.y() - start_pos.y()
                
                # Choose the dominant direction
                if abs(dx) > abs(dy):
                    # Horizontal first
                    ortho_pos = QPointF(scene_pos.x(), start_pos.y())
                else:
                    # Vertical first  
                    ortho_pos = QPointF(start_pos.x(), scene_pos.y())
                
                self.preview_wire.update_end_pos(ortho_pos)
            else:
                self.preview_wire.update_end_pos(scene_pos)
        
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses"""
        # modifiers = 

        if event.key() == Qt.Key_Escape:
            self.cancel_connection()
        elif event.key() == Qt.Key_Shift:
            self.shift_pressed = True
        # elif (event.modifiers() & Qt.ShiftModifier) and (event.modifiers() & Qt.ControlModifier):
        elif event.key() == Qt.Key_Control:
            self.shift_ctrl_pressed = True
        elif event.key() == Qt.Key_G:
            self.toggle_grid_display()  # G key toggles grid display
        # elif event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
        #     self.toggle_grid_snap()  # Ctrl+S toggles grid snapping
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        modifiers = event.modifiers()

        if event.key() == Qt.Key_Shift:
            self.shift_pressed = False
            # self.shift_ctrl_pressed = False

        elif event.key() == Qt.Key_Control:
            self.shift_ctrl_pressed = False
        super().keyReleaseEvent(event)

    def is_valid_connection(self, point1, point2):
        """Enhanced connection validation"""
        if point1 == point2:
            return False
        
        if isinstance(point1, JunctionPoint) or isinstance(point2, JunctionPoint):
            return True
        
        if hasattr(point1, 'point_type') and hasattr(point2, 'point_type'):
            if point1.point_type == point2.point_type:
                return False
        
        if hasattr(point1, 'parent_gate') and hasattr(point2, 'parent_gate'):
            if point1.parent_gate == point2.parent_gate:
                return False
        
        if hasattr(point1, 'point_type') and point1.point_type == 'input' and len(point1.connected_wires) > 0:
            return False
        if hasattr(point2, 'point_type') and point2.point_type == 'input' and len(point2.connected_wires) > 0:
            return False
        
        return True
    
    def get_all_tikz_code(self):
        """Generate TikZ code for all items in the scene"""
        tikz_code = []
        tikz_code.append("\\documentclass[tikz, border=15pt]{standalone}")
        tikz_code.append("\\usetikzlibrary{positioning, shapes.gates.logic.US, calc}")
        tikz_code.append("\\usepackage{amsmath}")
        tikz_code.append("\\begin{document}")
        tikz_code.append("\\begin{tikzpicture}")
        
        # Get all items
        gates = [item for item in self.scene.items() if isinstance(item, GateItem)]
        junctions = [item for item in self.scene.items() if isinstance(item, JunctionPoint)]
        wires = [item for item in self.scene.items() if isinstance(item, WireItem)]
        
        # Create gate ID mapping
        gate_id_map = {}
        for i, gate in enumerate(gates):
            gate_type_count = len([g for g in gates if g.gate_type == gate.gate_type])
            if gate_type_count > 1:
                gate_id = f"{gate.gate_type.lower()}{i+1}"
            else:
                gate_id = gate.gate_type.lower()
            gate_id_map[gate] = gate_id
        
        # Create junction ID mapping
        junction_id_map = {}
        for i, junction in enumerate(junctions):
            junction_id_map[junction] = f"junction{i+1}"
        
        # Add gates section
        if gates:
            tikz_code.append("    % Gates")
            for gate in gates:
                gate_id = gate_id_map[gate]
                tikz_code.append(gate.get_tikz_code(gate_id))
        
        # Add junctions section
        if junctions:
            tikz_code.append("    ")
            tikz_code.append("    % Junctions")
            for junction in junctions:
                junction_id = junction_id_map[junction]
                tikz_code.append(junction.get_tikz_code(junction_id))
        
        # Add connections section
        if wires:
            tikz_code.append("    ")
            tikz_code.append("    % Connections")
            for wire in wires:
                if wire.start_connection and wire.end_connection:
                    start_ref = self.get_connection_reference(wire.start_connection, gate_id_map, junction_id_map)
                    end_ref = self.get_connection_reference(wire.end_connection, gate_id_map, junction_id_map)
                    if start_ref and end_ref:
                        tikz_code.append(wire.get_tikz_code(start_ref, end_ref))
        
        tikz_code.append("\\end{tikzpicture}")
        tikz_code.append("\\end{document}")
        return "\n".join(tikz_code)
    
    def get_connection_reference(self, connection, gate_id_map, junction_id_map):
        """Get TikZ reference for a connection point"""
        if isinstance(connection, JunctionPoint):
            return junction_id_map.get(connection)
        elif isinstance(connection, ConnectionPoint):
            gate = connection.parent_gate
            if gate in gate_id_map:
                gate_id = gate_id_map[gate]
                if connection.point_type == 'output':
                    return f"{gate_id}.output" # Default output anchor
                else: # input
                    # Default input anchor. TikZ gates handle multiple inputs with 'input 1', 'input 2' etc.
                    if gate_id == "not":
                        return f"{gate_id}.input"                        
                    return f"{gate_id}.input {connection.index + 1}"
        return None
    
    def generate_complete_document(self):
        """Generate a complete LaTeX document with the circuit"""
        doc = Document(documentclass='standalone', 
                      document_options=['tikz', 'border=15pt'])
        
        # Add required packages and libraries
        doc.packages.append(Command('usetikzlibrary', 'positioning, shapes.gates.logic.US, calc'))
        doc.packages.append(Command('usepackage', 'amsmath'))
        
        # Get all items
        gates = [item for item in self.scene.items() if isinstance(item, GateItem)]
        junctions = [item for item in self.scene.items() if isinstance(item, JunctionPoint)]
        wires = [item for item in self.scene.items() if isinstance(item, WireItem)]
        
        # Create ID mappings
        gate_id_map = {}
        for i, gate in enumerate(gates):
            gate_type_count = len([g for g in gates if g.gate_type == gate.gate_type])
            if gate_type_count > 1:
                gate_id = f"{gate.gate_type.lower()}{i+1}"
            else:
                gate_id = gate.gate_type.lower()
            gate_id_map[gate] = gate_id
        
        junction_id_map = {}
        for i, junction in enumerate(junctions):
            junction_id_map[junction] = f"junction{i+1}"
        
        with doc.create(TikZ()) as tikz:
            # Add gates
            for gate in gates:
                gate_id = gate_id_map[gate]
                x, y = gate.pos().x() / 50, -gate.pos().y() / 50 # TikZ uses a different y-axis direction
                
                tikz_gates = {
                    "AND": "and gate US",
                    "OR": "or gate US", 
                    "NOT": "not gate US",
                    "NAND": "nand gate US",
                    "NOR": "nor gate US",
                    "XOR": "xor gate US",
                    "XNOR": "xnor gate US"
                }
                
                gate_name = tikz_gates.get(gate.gate_type, "and gate US")
                inputs_spec = f", inputs={gate.num_inputs}" if gate.num_inputs > 2 else ""
                rotation_spec = f", rotate={gate.angle}" if gate.angle != 0 else "" # Add rotation
                
                tikz.append(Command('node', 
                                  options=[f'{gate_name}, draw{inputs_spec}{rotation_spec}'],
                                  arguments=[f'({gate_id})'],
                                  extra_arguments=f'at ({x:.2f}, {y:.2f}) {{}}'))
            
            # Add junctions
            for junction in junctions:
                junction_id = junction_id_map[junction]
                x, y = junction.pos().x() / 50, -junction.pos().y() / 50
                tikz.append(Command('node', 
                                  options=['circle, fill, inner sep=1pt'],
                                  arguments=[f'({junction_id})'],
                                  extra_arguments=f'at ({x:.2f}, {y:.2f}) {{}}'))
            
            # Add connections
            for wire in wires:
                if wire.start_connection and wire.end_connection:
                    start_ref = self.get_connection_reference(wire.start_connection, gate_id_map, junction_id_map)
                    end_ref = self.get_connection_reference(wire.end_connection, gate_id_map, junction_id_map)
                    if start_ref and end_ref:
                        tikz.append(Command('draw', arguments=[f'({start_ref}) -- ({end_ref})']))
        
        return doc

class JunctionPoint(QGraphicsEllipseItem):
    """Junction point for splitting connections"""
    
    def __init__(self, x, y):
        super().__init__(-4, -4, 8, 8)  # Slightly larger than connection points
        self.setPos(x, y)
        
        # Style - filled black circle
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setBrush(QBrush(QColor(0, 0, 0)))
        
        # Make it movable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Connected wires
        self.connected_wires = []
        
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(100, 100, 100)))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 0, 0)))
        super().hoverLeaveEvent(event)
    
    def get_scene_pos(self):
        """Get the absolute scene position of this junction point"""
        return self.mapToScene(self.boundingRect().center())
    
    def add_wire(self, wire):
        """Add a wire connected to this point"""
        self.connected_wires.append(wire)
    
    def remove_wire(self, wire):
        """Remove a wire from this point"""
        if wire in self.connected_wires:
            self.connected_wires.remove(wire)
    
    def itemChange(self, change, value):
        """Handle item changes (like position changes)"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected wires when junction moves
            self.update_connected_wires()
        return super().itemChange(change, value)
    
    def update_connected_wires(self):
        """Update all wires connected to this junction"""
        for wire in self.connected_wires:
            wire.update_position()
    
    def get_tikz_code(self, junction_id):
        """Generate TikZ code for this junction"""
        x, y = self.pos().x() / 50, -self.pos().y() / 50
        return f"    \\node[circle, fill, inner sep=1pt] ({junction_id}) at ({x:.2f}, {y:.2f}) {{}};"


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
        self.setBrush(QBrush(QColor(100, 255, 100)))
        self.setPen(QPen(QColor(0, 200, 0), 2))
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
        self.angle = 0 # Angle for rotation
        
        # Connection points
        self.input_points = []
        self.output_points = []
        
        self.create_connection_points()
        
    def rotate_gate(self):
        self.angle = (self.angle + 90) % 360
        self.prepareGeometryChange() # Notify that geometry is changing
        
        for point in self.input_points + self.output_points:
            if point.scene():
                point.scene().removeItem(point)
            del point # Ensure cleanup
        self.input_points.clear()
        self.output_points.clear()
        self.create_connection_points()
        self.update_connected_wires() # Wires need to redraw
        self.update() # Request a repaint

    def create_connection_points(self):
        """Create input and output connection points"""
        # Clear existing points
        for point in self.input_points + self.output_points:
            if point.scene():
                point.scene().removeItem(point)
        
        self.input_points = []
        self.output_points = []
        
        input_x_offset = -12 # Was -10
        
        # Create input points (left side)
        if self.num_inputs == 2:
            y_positions_for_two_inputs = [-5.0, 5.0]
            for i in range(self.num_inputs):
                y_pos = y_positions_for_two_inputs[i]
                point = ConnectionPoint(self, 'input', i, input_x_offset, y_pos)
                self.input_points.append(point)
        else:
            input_spacing = self.height / (self.num_inputs + 1)
            for i in range(self.num_inputs):
                y_pos = input_spacing * (i + 1) - self.height/2
             
                point = ConnectionPoint(self, 'input', i, -10, y_pos) 
                self.input_points.append(point)
        
        output_point = ConnectionPoint(self, 'output', 0, self.width + 10, 0)
        self.output_points.append(output_point)

    def boundingRect(self):
        
        core_rect = QRectF(0, -self.height / 2, self.width, self.height)
        
        min_x, max_x = core_rect.left(), core_rect.right()
        min_y, max_y = core_rect.top(), core_rect.bottom()

        # Temporarily create unrotated points to find their extent
        temp_input_x_offset = -12
        temp_output_x_offset = self.width
        
        unrotated_points_coords = []
        if self.num_inputs == 2:
            y_positions_for_two_inputs = [-15.0, 15.0]
            for y_pos in y_positions_for_two_inputs:
                unrotated_points_coords.append(QPointF(temp_input_x_offset, y_pos))
        elif self.num_inputs == 1:
            unrotated_points_coords.append(QPointF(temp_input_x_offset, 0))
        else:
            input_spacing = self.height / (self.num_inputs + 1)
            for i in range(self.num_inputs):
                y_pos = input_spacing * (i + 1) - self.height / 2
                unrotated_points_coords.append(QPointF(temp_input_x_offset, y_pos))
        unrotated_points_coords.append(QPointF(temp_output_x_offset, 0))

        for p in unrotated_points_coords:
            min_x = min(min_x, p.x())
            max_x = max(max_x, p.x())
            min_y = min(min_y, p.y())
            max_y = max(max_y, p.y())
            
        # This is the bounding rect of the gate and its pins before rotation, relative to item's (0,0)
        base_brect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

        # Now, transform this base_brect by the current rotation around (self.width/2, 0)
        transform = QTransform()
        transform.translate(self.width / 2, 0) # To rotation center
        transform.rotate(self.angle)            # Rotate
        transform.translate(-self.width / 2, 0) # Back from rotation center
        
        # Map the four corners of the base_brect and find the new min/max
        p1 = transform.map(base_brect.topLeft())
        p2 = transform.map(base_brect.topRight())
        p3 = transform.map(base_brect.bottomLeft())
        p4 = transform.map(base_brect.bottomRight())

        final_min_x = min(p1.x(), p2.x(), p3.x(), p4.x())
        final_max_x = max(p1.x(), p2.x(), p3.x(), p4.x())
        final_min_y = min(p1.y(), p2.y(), p3.y(), p4.y())
        final_max_y = max(p1.y(), p2.y(), p3.y(), p4.y())
        
        # Add a small padding for selection outlines, etc.
        padding = 5 
        return QRectF(final_min_x - padding, final_min_y - padding, 
                      (final_max_x - final_min_x) + 2 * padding, 
                      (final_max_y - final_min_y) + 2 * padding)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(0, 0, 0), 2)
        if self.isSelected():
            pen.setColor(QColor(255, 0, 0)) # Highlight selected item
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255))) # Gate body color

        painter.save() # Save painter state

        
        painter.translate(self.width / 2, 0) # Move origin to rotation center
        painter.rotate(self.angle)           # Rotate
        painter.translate(-self.width / 2, 0) # Move origin back

        # Draw gate shape based on type
        if self.gate_type == "AND":
            self.draw_and_gate(painter)
        elif self.gate_type == "OR":
            self.draw_or_gate(painter)
        elif self.gate_type == "NOT":
            self.draw_not_gate(painter)
        elif self.gate_type == "NAND":
            self.draw_and_gate(painter)
            self.draw_negation_circle(painter, self.width, 0) # Circle at output
        elif self.gate_type == "NOR":
            self.draw_or_gate(painter)
            self.draw_negation_circle(painter, self.width, 0) # Circle at output
        elif self.gate_type == "XOR":
            self.draw_xor_gate(painter)
        elif self.gate_type == "XNOR":
            self.draw_xor_gate(painter)
            self.draw_negation_circle(painter, self.width, 0) # Circle at output
        
        painter.restore() # Restore painter state (removes rotation for other items)

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
        path.moveTo(0, -self.height/2)
        path.quadTo(self.width/4, -self.height/4, self.width/4, 0) # Inner curve control point 1
        path.quadTo(self.width/4, self.height/4, 0, self.height/2)  # Inner curve control point 2
        
        path.quadTo(self.width * 0.6, self.height/2 * 0.7, self.width, 0) # Top outer curve
        path.quadTo(self.width * 0.6, -self.height/2 * 0.7, 0, -self.height/2) # Bottom outer curve
        painter.drawPath(path)

    def draw_xor_gate(self, painter):
        """Draw XOR gate shape"""
        self.draw_or_gate(painter) # Draw OR shape first
        
        extra_arc_path = QPainterPath()
        
        arc_x_offset = -8
        extra_arc_path.moveTo(arc_x_offset, -self.height/2)
        extra_arc_path.quadTo(arc_x_offset + self.width/8, -self.height/4, arc_x_offset + self.width/8, 0)
        extra_arc_path.quadTo(arc_x_offset + self.width/8, self.height/4, arc_x_offset, self.height/2)
        painter.drawPath(extra_arc_path)
    
    def draw_not_gate(self, painter):
        """Draw NOT gate shape (triangle with circle)"""
        triangle = QPolygonF([
            QPointF(0, -self.height/2 * 0.6), # Make triangle a bit smaller
            QPointF(0, self.height/2 * 0.6),
            QPointF(self.width - 10, 0) # Point of triangle before circle
        ])
        painter.drawPolygon(triangle)
        self.draw_negation_circle(painter, self.width - 10, 0) # Circle at output of triangle
    
    def draw_negation_circle(self, painter, x, y):
        
        circle_radius = 5
        painter.drawEllipse(QPointF(x, y), circle_radius, circle_radius)

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
    
    def get_tikz_code(self, gate_id):
        """Generate TikZ code for this gate"""
        x, y = self.pos().x() / 50, -self.pos().y() / 50 # TikZ y-axis is inverted
        
        tikz_gates = {
            "AND": "and gate US", "OR": "or gate US", "NOT": "not gate US",
            "NAND": "nand gate US", "NOR": "nor gate US", "XOR": "xor gate US",
            "XNOR": "xnor gate US"
        }
        gate_name = tikz_gates.get(self.gate_type, "and gate US")
        inputs_spec = f", inputs={self.num_inputs}" if self.num_inputs > 2 else ""
        # Add rotation to TikZ node if angle is not 0
        rotation_spec = f", rotate={self.angle}" if self.angle != 0 else ""
        
        return f"    \\node[{gate_name}, draw{inputs_spec}{rotation_spec}] ({gate_id}) at ({x:.2f}, {y:.2f}) {{}};"


class WireItem(QGraphicsItem):
    """Enhanced wire item with better connection handling"""
    
    def __init__(self, start_point, end_point):
        super().__init__()
        self.start_connection = start_point 
        self.end_connection = end_point     
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Wire appearance
        self.wire_width = 2
        self.selected_width = 3
        
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
        
        local_start_pos = self.mapFromScene(start_pos)
        local_end_pos = self.mapFromScene(end_pos)

        # Add some padding for selection
        padding = 5
        return QRectF(local_start_pos, local_end_pos).normalized().adjusted(-padding, -padding, padding, padding)

    def paint(self, painter, option, widget):
        if not (self.start_connection and self.end_connection):
            return
            
        # Get scene positions from connection points
        start_pos_scene = self.start_connection.get_scene_pos()
        end_pos_scene = self.end_connection.get_scene_pos()

        # Map to local coordinates for drawing
        start_pos_local = self.mapFromScene(start_pos_scene)
        end_pos_local = self.mapFromScene(end_pos_scene)
        
        # Set pen based on selection state
        width = self.selected_width if self.isSelected() else self.wire_width
        pen = QPen(QColor(255, 0, 0) if self.isSelected() else QColor(0, 0, 0), width)
        painter.setPen(pen)
        
        # Draw the wire with antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawLine(start_pos_local, end_pos_local)

    def shape(self):
        """Define the shape for better mouse interaction"""
        if not (self.start_connection and self.end_connection):
            return QPainterPath()
        
        start_pos_scene = self.start_connection.get_scene_pos()
        end_pos_scene = self.end_connection.get_scene_pos()

        start_pos_local = self.mapFromScene(start_pos_scene)
        end_pos_local = self.mapFromScene(end_pos_scene)
        
        path = QPainterPath()
        
        stroker = QPainterPathStroker()
        stroker.setWidth(max(10, self.wire_width + 5)) # Make selection area a bit wider than the wire
        stroker.setCapStyle(Qt.RoundCap) # Makes ends easier to click

        line_path = QPainterPath()
        line_path.moveTo(start_pos_local)
        line_path.lineTo(end_pos_local)
        
        return stroker.createStroke(line_path)

    def update_position(self):
        """Update wire position when connected gates move"""
        self.prepareGeometryChange() # Important for QGraphicsItem when geometry changes
        if self.scene():
            self.scene().update(self.sceneBoundingRect()) # Update the region of the scene this wire occupies
        self.update() # Request repaint of the item itself
    
    def get_tikz_code(self, start_ref, end_ref):
        """Generate TikZ code for this wire"""
        return f"    \\draw ({start_ref}) -- ({end_ref});"


class PreviewWire(QGraphicsItem):
    """Temporary wire shown while connecting"""
    
    def __init__(self, start_point, mouse_pos):
        super().__init__()
        self.start_point = start_point
        self.end_pos = mouse_pos # This is in scene coordinates
        self.setZValue(-1)  # Draw behind other items
    
    def boundingRect(self):
        if not self.start_point:
            return QRectF()
        
        start_pos_scene = self.start_point.get_scene_pos()
        local_start = self.mapFromScene(start_pos_scene)
        local_end = self.mapFromScene(self.end_pos)

        return QRectF(local_start, local_end).normalized().adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget):
        if not self.start_point:
            return
        
        start_pos_scene = self.start_point.get_scene_pos()
        end_pos_scene = self.end_pos # Already in scene coordinates

        # Map to local for drawing
        start_pos_local = self.mapFromScene(start_pos_scene)
        end_pos_local = self.mapFromScene(end_pos_scene)
        
        # Draw dashed preview line
        pen = QPen(QColor(100, 100, 100), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawLine(start_pos_local, end_pos_local)
    
    def update_end_pos(self, scene_pos): # scene_pos is the new mouse position in scene coords
        """Update the end position of the preview wire"""
        self.prepareGeometryChange()
        self.end_pos = scene_pos # Store new scene coordinate
        self.update()


class CanvasWithRulers(QWidget):
    """Widget that combines canvas with rulers"""
    
    def __init__(self, circuit_canvas):
        super().__init__()
        self.canvas = circuit_canvas
        # Add scene property to satisfy RulerManager requirements
        self.scene = circuit_canvas.scene
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI with rulers and canvas"""
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Get rulers from the canvas's ruler manager
        h_ruler, v_ruler = self.canvas.ruler_manager.get_rulers()
        
        # Create corner widget (top-left corner)
        corner = QFrame()
        corner.setFixedSize(25, 25)
        corner.setStyleSheet("background-color: #f0f0f0; border: 1px solid #999;")
        
        # Add widgets to grid layout
        layout.addWidget(corner, 0, 0)          # Top-left corner
        layout.addWidget(h_ruler, 0, 1)         # Horizontal ruler (top)
        layout.addWidget(v_ruler, 1, 0)         # Vertical ruler (left)
        layout.addWidget(self.canvas, 1, 1)     # Canvas (main area)
        
        # Make sure the canvas takes up remaining space
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(1, 1)
        
        # Connect ruler updates to canvas view changes
        self.canvas.ruler_manager.rulers_toggled.connect(self.on_rulers_toggled)
    
    def on_rulers_toggled(self, visible):
        pass

class ToolPanel(QWidget):
    """Tool panel with gate selection and properties, now using QToolBox."""

    tool_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main layout for the ToolPanel
        main_layout = QVBoxLayout(self)

        # Create the QToolBox
        self.tool_box = QToolBox()
        main_layout.addWidget(self.tool_box)

        gates_page = QWidget()
        gates_layout = QVBoxLayout(gates_page)

        gate_types = ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"]
        for gate in gate_types:
            btn = QPushButton(gate)
            
            btn.clicked.connect(lambda checked, g=gate: self.tool_selected.emit(g))
            gates_layout.addWidget(btn)

        gates_layout.addStretch()
        self.tool_box.addItem(gates_page, "Logic Gates")

        circuits_page = QWidget()
        circuits_layout = QVBoxLayout(circuits_page)

        circuit_components = ["Resistor", "Capacitor", "Inductor", "VoltageSource", "CurrentSource"]
        for component in circuit_components:
            btn = QPushButton(component)

            btn.clicked.connect(lambda checked, c=component: self.tool_selected.emit(c))
            circuits_layout.addWidget(btn)

        circuits_layout.addStretch()
        self.tool_box.addItem(circuits_page, "Circuit Components")

        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()

        self.inputs_combo = QComboBox()
        self.inputs_combo.addItems(["2", "3", "4", "5"])
        props_layout.addRow("Inputs:", self.inputs_combo)

        self.value_edit = QLineEdit()
        props_layout.addRow("Value:", self.value_edit)


        props_group.setLayout(props_layout)
        main_layout.addWidget(props_group)

        main_layout.addStretch()
        # self.setLayout(main_layout)



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
        self.main_toolbar = HorizontalActionsToolbar(self)
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("LaTeX Circuit Designer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.addToolBar(self.main_toolbar)
        
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
        self.canvas_with_rulers = CanvasWithRulers(self.canvas)
        splitter.addWidget(self.canvas_with_rulers)

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
        self.update_timer.start(1000)
        
    def setup_menu(self):
            menubar = self.menuBar()

            file_menu = menubar.addMenu('File')
            file_menu.addAction(self.main_toolbar.new_action)
            file_menu.addAction(self.main_toolbar.open_action)
            file_menu.addAction(self.main_toolbar.save_action)
            file_menu.addSeparator()
            file_menu.addAction(self.main_toolbar.export_tikz_action)
            file_menu.addAction(self.main_toolbar.export_pdf_action)
            file_menu.addAction(self.main_toolbar.export_tex_action)

            edit_menu = menubar.addMenu('Edit')
            edit_menu.addAction(self.main_toolbar.delete_action)
            if hasattr(self.main_toolbar, 'rotate_action'): # Add rotate action to menu
                edit_menu.addAction(self.main_toolbar.rotate_action)


    def setup_connections(self):
        """Setup signal connections"""
        self.tool_panel.tool_selected.connect(self.canvas.set_tool)
        self.code_viewer.export_pdf_requested = self.export_pdf
        # Connect the new rotate action if it exists on the toolbar
        if hasattr(self.main_toolbar, 'rotate_action'):
            self.main_toolbar.rotate_action.triggered.connect(self.rotate_selected_gate)

    def rotate_selected_gate(self):
        selected_items = self.canvas.scene.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Rotate Gate", "No gate selected.")
            return
        
        rotated_any = False
        for item in selected_items:
            if isinstance(item, GateItem):
                item.rotate_gate()
                rotated_any = True
        
        if rotated_any:
            self.update_code() # Update TikZ code if a gate was rotated
            self.canvas.scene.update() # Ensure scene redraws
        else:
            QMessageBox.information(self, "Rotate Gate", "Selected item is not a rotatable gate.")

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
        selected_items = self.canvas.scene.selectedItems()
        for item in selected_items:
            # If item is a GateItem, also remove its connection points
            if isinstance(item, GateItem):
                for cp in item.input_points + item.output_points:
                    # Remove wires connected to this connection point
                    for wire in list(cp.connected_wires): # Iterate over a copy
                        if wire.scene():
                            wire.scene().removeItem(wire)
                        # Clean up references in other connection point/junction
                        if wire.start_connection == cp and wire.end_connection:
                            wire.end_connection.remove_wire(wire)
                        elif wire.end_connection == cp and wire.start_connection:
                            wire.start_connection.remove_wire(wire)
                    if cp.scene():
                        cp.scene().removeItem(cp)
                item.input_points.clear()
                item.output_points.clear()

            elif isinstance(item, WireItem):
                if item.start_connection:
                    item.start_connection.remove_wire(item)
                if item.end_connection:
                    item.end_connection.remove_wire(item)
            
            # For JunctionPoint, remove connected wires
            elif isinstance(item, JunctionPoint):
                for wire in list(item.connected_wires): # Iterate over a copy
                    if wire.scene():
                        wire.scene().removeItem(wire)
                     # Clean up references in other connection point/junction
                    if wire.start_connection == item and wire.end_connection:
                        wire.end_connection.remove_wire(wire)
                    elif wire.end_connection == item and wire.start_connection:
                        wire.start_connection.remove_wire(wire)
            
            if item.scene(): # Ensure item is still in scene before removing
                 self.canvas.scene.removeItem(item)
        self.update_code()
        
    def update_code(self):
        code = self.canvas.get_all_tikz_code()
        self.code_viewer.set_code(code)


def main():
    app = QApplication(sys.argv)
    
    window = LaTeXCircuitDesigner()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()