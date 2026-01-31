# -*- coding: utf-8 -*-
import sys
import os
import json
import threading
from datetime import datetime
from PIL import Image
import numpy as np

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedLayout, QScrollArea, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QDialog, QSizeGrip, QTextEdit, QSplitter,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QGridLayout,
    QGroupBox, QToolButton, QMenu, QSystemTrayIcon, QStyle
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QThread, QPoint, QSize, QTimer, QMetaObject,
    Q_ARG, Slot, QPropertyAnimation, QEasingCurve, QFile, QTextStream
)
from PySide6.QtGui import (
    QPixmap, QImage, QFont, QColor, QPalette, QIcon, QCursor,
    QFontDatabase, QScreen, QGuiApplication
)

# qdarktheme Import
try:
    import qdarktheme
except ImportError:
    qdarktheme = None

# Project Modules
from game_window import GameWindow
from smart_agent import SmartAgent
from knowledge_manager import KnowledgeBase
from config_manager import ConfigManager
from ai_brain import AIBrain
from logger_setup import logger, write_log
from performance_monitor import performance_monitor
from ui_components import DraggableWindow, LogPanel

# ============================================================================
# Phase 3: Log Signals (Signal-driven Cross-thread Communication)
# ============================================================================

class LogSignals(QObject):
    """Log Signals - For cross-thread logging"""
    log_received = Signal(dict)
    image_received = Signal(np.ndarray)
    status_changed = Signal(str, str)  # message, type

# Global Signal Instance
log_signals = LogSignals()

# ============================================================================
# Settings Dialog
# ============================================================================

class SettingsDialog(QDialog):
    """Settings Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.setWindowTitle("系统配置 (Settings)")
        self.setFixedSize(500, 450)
        # Styles are now handled by global QSS, but specific dialog styles can remain or be moved
        # Keeping minimal inline style for dialog specific layout
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; }
            QLabel { color: #cccccc; font-size: 12px; }
            QLineEdit { background-color: #3d3d3d; color: #cccccc; border: 1px solid #505050; border-radius: 4px; padding: 8px; }
            QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 4px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("AI 模型配置")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ecf0f1;")
        layout.addWidget(title)
        
        # API Key
        layout.addWidget(QLabel("API Key:"))
        self.entry_key = QLineEdit()
        self.entry_key.setPlaceholderText("sk-xxxxxxxx")
        self.entry_key.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.entry_key)
        
        self.show_key = QCheckBox("显示 API Key")
        self.show_key.setStyleSheet("color: #cccccc;")
        self.show_key.stateChanged.connect(self._toggle_key_visibility)
        layout.addWidget(self.show_key)
        
        # Endpoint ID
        layout.addWidget(QLabel("Endpoint ID (火山引擎节点号):"))
        self.entry_endpoint = QLineEdit()
        self.entry_endpoint.setPlaceholderText("ep-2024xxxx-xxxxx")
        layout.addWidget(self.entry_endpoint)
        
        # Model Name
        layout.addWidget(QLabel("Model Name (模型名称):"))
        self.entry_model = QComboBox()
        self.entry_model.addItems(["doubao-pro-4k", "doubao-lite-4k", "gpt-4o", "custom"])
        layout.addWidget(self.entry_model)
        
        layout.addStretch()
        
        # Save Button
        save_btn = QPushButton("💾 保存配置")
        save_btn.clicked.connect(self._save_config)
        layout.addWidget(save_btn)
    
    def _toggle_key_visibility(self, state):
        if state == Qt.Checked:
            self.entry_key.setEchoMode(QLineEdit.Normal)
        else:
            self.entry_key.setEchoMode(QLineEdit.Password)
    
    def _load_config(self):
        self.entry_key.setText(self.config.get("ai.api_key", ""))
        self.entry_endpoint.setText(self.config.get("ai.endpoint_id", ""))
        model = self.config.get("ai.model", "doubao-pro-4k")
        index = self.entry_model.findText(model)
        if index >= 0:
            self.entry_model.setCurrentIndex(index)
    
    def _save_config(self):
        self.config.set("ai.api_key", self.entry_key.text().strip())
        self.config.set("ai.endpoint_id", self.entry_endpoint.text().strip())
        self.config.set("ai.model", self.entry_model.currentText())
        self.accept()


# ============================================================================
# Main Window Class (AICmdCenter)
# ============================================================================

class AICmdCenter(QMainWindow):
    """AI Game Agent - Holographic Console"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Game Agent - 全息投影控制台")
        self.setMinimumSize(1280, 800)
        
        # Core Modules
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.asset_manager = AssetManager()
        
        self.game_window_driver = GameWindow()
        self.agent = SmartAgent(ui_queue=None, game_window=self.game_window_driver)
        
        # Performance Monitor
        performance_monitor.start_monitoring()
        
        # Window Map
        self.window_map = {}
        
        # Projector States
        self.projector_states = {
            "game": False,
            "log": False
        }
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Setup UI
        self._setup_ui()
        
        # Connect Signals
        self._connect_signals()
        
        # Initial Load
        self.refresh_game_list()
        self.refresh_window_list()
    
    def _setup_ui(self):
        """Setup UI Layout"""
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter: Projection Area | Console
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        
        # ========== Top: Projection Area (Curtain) ==========
        self.projection_area = QFrame()
        self.projection_area.setStyleSheet("background-color: #202020;") # Darker background
        projection_layout = QHBoxLayout(self.projection_area)
        projection_layout.setContentsMargins(20, 20, 20, 20)
        projection_layout.setSpacing(20)
        
        # Hint Label
        self.projection_hint = QLabel("点击控制台中的投影仪按钮开启窗口")
        self.projection_hint.setStyleSheet("""
            color: #505050;
            font-size: 16px;
            font-weight: bold;
        """)
        self.projection_hint.setAlignment(Qt.AlignCenter)
        projection_layout.addWidget(self.projection_hint)
        
        splitter.addWidget(self.projection_area)
        
        # ========== Bottom: Console (Desk) ==========
        self.console_area = QFrame()
        self.console_area.setStyleSheet("background-color: #2b2b2b;")
        self.console_area.setMinimumHeight(200)
        self.console_area.setMaximumHeight(250)
        
        self._setup_console()
        
        splitter.addWidget(self.console_area)
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
        
        # Create Floating Windows (Hidden initially)
        self._create_floating_windows()
    
    def _setup_console(self):
        """Setup Console Area"""
        layout = QHBoxLayout(self.console_area)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # ---- Left: Avatar ----
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(200, 180)
        avatar_frame.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(10, 10, 10, 10)
        
        avatar_label = QLabel("看板娘")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("color: #3498db; font-size: 14px;")
        avatar_layout.addWidget(avatar_label)
        
        layout.addWidget(avatar_frame)
        
        # ---- Middle: Game Config & Window Selection ----
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: transparent;")
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        
        # Game Config
        game_label = QLabel("🎮 游戏配置")
        game_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #cccccc;")
        control_layout.addWidget(game_label)
        
        self.game_selector = QComboBox()
        self.game_selector.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #505050;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
        """)
        self.game_selector.currentTextChanged.connect(self._on_game_change)
        control_layout.addWidget(self.game_selector)
        
        # Window Selection
        win_label = QLabel("🖥️ 窗口选择")
        win_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #cccccc;")
        control_layout.addWidget(win_label)
        
        win_select_layout = QHBoxLayout()
        
        self.window_selector = QComboBox()
        self.window_selector.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #505050;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
        """)
        win_select_layout.addWidget(self.window_selector)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_window_list)
        win_select_layout.addWidget(refresh_btn)
        
        control_layout.addLayout(win_select_layout)
        
        # Link Button
        self.link_btn = QPushButton("🔗 锁定选中窗口")
        self.link_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.link_btn.clicked.connect(self._link_selected_window)
        control_layout.addWidget(self.link_btn)
        
        # Link Status
        self.link_status = QLabel("未连接")
        self.link_status.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self.link_status.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.link_status)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
        # ---- Right: Projector & Controls ----
        projector_frame = QFrame()
        projector_frame.setStyleSheet("background-color: transparent;")
        projector_layout = QVBoxLayout(projector_frame)
        projector_layout.setContentsMargins(0, 0, 0, 0)
        projector_layout.setSpacing(10)
        
        # Projector Title
        projector_title = QLabel("📽️ 投影仪")
        projector_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #cccccc;")
        projector_layout.addWidget(projector_title)
        
        # Projector Buttons
        projector_btns = QHBoxLayout()
        
        self.btn_projector_game = QPushButton("🎮 游戏画面")
        self.btn_projector_game.setCheckable(True)
        self.btn_projector_game.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #cccccc;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                background-color: #405060;
            }
        """)
        self.btn_projector_game.clicked.connect(lambda: self._toggle_projector("game"))
        projector_btns.addWidget(self.btn_projector_game)
        
        self.btn_projector_log = QPushButton("🧠 思维流")
        self.btn_projector_log.setCheckable(True)
        self.btn_projector_log.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #cccccc;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #9b59b6;
                color: white;
            }
            QPushButton:hover {
                background-color: #405060;
            }
        """)
        self.btn_projector_log.clicked.connect(lambda: self._toggle_projector("log"))
        projector_btns.addWidget(self.btn_projector_log)
        
        projector_layout.addLayout(projector_btns)
        
        # Control Buttons
        control_btns = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ 启动代理")
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #606060;
            }
        """)
        self.btn_start.clicked.connect(self._start_agent)
        control_btns.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #606060;
            }
        """)
        self.btn_stop.clicked.connect(self._stop_agent)
        control_btns.addWidget(self.btn_stop)
        
        self.btn_config = QPushButton("⚙️ 配置")
        self.btn_config.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.btn_config.clicked.connect(self._show_settings)
        control_btns.addWidget(self.btn_config)
        
        projector_layout.addLayout(control_btns)
        projector_layout.addStretch()
        
        layout.addWidget(projector_frame)
    
    def _create_floating_windows(self):
        """Create Floating Windows with Acrylic Effect"""
        # Game Window
        self.win_game = DraggableWindow("🎮 游戏画面", self, acrylic_color="CC1a1a1a")
        self.win_game.setGeometry(50, 50, 640, 480)
        self.win_game.hide()
        
        self._setup_game_window()
        
        # Log Window
        self.win_log = DraggableWindow("🧠 思维流", self, acrylic_color="CC1a1a1a")
        self.win_log.setGeometry(720, 50, 500, 400)
        self.win_log.hide()
        
        self._setup_log_window()
    
    def _setup_game_window(self):
        content = self.win_game.get_content_widget()
        layout = self.win_game.get_content_layout()
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background-color: rgba(45, 45, 45, 150); border-bottom: 1px solid #404040;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        label = QLabel("👁️ 实时视觉 (Live Vision)")
        label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: bold;")
        toolbar_layout.addWidget(label)
        
        toolbar_layout.addStretch()
        
        self.view_mode = QComboBox()
        self.view_mode.addItems(["原始画面", "SoM网格", "UI匹配"])
        self.view_mode.currentTextChanged.connect(self._change_view_mode)
        toolbar_layout.addWidget(self.view_mode)
        
        layout.addWidget(toolbar)
        
        # Image Container
        self.image_container = QFrame()
        self.image_container.setStyleSheet("background-color: rgba(26, 26, 26, 150);")
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("请在控制台选择窗口并连接...")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #808080; font-size: 14px;")
        image_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.image_container, 1)
    
    def _setup_log_window(self):
        content = self.win_log.get_content_widget()
        layout = self.win_log.get_content_layout()
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
    
    def _connect_signals(self):
        log_signals.log_received.connect(self._on_log_received)
        log_signals.image_received.connect(self._on_image_received)
    
    # ========================================================================
    # Slots
    # ========================================================================
    
    @Slot(dict)
    def _on_log_received(self, log_data: dict):
        self.log_panel.add_log(log_data)
        write_log(log_data)
    
    @Slot(np.ndarray)
    def _on_image_received(self, img_array: np.ndarray):
        self._update_preview(img_array)
    
    def _toggle_projector(self, projector_type: str):
        """Toggle Projector with Animation"""
        self.projector_states[projector_type] = not self.projector_states[projector_type]
        
        target_window = None
        if projector_type == "game":
            target_window = self.win_game
            msg = "游戏投影仪"
        elif projector_type == "log":
            target_window = self.win_log
            msg = "日志投影仪"
            
        if target_window:
            is_open = self.projector_states[projector_type]
            self._animate_window(target_window, show=is_open)
            
            status = "已开启" if is_open else "已关闭"
            self._add_log(f"{msg}{status}", type="SYSTEM")
        
        # Update Hint
        if not any(self.projector_states.values()):
            self.projection_hint.show()
        else:
            self.projection_hint.hide()
            
    def _animate_window(self, window, show=True):
        """Animate Window Opacity"""
        if show:
            window.setWindowOpacity(0)
            window.show()
            anim = QPropertyAnimation(window, b"windowOpacity", self)
            anim.setDuration(300)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            # Keep reference to avoid GC
            window._anim = anim
        else:
            anim = QPropertyAnimation(window, b"windowOpacity", self)
            anim.setDuration(200)
            anim.setStartValue(1)
            anim.setEndValue(0)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.finished.connect(window.hide)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            window._anim = anim

    def _link_selected_window(self):
        selected_name = self.window_selector.currentText()
        if selected_name not in self.window_map:
            self._add_log("无效的窗口选择", type="ERROR")
            return
        
        target_hwnd = self.window_map[selected_name]
        
        if self.game_window_driver.init_hwnd(target_hwnd):
            title = self.game_window_driver.window_title
            self.link_status.setText(f"✅ 已连接: {title[:15]}...")
            self.link_status.setStyleSheet("color: #2ecc71; font-size: 11px;")
            self.btn_start.setEnabled(True)
            self._add_log(f"成功锁定: {title}", type="SYSTEM")
            self.link_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            self._test_snapshot()
        else:
            self.link_status.setText("❌ 连接失败")
            self.link_status.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self._add_log("无法绑定该窗口句柄", type="ERROR")
    
    def _start_agent(self):
        if not self.game_window_driver.hwnd:
            self._add_log("窗口句柄丢失，请重新连接", type="ERROR")
            return
        
        self._add_log("正在启动智能代理...", type="SYSTEM")
        
        success = self.agent.start(window_title=None)
        if success:
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.window_selector.setEnabled(False)
            self.link_btn.setEnabled(False)
        else:
            self.btn_start.setEnabled(True)
    
    def _stop_agent(self):
        self.agent.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.window_selector.setEnabled(True)
        self.link_btn.setEnabled(True)
        self._add_log("代理已停止", type="SYSTEM")
    
    def _change_view_mode(self, value: str):
        self._add_log(f"切换视觉模式: {value}", type="SYSTEM")
    
    def _on_game_change(self, choice: str):
        if choice and choice != "无配置文件":
            self.knowledge_base.load_game(choice)
            self._add_log(f"已加载知识库: {choice}", type="SYSTEM")
    
    def _show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._add_log("系统配置已更新", type="SYSTEM")
    
    def _update_preview(self, img_array: np.ndarray):
        try:
            if len(img_array.shape) == 3:
                height, width, channels = img_array.shape
                bytes_per_line = channels * width
                q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                height, width = img_array.shape
                bytes_per_line = width
                q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            
            pixmap = QPixmap.fromImage(q_image)
            
            container_size = self.image_container.size()
            scaled_pixmap = pixmap.scaled(
                container_size - QSize(20, 20),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            self.preview_label.setText("")
            
        except Exception as e:
            print(f"Preview Error: {e}")
    
    def _test_snapshot(self):
        import time
        start_time = time.time()
        img = self.game_window_driver.snapshot()
        performance_monitor.record_snapshot(time.time() - start_time)
        if img is not None:
            self._update_preview(img)
            self._add_log("视觉信号接入正常", type="VISION")
        else:
            self._add_log("窗口连接成功，但画面黑屏或受保护", type="ERROR")
    
    def _add_log(self, text: str, detail: str = "", type: str = "SYSTEM"):
        log_data = {"title": text, "detail": detail, "type": type, "time": datetime.now().timestamp()}
        log_signals.log_received.emit(log_data)
    
    def refresh_window_list(self):
        windows = self.game_window_driver.get_all_windows()
        self.window_map = {}
        display_list = []
        
        if not windows:
            display_list = ["未发现窗口"]
        else:
            for hwnd, title in windows:
                display_name = f"{title} [{hwnd}]"
                if len(display_name) > 40:
                    display_name = display_name[:37] + "..."
                self.window_map[display_name] = hwnd
                display_list.append(display_name)
        
        self.window_selector.clear()
        self.window_selector.addItems(display_list)
        
        self._add_log(f"已扫描到 {len(windows)} 个窗口", type="SYSTEM")
    
    def refresh_game_list(self):
        games = self.knowledge_base.list_games()
        self.game_selector.clear()
        if games:
            self.game_selector.addItems(games)
        else:
            self.game_selector.addItem("无配置文件")
    
    def closeEvent(self, event):
        self.agent.stop()
        report = performance_monitor.stop_monitoring()
        if report:
            self._add_log("性能监控报告已生成", detail=report[:500], type="SYSTEM")
        logger.close()
        event.accept()


# ============================================================================
# Asset Manager
# ============================================================================

class AssetManager:
    """Asset Manager"""
    
    def __init__(self):
        self.assets_dir = "assets"
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
        
        self.required_assets = {
            "bg_curtain": os.path.join(self.assets_dir, "bg_curtain.png"),
            "bg_console": os.path.join(self.assets_dir, "bg_console.png"),
            "avatar_placeholder": os.path.join(self.assets_dir, "avatar_placeholder.png"),
            "projector_off": os.path.join(self.assets_dir, "projector_off.png"),
            "projector_on": os.path.join(self.assets_dir, "projector_on.png"),
            "btn_start": os.path.join(self.assets_dir, "btn_start.png"),
            "btn_stop": os.path.join(self.assets_dir, "btn_stop.png"),
            "btn_config": os.path.join(self.assets_dir, "btn_config.png"),
        }
        
        self.generate_placeholders()
    
    def generate_placeholders(self):
        for name, path in self.required_assets.items():
            if not os.path.exists(path):
                self._create_placeholder(path, name)
    
    def _create_placeholder(self, path, name):
        color_map = {
            "bg_curtain": (200, 200, 200),
            "bg_console": (240, 240, 240),
            "avatar_placeholder": (180, 210, 240),
            "projector_off": (120, 120, 120),
            "projector_on": (100, 200, 100),
            "btn_start": (50, 200, 50),
            "btn_stop": (200, 50, 50),
            "btn_config": (50, 150, 200),
        }
        
        color = color_map.get(name, (200, 200, 200))
        size_map = {
            "bg_curtain": (1280, 600),
            "bg_console": (1280, 200),
            "avatar_placeholder": (200, 200),
            "projector_off": (80, 80),
            "projector_on": (80, 80),
            "btn_start": (60, 60),
            "btn_stop": (60, 60),
            "btn_config": (60, 60),
        }
        
        size = size_map.get(name, (100, 100))
        img = Image.new("RGB", size, color)
        img.save(path)
    
    def get_asset(self, name):
        return self.required_assets.get(name, None)


# ============================================================================
# Entry Point
# ============================================================================

def load_stylesheet(app):
    """Load Global Stylesheet"""
    style_file = QFile("assets/style.qss")
    if style_file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(style_file)
        app.setStyleSheet(stream.readAll())
        style_file.close()
    else:
        print("Warning: Could not load assets/style.qss")

def main():
    # High-DPI Support
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # Load Theme
    if qdarktheme:
        qdarktheme.setup_theme("dark")
    
    # Load Custom Styles
    load_stylesheet(app)
    
    window = AICmdCenter()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
