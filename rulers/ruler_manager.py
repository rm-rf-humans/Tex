from PyQt5.QtCore import QObject, pyqtSignal
from .ruler_widget import HorizontalRuler, VerticalRuler
from .guide_lines import GuideLineManager


class RulerManager(QObject):
    """Manages rulers and their interaction with the canvas"""
    
    rulers_toggled = pyqtSignal(bool)  # Emitted when rulers are shown/hidden
    
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.enabled = True
        
        # Create rulers
        self.horizontal_ruler = HorizontalRuler()
        self.vertical_ruler = VerticalRuler()
        
        # Create guide line manager
        self.guide_manager = GuideLineManager(canvas.scene)
        
        # Connect signals
        self.horizontal_ruler.ruler_clicked.connect(self.add_horizontal_guide)
        self.vertical_ruler.ruler_clicked.connect(self.add_vertical_guide)
        
        # Connect to canvas view changes
        self.canvas.horizontalScrollBar().valueChanged.connect(self.update_rulers)
        self.canvas.verticalScrollBar().valueChanged.connect(self.update_rulers)
        
        # Initialize ruler state
        self.update_rulers()
        
    def add_horizontal_guide(self, y_position):
        """Add a horizontal guide line"""
        self.guide_manager.add_horizontal_guide(y_position)
        
    def add_vertical_guide(self, x_position):
        """Add a vertical guide line"""
        self.guide_manager.add_vertical_guide(x_position)
        
    def update_rulers(self):
        """Update ruler display based on canvas state"""
        if not self.enabled:
            return
            
        # Get canvas transform
        transform = self.canvas.transform()
        scale = transform.m11()  # Assuming uniform scaling
        
        # Get visible scene rect
        visible_rect = self.canvas.mapToScene(self.canvas.viewport().rect()).boundingRect()
        
        # Update horizontal ruler
        self.horizontal_ruler.set_scale(scale)
        self.horizontal_ruler.set_offset(visible_rect.left())
        
        # Update vertical ruler  
        self.vertical_ruler.set_scale(scale)
        self.vertical_ruler.set_offset(visible_rect.top())
        
        # Update guide line scene rect
        self.guide_manager.update_scene_rect(self.canvas.scene.sceneRect())
        
    def set_enabled(self, enabled):
        """Enable or disable rulers"""
        self.enabled = enabled
        self.horizontal_ruler.setVisible(enabled)
        self.vertical_ruler.setVisible(enabled)
        self.rulers_toggled.emit(enabled)
        
        if enabled:
            self.update_rulers()
            
    def is_enabled(self):
        """Check if rulers are enabled"""
        return self.enabled
        
    def toggle_rulers(self):
        """Toggle ruler visibility"""
        self.set_enabled(not self.enabled)
        
    def clear_guides(self):
        """Clear all guide lines"""
        self.guide_manager.clear_all_guides()
        
    def set_grid_size(self, size):
        """Update grid size for rulers"""
        self.horizontal_ruler.set_grid_size(size)
        self.vertical_ruler.set_grid_size(size)
        
    def get_snap_position(self, position):
        """Get position snapped to guides"""
        return self.guide_manager.get_snap_position(position)
        
    def set_guide_snap_enabled(self, enabled):
        """Enable/disable snapping to guides"""
        self.guide_manager.set_snap_enabled(enabled)
        
    def set_guide_snap_threshold(self, threshold):
        """Set guide snap threshold"""
        self.guide_manager.set_snap_threshold(threshold)
        
    def get_rulers(self):
        """Get ruler widgets for layout"""
        return self.horizontal_ruler, self.vertical_ruler
        
    def get_guide_positions(self):
        """Get all guide positions"""
        return self.guide_manager.get_guide_positions()
