import json
import os
import tempfile
from pathlib import Path

class Config:
    """配置管理类，用于保存和加载用户配置"""

    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.config = {
            'fofa_key': '',
            'fofa_email': '',
            'quake_key': '',
            'afrog_path': '',
            'last_region': '全部',
            'last_query': '',
            'fingerprint_update_url': ''
        }
        # 加载配置文件，如果不存在则创建
        self.load_config()
        # 如果配置文件不存在，则创建并保存默认配置
        if not os.path.exists(self.config_file):
            print(f"配置文件 {self.config_file} 不存在，将创建默认配置文件")
            self.save_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 更新配置，保留默认值
                    for key, value in loaded_config.items():
                        if key in self.config:
                            self.config[key] = value
                print(f"配置文件已从 {self.config_file} 加载")
            except json.JSONDecodeError as e:
                print(f"配置文件格式错误: {e}")
                print("将使用默认配置")
                # 备份损坏的配置文件
                try:
                    import time
                    import shutil
                    backup_file = f"{self.config_file}.bak.{int(time.time())}"
                    shutil.copy2(self.config_file, backup_file)
                    print(f"已将损坏的配置文件备份为: {backup_file}")
                except Exception as backup_error:
                    print(f"备份配置文件失败: {backup_error}")
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                print("将使用默认配置")
        else:
            print(f"配置文件 {self.config_file} 不存在，将使用默认配置")

    def save_config(self):
        """保存配置文件"""
        try:
            # 确保配置文件所在目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 如果配置文件不存在，创建一个新的
            if not os.path.exists(self.config_file):
                print(f"配置文件 {self.config_file} 不存在，将创建新的配置文件")
            
            # 保存配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            print(f"配置文件已保存到: {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            # 如果保存失败，尝试保存到项目根目录（只有当当前路径不是项目根目录时才尝试）
            project_root = os.path.dirname(os.path.abspath(__file__))
            fallback_config_file = os.path.join(project_root, 'config.json')
            
            # 只有当备用路径与原路径不同时才尝试备用路径
            if fallback_config_file != self.config_file:
                try:
                    with open(fallback_config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, ensure_ascii=False, indent=4)
                    print(f"配置文件已保存到备用位置: {fallback_config_file}")
                    # 更新配置文件路径
                    self.config_file = fallback_config_file
                    return True
                except Exception as fallback_error:
                    print(f"保存到备用位置也失败: {fallback_error}")
            else:
                # 如果备用路径与原路径相同，尝试创建临时配置文件
                try:
                    temp_dir = tempfile.gettempdir()
                    temp_config_file = os.path.join(temp_dir, 'vrst_config.json')
                    with open(temp_config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, ensure_ascii=False, indent=4)
                    print(f"配置文件已保存到临时位置: {temp_config_file}")
                    # 更新配置文件路径
                    self.config_file = temp_config_file
                    return True
                except Exception as temp_error:
                    print(f"保存到临时位置也失败: {temp_error}")
            
            return False

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        if key in self.config:
            self.config[key] = value
            return True
        return False

    def is_fofa_configured(self):
        """检查FOFA API是否已配置"""
        return bool(self.config.get('fofa_key')) and bool(self.config.get('fofa_email'))

    def is_afrog_configured(self):
        """检查Afrog是否已配置"""
        return bool(self.config.get('afrog_path')) and os.path.exists(self.config.get('afrog_path', ''))

    def is_quake_configured(self):
        """检查360 Quake API是否已配置"""
        return bool(self.config.get('quake_key'))
