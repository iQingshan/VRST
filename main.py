#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time    : 2025/7/11 17:59
@Author  : 青山<qingshan@88.com>
@FileName: main.py
@Software: PyCharm
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
import os

from config import Config
from ui.main_window import MainWindow
from ui.main_page import MainPage
from ui.config_page import ConfigPage
from ui.tools_intro_page import ToolsIntroPage
from ui.about_page import AboutPage
from ui.vulnerability_fingerprint_page import VulnerabilityFingerprintPage
from ui.vulnerability_page import VulnerabilityPage

def main():

    """应用程序入口点"""
    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 设置应用程序图标 - 优化Windows平台图标显示
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
        app.setWindowIcon(app_icon)
        
        # 特别处理Windows平台
        if sys.platform.startswith('win'):
            # 在Windows 11上，有时需要额外设置任务栏图标ID
            try:
                # 尝试导入Windows特定的模块
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VRST.App.1.0.2")
            except Exception:
                # 如果导入失败或设置失败，忽略错误
                pass
    else:
        print("警告: 未找到有效的应用图标文件")

    # 创建配置实例（配置会在初始化时自动加载）
    config = Config()

    # 创建主窗口
    main_window = MainWindow(config)

    # 创建配置页面
    config_page = ConfigPage(config)
    
    # 创建主页面
    main_page = MainPage(config)
    
    # 创建工具介绍页面
    tools_intro_page = ToolsIntroPage()
    VulnerabilityFingerprint_Page = VulnerabilityFingerprintPage(config)
    # 创建关于页面
    about_page = AboutPage()
    
    # 创建漏洞页面
    vulnerability_page = VulnerabilityPage()

    # 将页面添加到主窗口
    main_window.add_tab(main_page, "检索")
    main_window.add_tab(VulnerabilityFingerprint_Page, "指纹")
    main_window.add_tab(vulnerability_page, "漏洞")
    main_window.add_tab(config_page, "配置")
    main_window.add_tab(tools_intro_page, "工具")
    main_window.add_tab(about_page, "关于")

    # 连接主页面的状态变化信号到主窗口的状态栏
    # 连接漏洞页面的状态变化信号到主窗口的状态栏
    vulnerability_page.status_changed.connect(main_window.set_status)

    main_page.status_changed.connect(main_window.set_status)
    
    # 连接漏洞指纹页面的状态变化信号到主窗口的状态栏
    VulnerabilityFingerprint_Page.status_changed.connect(main_window.set_status)

    # 显示主窗口
    main_window.show()

    # 运行应用程序的事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
