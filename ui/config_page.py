from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

class ConfigPage(QWidget):
    """配置页面"""

    def __init__(self, config):
        super().__init__()
        # 获取DPI缩放比例
        self.dpi_scale = self.get_dpi_scale()
        
        from . import styles
        # 使用动态生成的样式，传入DPI缩放比例
        self.setStyleSheet(styles.get_style(self.dpi_scale))
        
        self.config = config
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
        # 根据DPI缩放调整间距
        spacing = int(20 * self.dpi_scale)
        margin = int(10 * self.dpi_scale)
        button_width = int(120 * self.dpi_scale)
        
        layout = QVBoxLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(margin, margin, margin, margin)

        # FOFA API配置
        fofa_group = QGroupBox("FOFA API配置")
        fofa_layout = QVBoxLayout()

        # Email输入
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setText(self.config.get('fofa_email', ''))
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        fofa_layout.addLayout(email_layout)

        # Key输入
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        self.key_input = QLineEdit()
        self.key_input.setText(self.config.get('fofa_key', ''))
        self.key_input.setEchoMode(QLineEdit.Password)  # 密码模式显示
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        fofa_layout.addLayout(key_layout)

        fofa_group.setLayout(fofa_layout)
        layout.addWidget(fofa_group)

        # 360 Quake API配置
        quake_group = QGroupBox("360 Quake API配置")
        quake_layout = QVBoxLayout()

        # Key输入
        quake_key_layout = QHBoxLayout()
        quake_key_label = QLabel("API Key:")
        self.quake_key_input = QLineEdit()
        self.quake_key_input.setText(self.config.get('quake_key', ''))
        self.quake_key_input.setEchoMode(QLineEdit.Password)  # 密码模式显示
        quake_key_layout.addWidget(quake_key_label)
        quake_key_layout.addWidget(self.quake_key_input)
        quake_layout.addLayout(quake_key_layout)

        quake_group.setLayout(quake_layout)
        layout.addWidget(quake_group)

        # Afrog配置
        afrog_group = QGroupBox("Afrog配置")
        afrog_layout = QHBoxLayout()
        afrog_label = QLabel("Afrog路径:")
        self.afrog_path_input = QLineEdit()
        self.afrog_path_input.setText(self.config.get('afrog_path', ''))
        afrog_browse_btn = QPushButton("浏览...")
        afrog_browse_btn.clicked.connect(self.browse_afrog_path)
        afrog_layout.addWidget(afrog_label)
        afrog_layout.addWidget(self.afrog_path_input)
        afrog_layout.addWidget(afrog_browse_btn)
        afrog_group.setLayout(afrog_layout)
        layout.addWidget(afrog_group)

        # 漏洞指纹配置
        fingerprint_group = QGroupBox("漏洞指纹配置")
        fingerprint_layout = QVBoxLayout()

        # 远程更新地址
        update_url_layout = QHBoxLayout()
        update_url_label = QLabel("远程更新地址:")
        self.update_url_input = QLineEdit()
        self.update_url_input.setText(self.config.get('fingerprint_update_url', ''))
        update_url_layout.addWidget(update_url_label)
        update_url_layout.addWidget(self.update_url_input)
        fingerprint_layout.addLayout(update_url_layout)

        fingerprint_group.setLayout(fingerprint_layout)
        layout.addWidget(fingerprint_group)

        # 保存按钮
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("保存配置")
        save_btn.setFixedWidth(button_width)  # 使用缩放后的按钮宽度
        save_btn.clicked.connect(self.save_config)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

        # 添加弹性空间
        layout.addStretch()

        self.setLayout(layout)

    def browse_afrog_path(self):
        """浏览选择Afrog路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Afrog可执行文件", "", "可执行文件 (*)"
        )
        if file_path:
            self.afrog_path_input.setText(file_path)

    def save_config(self):
        """保存配置"""
        # 获取输入值
        fofa_email = self.email_input.text().strip()
        fofa_key = self.key_input.text().strip()
        quake_key = self.quake_key_input.text().strip()
        afrog_path = self.afrog_path_input.text().strip()
        fingerprint_update_url = self.update_url_input.text().strip()

        # 更新配置
        self.config.set('fofa_email', fofa_email)
        self.config.set('fofa_key', fofa_key)
        self.config.set('quake_key', quake_key)
        self.config.set('afrog_path', afrog_path)
        self.config.set('fingerprint_update_url', fingerprint_update_url)

        # 保存配置到文件
        if not self.config.save_config():
            QMessageBox.critical(self, "错误", "保存配置失败，请检查文件权限或磁盘空间")
            return

        # 显示成功消息
        QMessageBox.information(self, "成功", "配置已保存")
