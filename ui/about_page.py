from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class AboutPage(QWidget):
    """关于页面"""

    def __init__(self):
        super().__init__()
        # 获取DPI缩放比例
        self.dpi_scale = self.get_dpi_scale()
        self.init_ui()
        
    def get_dpi_scale(self):
        """获取DPI缩放比例"""
        import platform
        from PyQt5.QtWidgets import QApplication
        
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
        from . import styles
        # 使用动态生成的样式，传入DPI缩放比例
        self.setStyleSheet(styles.get_style(self.dpi_scale))

        # 计算缩放后的间距
        spacing = int(20 * self.dpi_scale)
        margin = int(10 * self.dpi_scale)

        # 主布局 - 水平布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(spacing)
        main_layout.setContentsMargins(margin, margin, margin, margin)

        # 左侧布局 - 项目介绍
        left_layout = QVBoxLayout()
        
        # 项目标题
        title_label = QLabel("漏洞储备检索工具 VRST")
        title_font = QFont()
        # 根据DPI缩放调整字体大小
        title_font.setPointSize(int(16 * self.dpi_scale))
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)

        # 项目信息
        project_browser = QTextBrowser()
        project_browser.setOpenExternalLinks(True)
        
        project_text = """
        <h3>版本: 1.0.1</h3>
        
        <h3>功能简介</h3>
        <p>本工具是一个用于解决红队进行攻防演练时快速检索漏洞储备中涉及靶标的资产，主要功能包括:</p>
        <ul>
            <li>通过FOFA API进行网络资产搜索</li>
            <li>对漏洞储备进行定向检索</li>
            <li>集成Afrog漏洞扫描器</li>
            <li>支持自定义配置和批量操作</li>
            <li>提供友好的图形用户界面</li>
            <li>支持多种操作系统</li>
            <li>开源项目，欢迎社区贡献</li>
            <li>使用Python编写，基于PyQt5框架</li>
            <li>支持多种漏洞指纹库</li>
            <li>提供详细的操作文档和使用指南</li>
            <li>易于扩展和定制</li>
            <li>集成社区支持和反馈渠道</li>
            <li>持续更新和维护</li>
            <li>提供安全的漏洞检索和管理功能</li>
            <li>支持多种数据格式导入和导出</li>
        </ul>
        <h3>项目地址</h3>
        <p><a href="https://github.com/iqingshan/VRST">https://github.com/iqingshan/VRST</a></p>
        <h3>许可证</h3>
        <p>本项目采用MIT许可证，详情请查看项目根目录下的LICENSE文件。</p>
        <h3>联系方式</h3>
        <p>如有任何问题或建议，请通过以下方式联系我们:青山（qingshan@88.com）</p>
        <ul>
        """
        project_browser.setHtml(project_text)
        left_layout.addWidget(project_browser)

        # 右侧布局 - 垂直分为两部分
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # 右侧上层 - 贡献者名单
        contributors_title = QLabel("贡献者名单")
        contributors_title.setFont(title_font)
        contributors_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(contributors_title)
        
        contributors_browser = QTextBrowser()
        contributors_browser.setHtml("""
        <ul>
            <li>青山 - 核心开发者 & 牛马红队</li>
            <li>张三 - UI设计</li>
            <li>李四 - 测试工程师</li>
            <li>王五 - 文档编写</li>
            <li>赵六 - 社区支持</li>
            <li>其他贡献者 - 感谢所有参与和支持本项目的朋友们！</li>
            <li>如果您也想参与贡献，请联系青山！</li>
        </ul>
        """)
        right_layout.addWidget(contributors_browser)

        # 右侧下层 - 更新日志
        changelog_title = QLabel("更新日志")
        changelog_title.setFont(title_font)
        changelog_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(changelog_title)
        
        changelog_browser = QTextBrowser()
        changelog_browser.setHtml("""
        <h4>v1.0.1 (2025-07-12)</h4>
        <ul>
            <li>增加远程更新漏洞储备指纹，团队协作。(@ppp)</li>
            <li>优化查询界面</li>
            <li>优化任务异步操作</li>
            <li>修复部分UI显示问题</li>
            <li>暂停夸克的使用，后续优化</li>
            <li>修复已知bug</li>
        </ul>
        <h4>v1.0.0 (2025-07-10)</h4>
        <ul>
            <li>初始版本发布</li>
            <li>实现基础漏洞检索功能</li>
            <li>集成FOFA API</li>
            <li>添加图形用户界面</li>
        </ul>
        """)
        right_layout.addWidget(changelog_browser)

        # 将左右布局添加到主布局
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=1)

        # 最终布局
        self.setLayout(main_layout)
