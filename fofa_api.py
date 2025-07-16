import base64
import requests
import json
from pypinyin import pinyin, Style
from urllib.parse import quote

"""
翻译中文城市
"""
def trans(str):
    str = str[:-1]
    trans_list = []
    for pinyin_name in pinyin(str, style=Style.NORMAL):
        for pinyin_name_ in pinyin_name:
            pinyin_name__ = pinyin_name_.capitalize()
            trans_list.append(pinyin_name__)
    return ''.join(trans_list)
class FofaAPI:
    """FOFA API调用类"""

    def __init__(self, email='', key=''):
        self.email = email
        self.key = key
        self.base_url = "https://fofa.info/api/v1/search/all"

    def set_credentials(self, email, key):
        """设置FOFA API凭证"""
        self.email = email
        self.key = key

    def search(self, query, region=None, page=1, size=1000):
        """
        搜索FOFA

        Args:
            query: FOFA查询语句
            region: 省份筛选，None表示全部
            city: 城市筛选，None表示全部
            page: 页码，从1开始
            size: 每页结果数，最大为10000

        Returns:
            dict: 包含查询结果的字典
        """
        if not self.email or not self.key:
            return {"error": "FOFA API凭证未配置"}

        # 处理地区筛选
        if region and region != "全部":
            if ' ' in region:  # 处理"省份 城市"格式
                province, city = region.split(' ', 1)
                city = trans(city)
                # print(city)
                query = f"{query} && region=\"{province}\" && city=\"{city.lower()}\""
            else:  # 单独省份
                query = f"{query} && region=\"{region}\""

        # 对查询语句进行Base64编码
        encoded_query = base64.b64encode(query.encode()).decode()

        # 构造请求参数
        params = {
            "key": self.key,
            "qbase64": encoded_query,
            "page": page,
            "size": size,
            "fields": "host,ip,port,protocol,title,domain,server,city"
        }
        # print(params)
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常

            # 解析响应
            result = response.json()
            # print(result)
            # 检查是否有错误
            if "error" in result and result["error"] is not False:
                return {"error": result.get("errmsg", "未知错误")}

            return result
        except requests.exceptions.RequestException as e:
            return {"error": f"请求错误: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "解析响应失败"}
        except Exception as e:
            return {"error": f"未知错误: {str(e)}"}

    def get_regions(self):
        """
        获取FOFA支持的地区列表

        Returns:
            list: 地区列表
        """
        # 这里返回一个预定义的地区列表，也可以通过API获取
        return [
            "全部", "中国", "美国", "日本", "德国", "韩国", "英国", "法国",
            "俄罗斯", "加拿大", "澳大利亚", "巴西", "印度", "意大利",
            "西班牙", "荷兰", "瑞典", "瑞士", "波兰", "土耳其"
        ]
