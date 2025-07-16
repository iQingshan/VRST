import os
import pandas as pd
from datetime import datetime

class ResultExporter:
    """结果导出类"""

    @staticmethod
    def export_to_csv(data, output_dir=None, filename=None):
        """
        将结果导出为CSV文件

        Args:
            data: 要导出的数据，应为列表或DataFrame
            output_dir: 输出目录，默认为当前目录下的results/exports
            filename: 文件名，默认为自动生成

        Returns:
            str: 导出文件的路径，如果失败则返回None
        """
        try:
            # 如果未指定输出目录，则使用默认目录
            if not output_dir:
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         'results', 'exports')

            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 如果未指定文件名，则自动生成
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fofa_results_{timestamp}.csv"

            # 确保文件名以.csv结尾
            if not filename.endswith('.csv'):
                filename += '.csv'

            # 完整的输出文件路径
            output_file = os.path.join(output_dir, filename)

            # 如果数据不是DataFrame，则转换为DataFrame
            if not isinstance(data, pd.DataFrame):
                # 假设data是一个字典列表或二维列表
                df = pd.DataFrame(data)
            else:
                df = data

            # 导出为CSV
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            return output_file
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return None

    @staticmethod
    def export_to_excel(data, output_dir=None, filename=None):
        """
        将结果导出为Excel文件

        Args:
            data: 要导出的数据，应为列表或DataFrame
            output_dir: 输出目录，默认为当前目录下的results/exports
            filename: 文件名，默认为自动生成

        Returns:
            str: 导出文件的路径，如果失败则返回None
        """
        try:
            # 如果未指定输出目录，则使用默认目录
            if not output_dir:
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         'results', 'exports')

            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 如果未指定文件名，则自动生成
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fofa_results_{timestamp}.xlsx"

            # 确保文件名以.xlsx结尾
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'

            # 完整的输出文件路径
            output_file = os.path.join(output_dir, filename)

            # 如果数据不是DataFrame，则转换为DataFrame
            if not isinstance(data, pd.DataFrame):
                # 假设data是一个字典列表或二维列表
                df = pd.DataFrame(data)
            else:
                df = data

            # 导出为Excel
            df.to_excel(output_file, index=False)

            return output_file
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return None

    @staticmethod
    def format_fofa_results(results):
        """
        格式化FOFA查询结果为DataFrame

        Args:
            results: FOFA API返回的结果

        Returns:
            pandas.DataFrame: 格式化后的结果
        """
        try:
            # 检查结果格式
            if not isinstance(results, dict) or "results" not in results:
                return pd.DataFrame()

            # 获取结果和字段
            data = results["results"]
            fields = results.get("fields", ["host", "ip", "port", "protocol", "title", "domain", "server", "city"])

            # 创建DataFrame
            df = pd.DataFrame(data, columns=fields)

            return df
        except Exception as e:
            print(f"格式化FOFA结果失败: {e}")
            return pd.DataFrame()
