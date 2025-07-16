from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTextBrowser, QScrollArea
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices

class ToolsIntroPage(QWidget):
    """工具介绍页面"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        from . import styles
        self.setStyleSheet(styles.GLOBAL_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 页面标题
        title_label = QLabel("工具介绍")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # FOFA 工具介绍
        fofa_group = self.create_tool_group(
            "FOFA",
            "FOFA (Finger Of First All) 是一款网络空间搜索引擎，类似于Shodan和ZoomEye。",
            [
                "FOFA可以帮助用户迅速进行网络资产匹配、加快后续工作进程。",
                "它通过对互联网进行持续扫描，收集和分析各种网络设备的指纹信息。",
                "用户可以使用FOFA来发现目标组织的资产，如Web服务器、数据库、物联网设备等。",
                "FOFA提供了强大的搜索语法，可以精确定位特定类型的设备或服务。"
            ],
            "https://fofa.info/"
        )
        scroll_layout.addWidget(fofa_group)

        # Quark 工具介绍
        fofa_group = self.create_tool_group(
            "Quark",
            "Quark 是一款网络空间搜索引擎，类似于Shodan和ZoomEye。",
            [
                "Quake 是 360 安全能力中心测绘云团队自主研发设计的全网空间测绘系统，能够对全球全量 IPv4、IPv6 地址进行持续性测绘工作。通过结合人工智能与机器学习的方式，具备全网资产设备精准发现、精准识别能力。",
                "它通过对互联网进行持续扫描，收集和分析各种网络设备的指纹信息。",
                "同时系统利用强大、灵活的底层核心扫描引擎，将丰富的安全漏洞数据库、安全攻防知识库与海量资产识别数据相结合，从而达到对全球网络空间安全风险感知的目的。",
                "Quake网络空间测绘系统致力于将虚拟网络空间与现实物理世界相关联，成为网络空间中的预警雷达 —— “因为看见，所以安全”。"
            ],
            "https://quake.360.net/"
        )
        scroll_layout.addWidget(fofa_group)


        # Afrog 工具介绍
        afrog_group = self.create_tool_group(
            "Afrog",
            "Afrog 是一款性能卓越、快速稳定、PoC 可定制的漏洞扫描工具。",
            [
                "Afrog支持自定义PoC，可以根据需要扩展功能。",
                "它采用高并发设计，扫描速度快，资源占用低。",
                "Afrog内置了丰富的漏洞检测规则，覆盖常见的Web安全漏洞。",
                "它提供了友好的命令行界面，易于使用和集成。",
                "Afrog支持多种输出格式，方便结果分析和报告生成。"
            ],
            "https://github.com/zan8in/afrog"
        )
        scroll_layout.addWidget(afrog_group)

        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def create_tool_group(self, tool_name, description, features, link):
        """创建工具介绍组件"""
        group = QGroupBox(tool_name)
        group_layout = QVBoxLayout()

        # 工具描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        group_layout.addWidget(desc_label)

        # 工具特性
        features_browser = QTextBrowser()
        features_browser.setOpenExternalLinks(True)
        features_text = "<ul>"
        for feature in features:
            features_text += f"<li>{feature}</li>"
        features_text += "</ul>"
        features_browser.setHtml(features_text)
        features_browser.setMaximumHeight(150)
        group_layout.addWidget(features_browser)

        # 官方链接
        link_label = QLabel(f'<a href="{link}">官方网站</a>')
        link_label.setOpenExternalLinks(True)
        group_layout.addWidget(link_label)

        group.setLayout(group_layout)
        return group
