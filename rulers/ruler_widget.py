"""
Ruler widgets for the circuit canvas
"""

import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics


class BaseRuler(QWidget):
    """Base class for rulers"""
    
    ruler_clicked = pyqtSignal(float)  # Emitted when ruler is clicked to add guide
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(25) if hasattr(self, '_is_horizontal') else self.setFixedWidth(25)
        self.scale = 1.0
        self.offset = 0.0
        self.grid_size = 25
        self.unit = "px"  # Could be extended to support different units
        
        # Appearance
        self.bg_color = QColor(240, 240, 240)
        self.text_color = QColor(60, 60, 60)
        self.major_tick_color = QColor(100, 100, 100)
        self.minor_tick_color = QColor(180, 180, 180)
        
        # Font
        self.font = QFont("Arial", 8)
        self.font_metrics = QFontMetrics(self.font)
        
    def set_scale(self, scale):
        """Set the zoom scale"""
        self.scale = scale
        self.update()
        
    def set_offset(self, offset):
        """Set the view offset"""
        self.offset = offset
        self.update()
        
    def set_grid_size(self, size):
        """Set the grid size for alignment"""
        self.grid_size = size
        self.update()
        
    def world_to_widget(self, world_pos):
        """Convert world coordinate to widget coordinate"""
        return (world_pos + self.offset) * self.scale
        
    def widget_to_world(self, widget_pos):
        """Convert widget coordinate to world coordinate"""
        return widget_pos / self.scale - self.offset


class HorizontalRuler(BaseRuler):
    """Horizontal ruler widget"""
    
    def __init__(self, parent=None):
        self._is_horizontal = True
        super().__init__(parent)
        self.setFixedHeight(25)
        self.setCursor(Qt.CrossCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        # Calculate tick spacing based on scale
        base_spacing = 50  # Base spacing in pixels
        world_spacing = base_spacing / self.scale
        
        # Round to nice numbers
        magnitude = 10 ** math.floor(math.log10(world_spacing))
        normalized = world_spacing / magnitude
        
        if normalized <= 1.0:
            nice_spacing = magnitude
        elif normalized <= 2.0:
            nice_spacing = 2 * magnitude
        elif normalized <= 5.0:
            nice_spacing = 5 * magnitude
        else:
            nice_spacing = 10 * magnitude
            
        pixel_spacing = nice_spacing * self.scale
        
        # Calculate starting position
        start_world = -self.offset
        start_tick = math.floor(start_world / nice_spacing) * nice_spacing
        
        painter.setPen(QPen(self.minor_tick_color, 1))
        painter.setFont(self.font)
        
        # Draw ticks and labels
        world_pos = start_tick
        while True:
            pixel_pos = self.world_to_widget(world_pos)
            if pixel_pos > self.width():
                break
                
            if 0 <= pixel_pos <= self.width():
                # Determine tick height
                is_major = abs(world_pos % (nice_spacing * 5)) < 0.001
                tick_height = 15 if is_major else 8
                
                # Draw tick
                color = self.major_tick_color if is_major else self.minor_tick_color
                painter.setPen(QPen(color, 1))
                painter.drawLine(int(pixel_pos), self.height() - tick_height, 
                               int(pixel_pos), self.height())
                
                # Draw label for major ticks
                if is_major and tick_height == 15:
                    painter.setPen(QPen(self.text_color, 1))
                    label = f"{int(world_pos)}"
                    label_width = self.font_metrics.width(label)
                    painter.drawText(int(pixel_pos - label_width/2), self.height() - 17, label)
                    
            world_pos += nice_spacing
            
        # Draw border
        painter.setPen(QPen(self.major_tick_color, 1))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            world_x = self.widget_to_world(event.x())
            self.ruler_clicked.emit(world_x)


class VerticalRuler(BaseRuler):
    """Vertical ruler widget"""
    
    def __init__(self, parent=None):
        self._is_horizontal = False
        super().__init__(parent)
        self.setFixedWidth(25)
        self.setCursor(Qt.CrossCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        # Calculate tick spacing (same logic as horizontal)
        base_spacing = 50
        world_spacing = base_spacing / self.scale
        
        magnitude = 10 ** math.floor(math.log10(world_spacing))
        normalized = world_spacing / magnitude
        
        if normalized <= 1.0:
            nice_spacing = magnitude
        elif normalized <= 2.0:
            nice_spacing = 2 * magnitude
        elif normalized <= 5.0:
            nice_spacing = 5 * magnitude
        else:
            nice_spacing = 10 * magnitude
            
        pixel_spacing = nice_spacing * self.scale
        
        # Calculate starting position
        start_world = -self.offset
        start_tick = math.floor(start_world / nice_spacing) * nice_spacing
        
        painter.setPen(QPen(self.minor_tick_color, 1))
        painter.setFont(self.font)
        
        # Draw ticks and labels
        world_pos = start_tick
        while True:
            pixel_pos = self.world_to_widget(world_pos)
            if pixel_pos > self.height():
                break
                
            if 0 <= pixel_pos <= self.height():
                # Determine tick height
                is_major = abs(world_pos % (nice_spacing * 5)) < 0.001
                tick_width = 15 if is_major else 8
                
                # Draw tick
                color = self.major_tick_color if is_major else self.minor_tick_color
                painter.setPen(QPen(color, 1))
                painter.drawLine(self.width() - tick_width, int(pixel_pos),
                               self.width(), int(pixel_pos))
                
                # Draw label for major ticks (rotated)
                if is_major and tick_width == 15:
                    painter.setPen(QPen(self.text_color, 1))
                    painter.save()
                    painter.translate(self.width() - 17, int(pixel_pos))
                    painter.rotate(-90)
                    label = f"{int(world_pos)}"
                    label_width = self.font_metrics.width(label)
                    painter.drawText(-label_width//2, 0, label)
                    painter.restore()
                    
            world_pos += nice_spacing
            
        # Draw border
        painter.setPen(QPen(self.major_tick_color, 1))
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height())
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            world_y = self.widget_to_world(event.y())
            self.ruler_clicked.emit(world_y)
