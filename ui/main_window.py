from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout,
                            QWidget, QStatusBar, QLabel, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QIcon, QFont
import platform
import os
import sys

class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.dpi_scale = self.get_dpi_scale()
        self.init_ui()

    def get_dpi_scale(self):
        """获取DPI缩放比例"""
        if platform.system() == 'Windows':
            try:
                # 获取主屏幕
                screen = QApplication.primaryScreen()
                dpi = screen.logicalDotsPerInch()
                
                # 标准DPI是96
                scale = dpi / 96.0
                
                # 限制缩放范围，避免过大或过小
                scale = max(0.8, min(scale, 2.0))
                
                return scale
            except Exception as e:
                print(f"获取DPI缩放失败: {e}")
                return 1.0
        else:
            # 非Windows系统返回默认值
            return 1.0

    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle("漏洞储备检索工具 VRST V1.0.1")
        
        # 设置应用图标 - 优化Windows平台图标显示
        self.setup_application_icon()
        
        # 安装事件过滤器，处理Windows下双击左上角导致意外退出的问题
        if platform.system() == "Windows":
            self.installEventFilter(self)
        
        # 根据DPI缩放调整窗口大小
        base_width = 1000
        base_height = 700
        scaled_width = int(base_width * self.dpi_scale)
        scaled_height = int(base_height * self.dpi_scale)
        self.resize(scaled_width, scaled_height)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        # 根据DPI缩放调整边距
        margin = int(10 * self.dpi_scale)
        main_layout.setContentsMargins(margin, margin, margin, margin)

        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        # 根据DPI缩放调整字体大小
        font_size = int(10 * self.dpi_scale)
        self.tab_widget.setFont(QFont("PingFang SC", font_size))
        main_layout.addWidget(self.tab_widget)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 添加状态栏标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 在状态栏右侧添加版权信息
        copyright_label = QLabel("© 2025 青山 版权所有")
        self.status_bar.addPermanentWidget(copyright_label)

        # 设置样式
        self.set_style()

    def set_style(self):
        """设置样式"""
        from . import styles
        # 使用动态生成的样式，传入DPI缩放比例
        self.setStyleSheet(styles.get_style(self.dpi_scale))


    def add_tab(self, widget, title):
        """添加选项卡"""
        self.tab_widget.addTab(widget, title)

    def show_message(self, title, message, icon=QMessageBox.Information):
        """显示消息对话框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def set_status(self, message):
        """设置状态栏消息"""
        self.status_label.setText(message)
        
    def switch_to_tab(self, tab_name):
        """切换到指定的标签页"""
        # 标签页名称到索引的映射
        tab_indices = {
            "main": 0,
            "vulnerability_fingerprint": 1,
            "vulnerability": 2,
            "config": 3,
            "tools_intro": 4,
            "about": 5
        }
        
        # 如果标签页名称存在于映射中，切换到对应的标签页
        if tab_name in tab_indices and tab_indices[tab_name] < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(tab_indices[tab_name])
            
    def get_tab(self, tab_name):
        """获取指定标签页的实例"""
        tab_indices = {
            "main": 0,
            "vulnerability_fingerprint": 1,
            "vulnerability": 2,
            "config": 3,
            "tools_intro": 4,
            "about": 5
        }
        
        if tab_name in tab_indices and tab_indices[tab_name] < self.tab_widget.count():
            return self.tab_widget.widget(tab_indices[tab_name])
        return None


    def closeEvent(self, event):
        """关闭窗口事件"""
        # 保存配置
        self.config.save_config()
        event.accept()
        
    def setup_application_icon(self):
        """设置应用图标，特别处理Windows平台的图标显示问题"""
        # 定义可能的图标路径列表，按优先级排序
        icon_paths = [
            "code.ico",           # 项目根目录下的code.png
        ]
        
        # 查找第一个存在的图标文件
        icon_path = None
        for path in icon_paths:
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            app_icon = QIcon(icon_path)
            
            # 设置窗口图标
            self.setWindowIcon(app_icon)
            
            # 特别处理Windows平台
            if platform.system() == "Windows":
                # 设置应用程序级别的图标（影响任务栏和左上角）
                # 获取当前应用程序实例
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(app_icon)
                
                # 在Windows 11上，有时需要额外设置任务栏图标ID
                try:
                    # 尝试导入Windows特定的模块
                    import ctypes
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VRST.App.1.0.1")
                except Exception:
                    # 如果导入失败或设置失败，忽略错误
                    pass
        else:
            print("警告: 未找到有效的应用图标文件")
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理Windows下双击左上角导致意外退出的问题"""
        if platform.system() == "Windows" and obj is self:
            # 处理非客户区域的鼠标双击事件（左上角图标区域）
            if event.type() == QEvent.NonClientAreaMouseButtonDblClick:
                # 阻止默认的双击行为（通常是关闭窗口）
                return True
        # 对于其他事件，使用默认处理
        return super().eventFilter(obj, event)
