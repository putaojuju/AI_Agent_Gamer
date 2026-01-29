# -*- coding: utf-8 -*-
import ctypes
from ctypes import c_int, c_void_p, Structure, byref, sizeof, windll
from datetime import datetime
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSizeGrip, QTextEdit, QWidget, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QCursor, QColor

# ============================================================================
# Windows Acrylic Effect Helper
# ============================================================================

class WindowEffect:
    """Windows 10/11 Acrylic Effect Helper"""
    
    class ACCENT_POLICY(Structure):
        _fields_ = [
            ("AccentState", c_int),
            ("AccentFlags", c_int),
            ("GradientColor", c_int),
            ("AnimationId", c_int)
        ]

    class WINDOWCOMPOSITIONATTRIBDATA(Structure):
        _fields_ = [
            ("Attribute", c_int),
            ("Data", c_void_p),
            ("SizeOfData", c_int)
        ]

    def set_acrylic(self, hwnd, gradient_color: str = "99000000", enable: bool = True):
        """
        Set Acrylic effect for a window
        :param hwnd: Window handle (int)
        :param gradient_color: Hex string (AABBGGRR), e.g., "99000000" for semi-transparent black
        :param enable: Enable or disable effect
        """
        try:
            # AccentState: 3 = ACCENT_ENABLE_BLURBEHIND, 4 = ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent_state = 4 if enable else 0
            
            # Convert hex color to int
            # Note: Windows expects AABBGGRR
            color_int = int(gradient_color, 16)
            
            policy = self.ACCENT_POLICY()
            policy.AccentState = accent_state
            policy.AccentFlags = 2  # 2 = Draw left border, 4 = Draw top border, etc.
            policy.GradientColor = color_int
            policy.AnimationId = 0
            
            data = self.WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19  # WCA_ACCENT_POLICY
            data.Data = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
            data.SizeOfData = ctypes.sizeof(policy)
            
            windll.user32.SetWindowCompositionAttribute(int(hwnd), byref(data))
        except Exception as e:
            print(f"Failed to set acrylic effect: {e}")

# Global instance
window_effect = WindowEffect()


# ============================================================================
# Draggable Window Component
# ============================================================================

class DraggableWindow(QFrame):
    """
    Draggable, Resizable Floating Window with Acrylic Effect
    """
    def __init__(self, title="Window", parent=None, acrylic_color="CC1a1a1a"):
        super().__init__(parent)
        self._title = title
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._window_start_pos = QPoint()
        self._acrylic_color = acrylic_color
        
        # Set window flags
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(200, 150)
        
        # Setup UI
        self._setup_ui()
        
    def showEvent(self, event):
        """Enable Acrylic effect when shown"""
        super().showEvent(event)
        # Delay slightly to ensure window handle is ready
        hwnd = self.winId()
        window_effect.set_acrylic(hwnd, gradient_color=self._acrylic_color)
        
    def _setup_ui(self):
        """Setup UI Layout"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setObjectName("TitleBar") # For QSS
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(5)
        
        # Title Label
        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("TitleLabel")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # Close Button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.clicked.connect(self.hide)
        title_layout.addWidget(self.close_btn)
        
        self.main_layout.addWidget(self.title_bar)
        
        # Content Area
        self.content_area = QFrame()
        self.content_area.setObjectName("ContentArea")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.content_area, 1)
        
        # Size Grip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("SizeGrip")
        
        # Grip Container
        grip_container = QFrame()
        grip_layout = QHBoxLayout(grip_container)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.main_layout.addWidget(grip_container)
        
    def get_content_widget(self):
        return self.content_area
    
    def get_content_layout(self):
        return self.content_layout
    
    def set_title(self, title: str):
        self._title = title
        self.title_label.setText(title)
    
    # ========================================================================
    # Drag Logic
    # ========================================================================
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self._dragging = True
                self._drag_start_pos = event.globalPosition().toPoint()
                self._window_start_pos = self.pos()
                event.accept()
    
    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._window_start_pos + delta
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()


# ============================================================================
# Log Components
# ============================================================================

class LogCard(QFrame):
    """Log Card Component"""
    
    COLORS = {
        "THOUGHT": "#9b59b6",  # Purple
        "VISION": "#3498db",   # Blue
        "ACTION": "#2ecc71",   # Green
        "SYSTEM": "#95a5a6",   # Gray
        "ERROR": "#e74c3c",    # Red
        "WARNING": "#f39c12"   # Orange
    }
    
    ICONS = {
        "THOUGHT": "🧠", "VISION": "👁️", "ACTION": "🖱️",
        "SYSTEM": "⚙️", "ERROR": "❌", "WARNING": "⚠️"
    }
    
    def __init__(self, log_data: dict, parent=None):
        super().__init__(parent)
        
        raw_type = log_data.get("type", "SYSTEM")
        self.log_type = raw_type.upper() if raw_type else "SYSTEM"
        self.title_text = log_data.get("title", log_data.get("text", "Info"))
        self.detail = log_data.get("detail", "")
        
        ts = log_data.get("time", datetime.now().timestamp())
        self.timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        
        self.is_expanded = False
        self.accent_color = self.COLORS.get(self.log_type, "#95a5a6")
        self.icon = self.ICONS.get(self.log_type, "📝")
        
        self.setObjectName("LogCard")
        # Dynamic style for border color
        self.setStyleSheet(f"LogCard {{ border-left: 4px solid {self.accent_color}; }}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(4)
        
        # Header
        self.header = QFrame()
        self.header.setCursor(QCursor(Qt.PointingHandCursor))
        self.header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Timestamp
        time_label = QLabel(f"[{self.timestamp}]")
        time_label.setObjectName("LogTime")
        header_layout.addWidget(time_label)
        
        # Title
        title = QLabel(f"{self.icon} {self.title_text}")
        title.setObjectName("LogTitle")
        title.setWordWrap(True)
        header_layout.addWidget(title, 1)
        
        # Arrow
        if self.detail:
            self.arrow = QLabel("▶")
            self.arrow.setObjectName("LogArrow")
            header_layout.addWidget(self.arrow)
        
        self.main_layout.addWidget(self.header)
        
        # Detail
        if self.detail:
            self.detail_widget = QTextEdit()
            self.detail_widget.setPlainText(str(self.detail))
            self.detail_widget.setReadOnly(True)
            self.detail_widget.setObjectName("LogDetail")
            self.detail_widget.setMaximumHeight(200)
            self.detail_widget.hide()
            self.main_layout.addWidget(self.detail_widget)
            
            self.header.mousePressEvent = self._toggle_expand
    
    def _toggle_expand(self, event):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.arrow.setText("▼")
            self.detail_widget.show()
            line_count = len(self.detail.split('\n'))
            height = min(400, max(60, line_count * 18))
            self.detail_widget.setMaximumHeight(height)
        else:
            self.arrow.setText("▶")
            self.detail_widget.hide()


class LogPanel(QFrame):
    """Log Panel Component"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_history = []
        self.current_filter = "ALL"
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setObjectName("LogToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        title = QLabel("🧠 思维流")
        title.setObjectName("LogPanelTitle")
        toolbar_layout.addWidget(title)
        
        toolbar_layout.addStretch()
        
        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "THOUGHT", "VISION", "ACTION", "SYSTEM"])
        self.filter_combo.setCurrentText("ALL")
        self.filter_combo.setFixedWidth(100)
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        toolbar_layout.addWidget(self.filter_combo)
        
        layout.addWidget(toolbar)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("LogScrollArea")
        
        # Log Container
        self.log_container = QWidget()
        self.log_container.setStyleSheet("background-color: transparent;")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_layout.setSpacing(4)
        self.log_layout.addStretch()
        
        scroll.setWidget(self.log_container)
        layout.addWidget(scroll, 1)
        
        self.scroll_area = scroll
    
    def add_log(self, log_data: dict):
        if "time" not in log_data:
            log_data["time"] = datetime.now().timestamp()
        
        self.log_history.append(log_data)
        if len(self.log_history) > 200:
            self.log_history.pop(0)
        
        current_type = log_data.get("type", "SYSTEM").upper()
        if self.current_filter == "ALL" or self.current_filter == current_type:
            self._render_card(log_data)
    
    def _render_card(self, log_data: dict):
        card = LogCard(log_data)
        self.log_layout.insertWidget(self.log_layout.count() - 1, card)
        
        # Auto scroll
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _apply_filter(self, filter_type: str):
        self.current_filter = filter_type
        
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for log in self.log_history:
            log_type = log.get("type", "SYSTEM").upper()
            if filter_type == "ALL" or filter_type == log_type:
                self._render_card(log)
    
    def clear(self):
        self.log_history.clear()
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
