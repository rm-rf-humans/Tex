"""
Guide lines for precise alignment
"""

from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QColor, QCursor


class GuideLine(QGraphicsLineItem):
    """A draggable guide line for alignment"""
    
    def __init__(self, orientation, position, scene_rect):
        super().__init__()
        self.orientation = orientation  # 'horizontal' or 'vertical'
        self.scene_rect = scene_rect
        self.snap_threshold = 10  # Pixels for snapping
        
        # Appearance
        self.normal_pen = QPen(QColor(0, 150, 255, 180), 1, Qt.DashLine)
        self.hover_pen = QPen(QColor(0, 150, 255, 255), 2, Qt.DashLine)
        self.setPen(self.normal_pen)
        
        # Make it interactive
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self.setCursor(Qt.SizeVerCursor if orientation == 'horizontal' else Qt.SizeHorCursor)
        
        self.update_line(position)
        
    def update_line(self, position):
        """Update the line geometry"""
        if self.orientation == 'horizontal':
            # Horizontal line spans the width of the scene
            self.setLine(self.scene_rect.left(), position, 
                        self.scene_rect.right(), position)
        else:
            # Vertical line spans the height of the scene
            self.setLine(position, self.scene_rect.top(), 
                        position, self.scene_rect.bottom())
                        
    def get_position(self):
        """Get the current position of the guide"""
        if self.orientation == 'horizontal':
            return self.line().y1()
        else:
            return self.line().x1()
            
    def itemChange(self, change, value):
        """Handle item changes, especially position changes"""
        if change == QGraphicsItem.ItemPositionChange:
            # Constrain movement to the appropriate axis
            if self.orientation == 'horizontal':
                # Only allow vertical movement
                new_pos = QPointF(0, value.y())
                # Update line position
                self.update_line(value.y())
            else:
                # Only allow horizontal movement
                new_pos = QPointF(value.x(), 0)
                # Update line position
                self.update_line(value.x())
            return new_pos
        return super().itemChange(change, value)
        
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        self.setPen(self.hover_pen)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        self.setPen(self.normal_pen)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.RightButton:
            # Right click to delete
            if self.scene():
                self.scene().removeItem(self)
        else:
            super().mousePressEvent(event)


class GuideLineManager:
    """Manages guide lines in the scene"""
    
    def __init__(self, scene):
        self.scene = scene
        self.horizontal_guides = []
        self.vertical_guides = []
        self.snap_enabled = True
        self.snap_threshold = 10  # pixels
        
    def add_horizontal_guide(self, y_position):
        """Add a horizontal guide line"""
        scene_rect = self.scene.sceneRect()
        guide = GuideLine('horizontal', y_position, scene_rect)
        self.scene.addItem(guide)
        self.horizontal_guides.append(guide)
        return guide
        
    def add_vertical_guide(self, x_position):
        """Add a vertical guide line"""
        scene_rect = self.scene.sceneRect()
        guide = GuideLine('vertical', x_position, scene_rect)
        self.scene.addItem(guide)
        self.vertical_guides.append(guide)
        return guide
        
    def remove_guide(self, guide):
        """Remove a guide line"""
        if guide in self.horizontal_guides:
            self.horizontal_guides.remove(guide)
        if guide in self.vertical_guides:
            self.vertical_guides.remove(guide)
        if guide.scene():
            guide.scene().removeItem(guide)
            
    def clear_all_guides(self):
        """Remove all guide lines"""
        for guide in self.horizontal_guides[:]:
            self.remove_guide(guide)
        for guide in self.vertical_guides[:]:
            self.remove_guide(guide)
            
    def get_snap_position(self, position):
        """Get snapped position if close to a guide"""
        if not self.snap_enabled:
            return position
            
        snapped_pos = QPointF(position)
        
        # Check vertical guides for X snapping
        for guide in self.vertical_guides:
            guide_x = guide.get_position()
            if abs(position.x() - guide_x) <= self.snap_threshold:
                snapped_pos.setX(guide_x)
                break
                
        # Check horizontal guides for Y snapping
        for guide in self.horizontal_guides:
            guide_y = guide.get_position()
            if abs(position.y() - guide_y) <= self.snap_threshold:
                snapped_pos.setY(guide_y)
                break
                
        return snapped_pos
        
    def set_snap_enabled(self, enabled):
        """Enable or disable snapping to guides"""
        self.snap_enabled = enabled
        
    def set_snap_threshold(self, threshold):
        """Set the snap threshold in pixels"""
        self.snap_threshold = threshold
        
    def update_scene_rect(self, rect):
        """Update scene rectangle for all guides"""
        for guide in self.horizontal_guides + self.vertical_guides:
            guide.scene_rect = rect
            guide.update_line(guide.get_position())
            
    def get_guide_positions(self):
        """Get all guide positions"""
        return {
            'horizontal': [guide.get_position() for guide in self.horizontal_guides],
            'vertical': [guide.get_position() for guide in self.vertical_guides]
        }
