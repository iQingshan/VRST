"""
优化版极简UI设计 - 提升视觉层次与可用性
支持Windows系统下的DPI自适应
"""

import platform
import sys

def get_dpi_scale():
    """
    获取系统DPI缩放比例
    
    Returns:
        float: DPI缩放比例，默认为1.0
    """
    if platform.system() == 'Windows':
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QCoreApplication
            
            # 如果没有QApplication实例，创建一个临时的
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
                
            # 获取主屏幕
            screen = app.primaryScreen()
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

def get_style(scale_factor=None):
    """
    根据DPI缩放比例生成样式表
    
    Args:
        scale_factor: 手动指定的缩放比例，如果为None则自动检测
    
    Returns:
        str: 生成的样式表字符串
    """
    # 如果没有指定缩放比例，则自动检测
    if scale_factor is None:
        scale_factor = get_dpi_scale()
    
    # 基础字体大小
    base_font_size = int(13 * scale_factor)
    
    # 其他尺寸
    border_radius = int(4 * scale_factor)
    padding_small = int(4 * scale_factor)
    padding_medium = int(8 * scale_factor)
    padding_large = int(12 * scale_factor)
    padding_xlarge = int(16 * scale_factor)
    min_width = int(80 * scale_factor)
    min_height = int(24 * scale_factor)
    scrollbar_width = int(10 * scale_factor)
    scrollbar_min_height = int(30 * scale_factor)
    
    return f"""
/* === 基础设置 === */
QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: {base_font_size}px;
    color: #222222;
    background: #ffffff;
}}

/* === 主窗口 === */
QMainWindow {{
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: {border_radius}px;
}}

/* === 按钮 - 优化视觉反馈 === */
QPushButton {{
    color: #ffffff;
    border: none;
    border-radius: {border_radius}px;
    padding: {padding_medium}px {padding_xlarge}px;
    min-width: {min_width}px;
    background: #4285f4;
    transition: all 0.1s ease;
}}

QPushButton:hover {{
    background: #3367d6;
}}

QPushButton:pressed {{
    background: #2a56c6;
    padding-top: {padding_medium + 1}px;
    padding-bottom: {padding_medium - 1}px;
}}

QPushButton:disabled {{
    background: #f1f1f1;
    color: #aaaaaa;
}}

/* === 输入控件 - 提升可用性 === */
QLineEdit, QTextEdit, QComboBox {{
    border: 1px solid #e0e0e0;
    border-radius: {border_radius}px;
    padding: {padding_medium}px {padding_large}px;
    min-height: {min_height}px;
    background: #ffffff;
}}

QComboBox::drop-down {{
    width: {min_height}px;
    border-left: 1px solid #e0e0e0;
}}

QComboBox QAbstractItemView {{
    border: 1px solid #e0e0e0;
    padding: {padding_small}px;
    selection-background-color: #e8f0fe;
}}

QLineEdit:focus, 
QTextEdit:focus, 
QComboBox:focus {{
    border: 1px solid #4285f4;
    outline: none;
}}

/* === 标签页 - 优化视觉层次 === */
QTabWidget::pane {{
    border: 1px solid #e0e0e0;
    border-top: none;
    border-radius: 0 0 {border_radius}px {border_radius}px;
}}

QTabBar::tab {{
    padding: {padding_medium}px {padding_xlarge}px;
    border: 1px solid #e0e0e0;
    border-bottom: none;
    border-radius: {border_radius}px {border_radius}px 0 0;
    margin-right: {padding_small}px;
    background: #f5f5f5;
}}

QTabBar::tab:selected {{
    background: #ffffff;
    border-bottom: 1px solid #ffffff;
    margin-bottom: -1px;
}}

/* === 表格 - 提升可读性 === */
QTableView {{
    border: 1px solid #e0e0e0;
    gridline-color: #f0f0f0;
    selection-background-color: #e8f0fe;
}}

QHeaderView::section {{
    padding: {padding_medium}px;
    background: #f5f5f5;
    border: none;
}}

/* === 滚动条 - 更精细 === */
QScrollBar:vertical {{
    width: {scrollbar_width}px;
    background: #f5f5f5;
}}

QScrollBar::handle:vertical {{
    background: #cccccc;
    min-height: {scrollbar_min_height}px;
    border-radius: {scrollbar_width // 2}px;
}}

/* === 深色模式 - 优化对比度 === */
[theme="dark"] {{
    color: #e0e0e0;
    background: #333333;
}}

[theme="dark"] QMainWindow {{
    background: #333333;
    border-color: #555555;
}}

[theme="dark"] QPushButton {{
    background: #5c8df5;
}}

[theme="dark"] QLineEdit,
[theme="dark"] QTextEdit,
[theme="dark"] QComboBox,
[theme="dark"] QTableView {{
    background: #444444;
    border-color: #555555;
}}

[theme="dark"] QTabBar::tab {{
    background: #444444;
    border-color: #555555;
}}

[theme="dark"] QTabBar::tab:selected {{
    background: #333333;
}}

[theme="dark"] QHeaderView::section {{
    background: #444444;
}}
"""

# 默认样式，使用自动检测的DPI缩放
GLOBAL_STYLE = get_style()