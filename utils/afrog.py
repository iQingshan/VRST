import subprocess
import json
import os
from datetime import datetime

class AfrogScanner:
    """Afrog工具调用类"""

    def __init__(self, afrog_path=''):
        self.afrog_path = afrog_path

    def set_path(self, path):
        """设置Afrog工具路径"""
        self.afrog_path = path
        
    def is_available(self):
        """检查Afrog工具是否可用"""
        return bool(self.afrog_path and os.path.exists(self.afrog_path))

    def scan(self, target, output_dir=None):
        """
        使用Afrog扫描目标

        Args:
            target: 扫描目标，可以是URL或IP地址
            output_dir: 输出目录，默认为当前目录下的results/afrog

        Returns:
            dict: 包含扫描结果的字典
        """
        if not self.afrog_path or not os.path.exists(self.afrog_path):
            return {"error": "Afrog路径未配置或不存在"}

        # 如果未指定输出目录，则使用默认目录
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     'results', 'afrog')

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"afrog_scan_{timestamp}.json")
        # print(f"扫描结果将保存到: {output_file}")
        # exit()
        # 构造Afrog命令
        cmd = [
            self.afrog_path,
            '-t', target,
            '-j', output_file,
        ]

        try:
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # 检查命令是否成功执行
            if process.returncode != 0:
                return {"error": f"Afrog执行失败: {stderr}"}

            # 读取扫描结果
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)

                    return {
                        "success": True,
                        "output_file": output_file,
                        "results": results
                    }
                except json.JSONDecodeError:
                    return {"error": "解析结果文件失败"}
            else:
                return {"error": "扫描完成，但未生成结果文件"}
        except Exception as e:
            return {"error": f"执行Afrog时出错: {str(e)}"}