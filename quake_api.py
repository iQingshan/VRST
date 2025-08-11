import requests
import base64
import json
import time
import random


class QuakeAPI:
    """360 Quake API客户端"""

    def __init__(self, key=""):
        self.key = key
        self.base_url = "https://quake.360.cn/api/v3"
        self.headers = {
            "Content-Type": "application/json",
            "X-QuakeToken": key
        }

    def search(self, query, region=None, page=1, size=100):
        """
        搜索主机
        :param query: 查询语句
        :param region: 地区
        :param page: 页码
        :param size: 每页数量
        :return: 搜索结果
        """
        # print(region)
        try:
            # 构建查询语句
            if region:
                region_parts = region.strip().split(' ', 1)
                if len(region_parts) == 2:  # 包含省份和城市
                    province, city = region_parts
                    query = f"{query} AND province:\"{province}\" AND city:\"{city}\""
                elif region_parts[0]:  # 只有省份
                    query = f"{query} AND province:\"{region_parts[0]}\""
            # print(query)
            # 构建请求数据
            data = {
                "query": query,
                "start": (page - 1) * size,
                "size": size,
            }
            # print(data)
            # 添加1-2秒随机延迟，避免API请求过于频繁
            delay = random.uniform(1, 2)
            time.sleep(delay)
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/search/quake_service",
                headers=self.headers,
                json=data
            )

            # 检查响应状态
            if response.status_code != 200:
                return {
                    "error": f"API请求失败: {response.status_code} {response.text}",
                    "results": [],
                    "size": 0
                }

            # 解析响应
            result = response.json()

            # 检查是否有错误
            if "code" in result and result["code"] != 0:
                return {
                    "error": f"API返回错误: {result.get('message', '未知错误')}",
                    "results": [],
                    "size": 0
                }

            # 格式化结果，使其与FOFA API结果格式一致
            formatted_results = []
            fields = ["host", "ip", "port", "protocol", "title", "domain", "server", "city"]

            for item in result.get("data", []):
                host = f"{item.get('ip', '')}:{item.get('port', '')}"
                ip = item.get('ip', '')
                port = str(item.get('port', ''))
                protocol = item.get('service', {}).get('name', '')
                title = item.get('title', '')
                domain = item.get('domain', '')
                server = item.get('service', {}).get('http', {}).get('server', '')
                city = f"{item.get('country', '')} {item.get('province', '')} {item.get('city', '')}".strip()

                formatted_results.append([host, ip, port, protocol, title, domain, server, city])

            return {
                "results": formatted_results,
                "fields": fields,
                "size": result.get("meta", {}).get("total", len(formatted_results))
            }

        except Exception as e:
            return {
                "error": f"请求出错: {str(e)}",
                "results": [],
                "size": 0
            }
