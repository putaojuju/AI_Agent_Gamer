# -*- coding: utf-8 -*-
import sys
import os
import json
import threading
from datetime import datetime
from PIL import Image
import numpy as np

# PySide6 导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedLayout, QScrollArea, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QDialog, QSizeGrip, QTextEdit, QSplitter,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QGridLayout,
    QGroupBox, QToolButton, QMenu, QSystemTrayIcon, QStyle
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QThread, QPoint, QSize, QTimer, QMetaObject,
    Q_ARG, Slot
)
from PySide6.QtGui import (
    QPixmap, QImage, QFont, QColor, QPalette, QIcon, QCursor,
    QFontDatabase, QScreen, QGuiApplication
)

# qdarktheme 导入
try:
    import qdarktheme
except ImportError:
    qdarktheme = None

# 引入项目模块
from game_window import GameWindow
from smart_agent import SmartAgent
from knowledge_manager import KnowledgeBase
from config_manager import ConfigManager
from ai_brain import AIBrain
from logger_setup import logger, write_log
from performance_monitor import performance_monitor


# ============================================================================
# Phase 3: 日志信号类 (Signal-driven 跨线程通信)
# ============================================================================

class LogSignals(QObject):
    """日志信号类 - 用于跨线程日志通信"""
    log_received = Signal(dict)
    image_received = Signal(np.ndarray)
    status_changed = Signal(str, str)  # message, type


# 全局信号实例
log_signals = LogSignals()


# ============================================================================
# Phase 2: 可拖拽窗口组件 (DraggableWindow)
# ============================================================================

class DraggableWindow(QFrame):
    """
    可拖拽、可缩放的悬浮窗口组件 (PySide6 版本)
    使用 Qt 原生组件实现，避免手写复杂算法
    """
    def __init__(self, title="Window", parent=None):
        super().__init__(parent)
        self._title = title
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._window_start_pos = QPoint()
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(200, 150)
        
        # 应用 QSS 样式
        self.setStyleSheet("""
            DraggableWindow {
                background-color: rgba(30, 30, 30, 230);
                border: 1px solid #505050;
                border-radius: 8px;
            }
        """)
        
        # 创建布局
        self._setup_ui()
        
    def _setup_ui(self):
        """设置 UI 布局"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        
        # 标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                border-bottom: 1px solid #404040;
            }
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(5)
        
        # 标题标签
        self.title_label = QLabel(self._title)
        self.title_label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: bold;")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #999999;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e81123;
                color: white;
                border-radius: 4px;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        title_layout.addWidget(self.close_btn)
        
        self.main_layout.addWidget(self.title_bar)
        
        # 内容区域
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom-left-radius: 7px;
                border-bottom-right-radius: 7px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.content_area, 1)
        
        # 右下角缩放手柄 (使用 Qt 原生 QSizeGrip)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("""
            QSizeGrip {
                background-color: #3498db;
                width: 16px;
                height: 16px;
                border-bottom-right-radius: 6px;
            }
        """)
        
        # 将 size grip 添加到右下角
        grip_container = QFrame()
        grip_layout = QHBoxLayout(grip_container)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.main_layout.addWidget(grip_container)
        
    def get_content_widget(self):
        """获取内容区域 widget，用于添加自定义内容"""
        return self.content_area
    
    def get_content_layout(self):
        """获取内容区域布局"""
        return self.content_layout
    
    def set_title(self, title: str):
        """设置窗口标题"""
        self._title = title
        self.title_label.setText(title)
    
    # ========================================================================
    # 拖拽逻辑 - 使用 event.globalPosition() 计算全局偏移
    # ========================================================================
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在标题栏上
            if self.title_bar.geometry().contains(event.pos()):
                self._dragging = True
                # 记录鼠标按下的全局位置
                self._drag_start_pos = event.globalPosition().toPoint()
                # 记录窗口当前位置
                self._window_start_pos = self.pos()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 执行拖拽"""
        if self._dragging and event.buttons() == Qt.LeftButton:
            # 计算全局偏移量
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            # 计算新位置
            new_pos = self._window_start_pos + delta
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()


# ============================================================================
# 日志卡片组件
# ============================================================================

class LogCard(QFrame):
    """日志卡片组件 - 显示单条日志"""
    
    COLORS = {
        "THOUGHT": "#9b59b6",  # 紫色
        "VISION": "#3498db",   # 蓝色
        "ACTION": "#2ecc71",   # 绿色
        "SYSTEM": "#95a5a6",   # 灰色
        "ERROR": "#e74c3c",    # 红色
        "WARNING": "#f39c12"   # 橙色
    }
    
    ICONS = {
        "THOUGHT": "🧠", "VISION": "👁️", "ACTION": "🖱️",
        "SYSTEM": "⚙️", "ERROR": "❌", "WARNING": "⚠️"
    }
    
    def __init__(self, log_data: dict, parent=None):
        super().__init__(parent)
        
        # 解析数据
        raw_type = log_data.get("type", "SYSTEM")
        self.log_type = raw_type.upper() if raw_type else "SYSTEM"
        self.title_text = log_data.get("title", log_data.get("text", "Info"))
        self.detail = log_data.get("detail", "")
        
        ts = log_data.get("time", datetime.now().timestamp())
        self.timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        
        self.is_expanded = False
        self.accent_color = self.COLORS.get(self.log_type, "#95a5a6")
        self.icon = self.ICONS.get(self.log_type, "📝")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setStyleSheet(f"""
            LogCard {{
                background-color: #2b2b2b;
                border-radius: 6px;
                border-left: 4px solid {self.accent_color};
            }}
            LogCard:hover {{
                background-color: #353535;
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(4)
        
        # 标题行
        self.header = QFrame()
        self.header.setCursor(QCursor(Qt.PointingHandCursor))
        self.header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # 时间戳
        time_label = QLabel(f"[{self.timestamp}]")
        time_label.setStyleSheet("color: #7f8c8d; font-size: 10px; font-family: Consolas;")
        header_layout.addWidget(time_label)
        
        # 标题
        title = QLabel(f"{self.icon} {self.title_text}")
        title.setStyleSheet("color: #ecf0f1; font-size: 12px; font-weight: bold;")
        title.setWordWrap(True)
        header_layout.addWidget(title, 1)
        
        # 展开箭头
        if self.detail:
            self.arrow = QLabel("▶")
            self.arrow.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            header_layout.addWidget(self.arrow)
        
        self.main_layout.addWidget(self.header)
        
        # 详情区域 (初始隐藏)
        if self.detail:
            self.detail_widget = QTextEdit()
            self.detail_widget.setPlainText(str(self.detail))
            self.detail_widget.setReadOnly(True)
            self.detail_widget.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #bdc3c7;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: Consolas;
                    font-size: 11px;
                }
            """)
            self.detail_widget.setMaximumHeight(200)
            self.detail_widget.hide()
            self.main_layout.addWidget(self.detail_widget)
            
            # 绑定点击事件
            self.header.mousePressEvent = self._toggle_expand
    
    def _toggle_expand(self, event):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.arrow.setText("▼")
            self.detail_widget.show()
            # 调整高度
            line_count = len(self.detail.split('\n'))
            height = min(400, max(60, line_count * 18))
            self.detail_widget.setMaximumHeight(height)
        else:
            self.arrow.setText("▶")
            self.detail_widget.hide()


# ============================================================================
# 日志面板组件
# ============================================================================

class LogPanel(QFrame):
    """日志面板 - 管理日志流显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_history = []
        self.current_filter = "ALL"
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 工具栏
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background-color: #2b2b2b; border-bottom: 1px solid #404040;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        title = QLabel("🧠 思维流")
        title.setStyleSheet("color: #cccccc; font-size: 13px; font-weight: bold;")
        toolbar_layout.addWidget(title)
        
        toolbar_layout.addStretch()
        
        # 过滤器
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "THOUGHT", "VISION", "ACTION", "SYSTEM"])
        self.filter_combo.setCurrentText("ALL")
        self.filter_combo.setFixedWidth(100)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #cccccc;
                selection-background-color: #505050;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        toolbar_layout.addWidget(self.filter_combo)
        
        layout.addWidget(toolbar)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606060;
            }
        """)
        
        # 日志容器
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_layout.setSpacing(4)
        self.log_layout.addStretch()
        
        scroll.setWidget(self.log_container)
        layout.addWidget(scroll, 1)
        
        self.scroll_area = scroll
    
    def add_log(self, log_data: dict):
        """添加日志"""
        if "time" not in log_data:
            log_data["time"] = datetime.now().timestamp()
        
        self.log_history.append(log_data)
        if len(self.log_history) > 200:
            self.log_history.pop(0)
        
        current_type = log_data.get("type", "SYSTEM").upper()
        if self.current_filter == "ALL" or self.current_filter == current_type:
            self._render_card(log_data)
    
    def _render_card(self, log_data: dict):
        """渲染日志卡片"""
        card = LogCard(log_data)
        # 插入到 stretch 之前
        self.log_layout.insertWidget(self.log_layout.count() - 1, card)
        
        # 自动滚动到底部
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _apply_filter(self, filter_type: str):
        """应用过滤器"""
        self.current_filter = filter_type
        
        # 清除现有卡片
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新渲染
        for log in self.log_history:
            log_type = log.get("type", "SYSTEM").upper()
            if filter_type == "ALL" or filter_type == log_type:
                self._render_card(log)
    
    def clear(self):
        """清空日志"""
        self.log_history.clear()
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# 设置对话框
# ============================================================================

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.setWindowTitle("系统配置 (Settings)")
        self.setFixedSize(500, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
            }
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
        """)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        # 标题
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
        
        # 保存按钮
        save_btn = QPushButton("💾 保存配置")
        save_btn.clicked.connect(self._save_config)
        layout.addWidget(save_btn)
    
    def _toggle_key_visibility(self, state):
        """切换 API Key 可见性"""
        if state == Qt.Checked:
            self.entry_key.setEchoMode(QLineEdit.Normal)
        else:
            self.entry_key.setEchoMode(QLineEdit.Password)
    
    def _load_config(self):
        """加载配置"""
        self.entry_key.setText(self.config.get("ai.api_key", ""))
        self.entry_endpoint.setText(self.config.get("ai.endpoint_id", ""))
        model = self.config.get("ai.model", "doubao-pro-4k")
        index = self.entry_model.findText(model)
        if index >= 0:
            self.entry_model.setCurrentIndex(index)
    
    def _save_config(self):
        """保存配置"""
        self.config.set("ai.api_key", self.entry_key.text().strip())
        self.config.set("ai.endpoint_id", self.entry_endpoint.text().strip())
        self.config.set("ai.model", self.entry_model.currentText())
        self.accept()


# ============================================================================
# 主窗口类 (AICmdCenter)
# ============================================================================

class AICmdCenter(QMainWindow):
    """AI 游戏代理控制台 - PySide6 版本"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Game Agent - 全息投影控制台")
        self.setMinimumSize(1280, 800)
        
        # 核心模块初始化
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.asset_manager = AssetManager()
        
        self.game_window_driver = GameWindow()
        self.agent = SmartAgent(ui_queue=None, game_window=self.game_window_driver)
        
        # 启动性能监控
        performance_monitor.start_monitoring()
        
        # 窗口映射
        self.window_map = {}
        
        # 投影仪状态
        self.projector_states = {
            "game": False,
            "log": False
        }
        
        # 设置中心窗口
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 设置全局样式
        self._setup_styles()
        
        # 创建 UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 初始加载
        self.refresh_game_list()
        self.refresh_window_list()
    
    def _setup_styles(self):
        """设置全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
        """)
    
    def _setup_ui(self):
        """设置 UI 布局"""
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 分割器：投影区 | 控制台
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #404040;
            }
        """)
        
        # ========== 上半部分：投影区 (灰色幕布) ==========
        self.projection_area = QFrame()
        self.projection_area.setStyleSheet("background-color: #e0e0e0;")
        projection_layout = QHBoxLayout(self.projection_area)
        projection_layout.setContentsMargins(20, 20, 20, 20)
        projection_layout.setSpacing(20)
        
        # 提示标签
        self.projection_hint = QLabel("点击控制台中的投影仪按钮开启窗口")
        self.projection_hint.setStyleSheet("""
            color: #808080;
            font-size: 16px;
            font-weight: bold;
        """)
        self.projection_hint.setAlignment(Qt.AlignCenter)
        projection_layout.addWidget(self.projection_hint)
        
        splitter.addWidget(self.projection_area)
        
        # ========== 下半部分：控制台 (白色桌面) ==========
        self.console_area = QFrame()
        self.console_area.setStyleSheet("background-color: #f5f5f5;")
        self.console_area.setMinimumHeight(200)
        self.console_area.setMaximumHeight(250)
        
        self._setup_console()
        
        splitter.addWidget(self.console_area)
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
        
        # 创建悬浮窗口 (初始隐藏)
        self._create_floating_windows()
    
    def _setup_console(self):
        """设置控制台区域"""
        layout = QHBoxLayout(self.console_area)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # ---- 左侧：看板娘位置 ----
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(200, 180)
        avatar_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
            }
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(10, 10, 10, 10)
        
        avatar_label = QLabel("看板娘")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("color: #1976d2; font-size: 14px;")
        avatar_layout.addWidget(avatar_label)
        
        layout.addWidget(avatar_frame)
        
        # ---- 中间：游戏配置和窗口选择 ----
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: transparent;")
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        
        # 游戏配置
        game_label = QLabel("🎮 游戏配置")
        game_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
        control_layout.addWidget(game_label)
        
        self.game_selector = QComboBox()
        self.game_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                min-width: 200px;
            }
        """)
        self.game_selector.currentTextChanged.connect(self._on_game_change)
        control_layout.addWidget(self.game_selector)
        
        # 窗口选择
        win_label = QLabel("🖥️ 窗口选择")
        win_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
        control_layout.addWidget(win_label)
        
        win_select_layout = QHBoxLayout()
        
        self.window_selector = QComboBox()
        self.window_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                min-width: 200px;
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
        
        # 连接按钮
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
        
        # 连接状态
        self.link_status = QLabel("未连接")
        self.link_status.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self.link_status.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.link_status)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
        # ---- 右侧：投影仪和控制按钮 ----
        projector_frame = QFrame()
        projector_frame.setStyleSheet("background-color: transparent;")
        projector_layout = QVBoxLayout(projector_frame)
        projector_layout.setContentsMargins(0, 0, 0, 0)
        projector_layout.setSpacing(10)
        
        # 投影仪标题
        projector_title = QLabel("📽️ 投影仪")
        projector_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
        projector_layout.addWidget(projector_title)
        
        # 投影仪按钮
        projector_btns = QHBoxLayout()
        
        self.btn_projector_game = QPushButton("🎮 游戏画面")
        self.btn_projector_game.setCheckable(True)
        self.btn_projector_game.setStyleSheet("""
            QPushButton {
                background-color: #90caf9;
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #42a5f5;
                color: white;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
        """)
        self.btn_projector_game.clicked.connect(lambda: self._toggle_projector("game"))
        projector_btns.addWidget(self.btn_projector_game)
        
        self.btn_projector_log = QPushButton("🧠 思维流")
        self.btn_projector_log.setCheckable(True)
        self.btn_projector_log.setStyleSheet("""
            QPushButton {
                background-color: #90caf9;
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #42a5f5;
                color: white;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
        """)
        self.btn_projector_log.clicked.connect(lambda: self._toggle_projector("log"))
        projector_btns.addWidget(self.btn_projector_log)
        
        projector_layout.addLayout(projector_btns)
        
        # 控制按钮
        control_btns = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ 启动代理")
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.btn_start.clicked.connect(self._start_agent)
        control_btns.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.btn_stop.clicked.connect(self._stop_agent)
        control_btns.addWidget(self.btn_stop)
        
        self.btn_config = QPushButton("⚙️ 配置")
        self.btn_config.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.btn_config.clicked.connect(self._show_settings)
        control_btns.addWidget(self.btn_config)
        
        projector_layout.addLayout(control_btns)
        projector_layout.addStretch()
        
        layout.addWidget(projector_frame)
    
    def _create_floating_windows(self):
        """创建悬浮窗口"""
        # 游戏画面窗口
        self.win_game = DraggableWindow("🎮 游戏画面", self)
        self.win_game.setGeometry(50, 50, 640, 480)
        self.win_game.hide()
        
        # 设置游戏窗口内容
        self._setup_game_window()
        
        # 日志窗口
        self.win_log = DraggableWindow("🧠 思维流", self)
        self.win_log.setGeometry(720, 50, 500, 400)
        self.win_log.hide()
        
        # 设置日志窗口内容
        self._setup_log_window()
    
    def _setup_game_window(self):
        """设置游戏窗口内容"""
        content = self.win_game.get_content_widget()
        layout = self.win_game.get_content_layout()
        
        # 工具栏
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #404040;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        label = QLabel("👁️ 实时视觉 (Live Vision)")
        label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: bold;")
        toolbar_layout.addWidget(label)
        
        toolbar_layout.addStretch()
        
        self.view_mode = QComboBox()
        self.view_mode.addItems(["原始画面", "SoM网格", "UI匹配"])
        self.view_mode.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.view_mode.currentTextChanged.connect(self._change_view_mode)
        toolbar_layout.addWidget(self.view_mode)
        
        layout.addWidget(toolbar)
        
        # 图像显示区域
        self.image_container = QFrame()
        self.image_container.setStyleSheet("background-color: #1a1a1a;")
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("请在控制台选择窗口并连接...")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #808080; font-size: 14px;")
        image_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.image_container, 1)
    
    def _setup_log_window(self):
        """设置日志窗口内容"""
        content = self.win_log.get_content_widget()
        layout = self.win_log.get_content_layout()
        
        # 创建日志面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
    
    def _connect_signals(self):
        """连接信号"""
        # 连接日志信号
        log_signals.log_received.connect(self._on_log_received)
        log_signals.image_received.connect(self._on_image_received)
    
    # ========================================================================
    # 槽函数
    # ========================================================================
    
    @Slot(dict)
    def _on_log_received(self, log_data: dict):
        """接收日志信号"""
        self.log_panel.add_log(log_data)
        # 同时写入日志文件
        write_log(log_data)
    
    @Slot(np.ndarray)
    def _on_image_received(self, img_array: np.ndarray):
        """接收图像信号"""
        self._update_preview(img_array)
    
    def _toggle_projector(self, projector_type: str):
        """切换投影仪状态"""
        self.projector_states[projector_type] = not self.projector_states[projector_type]
        
        if projector_type == "game":
            if self.projector_states[projector_type]:
                self.win_game.show()
                self._add_log("游戏投影仪已开启", type="SYSTEM")
            else:
                self.win_game.hide()
                self._add_log("游戏投影仪已关闭", type="SYSTEM")
        elif projector_type == "log":
            if self.projector_states[projector_type]:
                self.win_log.show()
                self._add_log("日志投影仪已开启", type="SYSTEM")
            else:
                self.win_log.hide()
                self._add_log("日志投影仪已关闭", type="SYSTEM")
        
        # 更新提示标签
        if not any(self.projector_states.values()):
            self.projection_hint.show()
        else:
            self.projection_hint.hide()
    
    def _link_selected_window(self):
        """连接选中的窗口"""
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
            # 测试截图
            self._test_snapshot()
        else:
            self.link_status.setText("❌ 连接失败")
            self.link_status.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self._add_log("无法绑定该窗口句柄", type="ERROR")
    
    def _start_agent(self):
        """启动代理"""
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
        """停止代理"""
        self.agent.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.window_selector.setEnabled(True)
        self.link_btn.setEnabled(True)
        self._add_log("代理已停止", type="SYSTEM")
    
    def _change_view_mode(self, value: str):
        """切换视图模式"""
        self._add_log(f"切换视觉模式: {value}", type="SYSTEM")
    
    def _on_game_change(self, choice: str):
        """游戏变更"""
        if choice and choice != "无配置文件":
            self.knowledge_base.load_game(choice)
            self._add_log(f"已加载知识库: {choice}", type="SYSTEM")
    
    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._add_log("系统配置已更新", type="SYSTEM")
    
    def _update_preview(self, img_array: np.ndarray):
        """更新预览图像"""
        try:
            # 转换 numpy 数组为 QImage
            if len(img_array.shape) == 3:
                height, width, channels = img_array.shape
                bytes_per_line = channels * width
                q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                height, width = img_array.shape
                bytes_per_line = width
                q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            
            pixmap = QPixmap.fromImage(q_image)
            
            # 缩放以适应容器
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
        """测试截图"""
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
        """添加日志"""
        log_data = {"title": text, "detail": detail, "type": type, "time": datetime.now().timestamp()}
        log_signals.log_received.emit(log_data)
    
    # ========================================================================
    # 公共方法
    # ========================================================================
    
    def refresh_window_list(self):
        """刷新窗口列表"""
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
        """刷新游戏列表"""
        games = self.knowledge_base.list_games()
        self.game_selector.clear()
        if games:
            self.game_selector.addItems(games)
        else:
            self.game_selector.addItem("无配置文件")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.agent.stop()
        # 停止性能监控并生成报告
        report = performance_monitor.stop_monitoring()
        if report:
            self._add_log("性能监控报告已生成", detail=report[:500], type="SYSTEM")
        # 关闭日志文件
        logger.close()
        event.accept()


# ============================================================================
# 资源管理器类
# ============================================================================

class AssetManager:
    """资源管理器 - 管理图片资源"""
    
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
        """生成占位图片"""
        for name, path in self.required_assets.items():
            if not os.path.exists(path):
                self._create_placeholder(path, name)
    
    def _create_placeholder(self, path, name):
        """创建单个占位图片"""
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
        """获取资源路径"""
        return self.required_assets.get(name, None)


# ============================================================================
# 程序入口
# ============================================================================

def main():
    # 启用 High-DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # 应用深色主题
    if qdarktheme:
        qdarktheme.setup_theme("dark")
    
    window = AICmdCenter()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
