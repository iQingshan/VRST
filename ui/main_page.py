from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QComboBox, QLineEdit, QPushButton, QTableWidget,
                            QTableWidgetItem, QHeaderView, QFileDialog,
                            QMessageBox, QMenu, QAction, QProgressBar, QApplication,
                            QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QColor, QCursor

import pandas as pd
import os
import threading
import time
import webbrowser

from fofa_api import FofaAPI
from quake_api import QuakeAPI
from utils.export import ResultExporter
from utils.afrog import AfrogScanner

class FofaSearchThread(QThread):
    """FOFA搜索线程"""
    # 定义信号
    search_finished = pyqtSignal(dict)
    search_error = pyqtSignal(str)

    def __init__(self, fofa_api, query, region=None, page=1, size=100):
        super().__init__()
        self.fofa_api = fofa_api
        self.query = query
        self.region = region
        self.page = page
        self.size = size

    def run(self):
        try:
            # 执行FOFA搜索
            result = self.fofa_api.search(
                query=self.query,
                region=self.region,
                page=self.page,
                size=self.size
            )

            # 检查是否有错误
            if "error" in result and result["error"] is not False:
                self.search_error.emit(str(result["error"]))
                return

            # 发送结果
            self.search_finished.emit(result)
        except Exception as e:
            self.search_error.emit(f"搜索出错: {str(e)}")


class QuakeSearchThread(QThread):
    """Quake搜索线程"""
    # 定义信号
    search_finished = pyqtSignal(dict)
    search_error = pyqtSignal(str)

    def __init__(self, quake_api, query, region=None, page=1, size=100):
        super().__init__()
        self.quake_api = quake_api
        self.query = query
        self.region = region
        self.page = page
        self.size = size

    def run(self):
        try:
            # 构建查询语句
            query = self.query
            if self.region:
                province, city = self.region.split(' ', 1) if ' ' in self.region else (self.region, '')
                query += f' province_cn:"{province}"'
                if city:
                    query += f' city_cn:"{city}"'
            
            # 执行Quake搜索
            result = self.quake_api.search(
                query=query,
                page=self.page,
                size=self.size
            )

            # 检查是否有错误
            if "error" in result and result["error"] is not False:
                self.search_error.emit(str(result["error"]))
                return

            # 发送结果
            self.search_finished.emit(result)
        except Exception as e:
            self.search_error.emit(f"搜索出错: {str(e)}")


class ScanThread(QThread):
    """扫描线程"""
    # 定义信号
    scan_finished = pyqtSignal(dict)
    scan_error = pyqtSignal(str)

    def __init__(self, scanner, target):
        super().__init__()
        self.scanner = scanner
        self.target = target

    def run(self):
        try:
            # 执行扫描
            result = self.scanner.scan(self.target)

            # 检查是否有错误
            if "error" in result:
                self.scan_error.emit(result["error"])
                return

            # 发送结果
            self.scan_finished.emit(result)
        except Exception as e:
            self.scan_error.emit(f"扫描出错: {str(e)}")


class BatchSearchWorker(QObject):
    """批量检索工作线程"""
    # 定义信号
    search_progress = pyqtSignal(int, int, str)  # 当前进度, 总数, 当前指纹名称
    search_finished = pyqtSignal(list)  # 所有结果列表
    search_error = pyqtSignal(str)  # 错误信息
    finished = pyqtSignal()  # 完成信号

    def __init__(self, fofa_api, fingerprints, region=""):
        super().__init__()
        self.fofa_api = fofa_api
        self.fingerprints = fingerprints
        self.region = region
        self.results = []

    def run(self):
        """执行批量检索"""
        try:
            total = len(self.fingerprints)
            for i, fingerprint in enumerate(self.fingerprints):
                # 更新进度
                self.search_progress.emit(i + 1, total, fingerprint.get('name', '未命名'))
                
                # 执行FOFA搜索
                query = fingerprint.get('url', '')
                if not query:
                    continue
                    
                result = self.fofa_api.search(
                    query=query,
                    region=self.region,
                    page=1,
                    size=10000
                )
                
                # 检查是否有错误
                if "error" in result and result["error"] is not False:
                    self.search_error.emit(str(result["error"]))
                    return
                
                # 添加指纹信息到结果中
                result['fingerprint'] = {
                    'name': fingerprint.get('name', '未命名'),
                    'version': fingerprint.get('version', ''),
                    'description': fingerprint.get('description', '')
                }
                
                # 添加到结果列表
                self.results.append(result)
            
            # 发送结果
            self.search_finished.emit(self.results)
        except Exception as e:
            self.search_error.emit(f"批量检索出错: {str(e)}")
        finally:
            self.finished.emit()


class MainPage(QWidget):
    """主页面类"""

    # 定义信号
    status_changed = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 获取DPI缩放比例
        self.dpi_scale = self.get_dpi_scale()

        # 创建FOFA API实例
        self.fofa_api = FofaAPI(
            email=self.config.get('fofa_email', ''),
            key=self.config.get('fofa_key', '')
        )

        # 创建360 Quake API实例
        self.quake_api = QuakeAPI(
            key=self.config.get('quake_key', '')
        )

        # 当前搜索模式 (0: FOFA, 1: Quake)
        self.current_mode = 0

        # 创建Afrog扫描器实例
        self.afrog_scanner = AfrogScanner(
            afrog_path=self.config.get('afrog_path', '')
        )

        # 初始化变量
        self.search_results = None
        self.current_page = 1
        self.page_size = 100

        # 初始化UI
        self.init_ui()
        
    def get_dpi_scale(self):
        """获取DPI缩放比例"""
        import platform
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

        # 计算缩放后的尺寸
        margin = int(15 * self.dpi_scale)
        spacing = int(15 * self.dpi_scale)
        small_spacing = int(10 * self.dpi_scale)
        button_min_width = int(80 * self.dpi_scale)
        mode_button_min_width = int(120 * self.dpi_scale)
        
        # 计算缩放后的字体大小
        font_size_normal = int(10 * self.dpi_scale)
        font_size_small = int(9 * self.dpi_scale)

        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)

        # 创建搜索区域
        search_layout = QHBoxLayout()
        search_layout.setSpacing(small_spacing)
        search_layout.setContentsMargins(0, 0, 0, small_spacing)

        # 查询语句输入
        query_label = QLabel("检索语句:")
        query_label.setFont(QFont("PingFang SC", font_size_normal))
        search_layout.addWidget(query_label)

        self.query_input = QLineEdit()
        self.query_input.setFont(QFont("PingFang SC", font_size_normal))
        self.query_input.setPlaceholderText("输入查询语句，例如: domain=\"example.com\"")
        search_layout.addWidget(self.query_input)

        # 搜索按钮
        self.search_button = QPushButton("查询")
        self.search_button.setFont(QFont("PingFang SC", font_size_normal))
        self.search_button.setMinimumWidth(button_min_width)
        search_layout.addWidget(self.search_button)

        # 添加模式切换按钮
        self.mode_button = QPushButton("切换模式(FOFA)")
        self.mode_button.setFont(QFont("PingFang SC", font_size_normal))
        self.mode_button.setMinimumWidth(mode_button_min_width)
        self.mode_button.clicked.connect(self.toggle_search_mode)
        search_layout.addWidget(self.mode_button)

        main_layout.addLayout(search_layout)

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 创建结果表格
        self.result_table = QTableWidget()
        self.result_table.setFont(QFont("PingFang SC", font_size_small))
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置为不可编辑
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)  # 设置为选择整行
        self.result_table.setContextMenuPolicy(Qt.CustomContextMenu)  # 设置为自定义右键菜单
        
        # 设置表格列数和表头
        self.result_table.setColumnCount(9)
        self.result_table.setHorizontalHeaderLabels(["主机", "IP", "端口", "协议", "标题", "域名", "服务器", "城市", "系统名称"])
        
        # 调整列宽（根据DPI缩放）
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setColumnWidth(0, int(150 * self.dpi_scale))  # 主机
        self.result_table.setColumnWidth(1, int(120 * self.dpi_scale))  # IP
        self.result_table.setColumnWidth(2, int(60 * self.dpi_scale))   # 端口
        self.result_table.setColumnWidth(3, int(80 * self.dpi_scale))   # 协议
        self.result_table.setColumnWidth(4, int(200 * self.dpi_scale))  # 标题
        self.result_table.setColumnWidth(5, int(150 * self.dpi_scale))  # 域名
        self.result_table.setColumnWidth(6, int(150 * self.dpi_scale))  # 服务器
        self.result_table.setColumnWidth(7, int(100 * self.dpi_scale))  # 城市
        self.result_table.setColumnWidth(8, int(150 * self.dpi_scale))  # 系统名称
        
        main_layout.addWidget(self.result_table)

        # 创建底部按钮区域
        button_layout = QHBoxLayout()

        # 导出按钮
        self.export_button = QPushButton("导出结果")
        self.export_button.setFont(QFont("PingFang SC", font_size_normal))
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        # 检索漏洞指纹按钮
        self.fingerprint_button = QPushButton("检索漏洞指纹")
        self.fingerprint_button.setFont(QFont("PingFang SC", font_size_normal))
        self.fingerprint_button.clicked.connect(self.show_fingerprint_tab)
        button_layout.addWidget(self.fingerprint_button)

        # 添加分页控件
        self.prev_page_button = QPushButton("上一页")
        self.prev_page_button.setFont(QFont("PingFang SC", font_size_normal))
        self.prev_page_button.setEnabled(False)
        button_layout.addWidget(self.prev_page_button)

        self.page_label = QLabel("第1页")
        self.page_label.setFont(QFont("PingFang SC", font_size_normal))
        self.page_label.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(self.page_label)

        self.next_page_button = QPushButton("下一页")
        self.next_page_button.setFont(QFont("PingFang SC", font_size_normal))
        self.next_page_button.setEnabled(False)
        button_layout.addWidget(self.next_page_button)

        main_layout.addLayout(button_layout)

        # 连接信号和槽
        self.connect_signals()

        # 加载地区列表
        self.load_regions()

        # 加载上次的查询
        self.load_last_query()

    def connect_signals(self):
        """连接信号和槽"""
        # 搜索按钮点击事件
        self.search_button.clicked.connect(self.search)

        # 导出按钮点击事件
        self.export_button.clicked.connect(self.export_results)

        # 表格右键菜单事件
        self.result_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 表格双击事件
        self.result_table.doubleClicked.connect(self.on_table_double_click)

        # 分页按钮点击事件
        self.prev_page_button.clicked.connect(self.prev_page)
        self.next_page_button.clicked.connect(self.next_page)

    def on_table_double_click(self, index):
        """处理表格双击事件"""
        row = index.row()
        url = None
        
        # 获取主机、端口和协议信息
        host_item = self.result_table.item(row, 0)  # 假设host在第0列
        port_item = self.result_table.item(row, 1)  # 假设port在第1列
        protocol_item = self.result_table.item(row, 2)  # 假设protocol在第2列
        
        if host_item:
            host = host_item.text().strip()
            port = port_item.text().strip() if port_item else ""
            protocol = protocol_item.text().strip().lower() if protocol_item else "http"
            
            # 清理协议格式
            protocol = protocol.split(":")[0].replace("/", "").lower()
            if protocol not in ["http", "https"]:
                protocol = "http"

            if 'https' not in host and 'http' not in host:
                # 构建URL
                if port and port.isdigit():
                    url = f"{protocol}://{host}:{port}"
                else:
                    url = f"{protocol}://{host}"
            else:
                url = host

        # print(url)
        if url:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "打开失败", f"无法打开URL: {str(e)}")

    def load_regions(self):
        """加载中国地区列表"""
        # 中国省份数据
        self.china_regions = {
            "北京市": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区", "顺义区", "通州区", "大兴区", "房山区", "门头沟区", "昌平区", "平谷区", "密云区", "延庆区"],
            "天津市": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区", "滨海新区", "宁河区", "静海区", "蓟州区"],
            "河北省": ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"],
            "山西省": ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"],
            "内蒙古自治区": ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市", "兴安盟", "锡林郭勒盟", "阿拉善盟"],
            "辽宁省": ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"],
            "吉林省": ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市", "延边朝鲜族自治州"],
            "黑龙江省": ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市", "黑河市", "绥化市", "大兴安岭地区"],
            "上海市": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区", "青浦区", "奉贤区", "崇明区"],
            "江苏省": ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市"],
            "浙江省": ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"],
            "安徽省": ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市", "池州市", "宣城市"],
            "福建省": ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市"],
            "江西省": ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市", "上饶市"],
            "山东省": ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市", "临沂市", "德州市", "聊城市", "滨州市", "菏泽市"],
            "河南省": ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市", "济源市"],
            "湖北省": ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市", "恩施土家族苗族自治州", "仙桃市", "潜江市", "天门市", "神农架林区"],
            "湖南省": ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市", "永州市", "怀化市", "娄底市", "湘西土家族苗族自治州"],
            "广东省": ["广州市", "韶关市", "深圳市", "珠海市", "汕头市", "佛山市", "江门市", "湛江市", "茂名市", "肇庆市", "惠州市", "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市"],
            "广西壮族自治区": ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市", "河池市", "来宾市", "崇左市"],
            "海南省": ["海口市", "三亚市", "三沙市", "儋州市", "五指山市", "琼海市", "文昌市", "万宁市", "东方市", "定安县", "屯昌县", "澄迈县", "临高县", "白沙黎族自治县", "昌江黎族自治县", "乐东黎族自治县", "陵水黎族自治县", "保亭黎族苗族自治县", "琼中黎族苗族自治县"],
            "重庆市": ["万州区", "涪陵区", "渝中区", "大渡口区", "江北区", "沙坪坝区", "九龙坡区", "南岸区", "北碚区", "綦江区", "大足区", "渝北区", "巴南区", "黔江区", "长寿区", "江津区", "合川区", "永川区", "南川区", "璧山区", "铜梁区", "潼南区", "荣昌区", "开州区", "梁平区", "武隆区"],
            "四川省": ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市", "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州"],
            "贵州省": ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市", "黔西南布依族苗族自治州", "黔东南苗族侗族自治州", "黔南布依族苗族自治州"],
            "云南省": ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市", "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州", "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州"],
            "西藏自治区": ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市", "阿里地区"],
            "陕西省": ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
            "甘肃省": ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市", "陇南市", "临夏回族自治州", "甘南藏族自治州"],
            "青海省": ["西宁市", "海东市", "海北藏族自治州", "黄南藏族自治州", "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州", "海西蒙古族藏族自治州"],
            "宁夏回族自治区": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
            "新疆维吾尔自治区": ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市", "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区", "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区"],
            "台湾省": ["台北市", "新北市", "桃园市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉义市", "新竹县", "苗栗县", "彰化县", "南投县", "云林县", "嘉义县", "屏东县", "宜兰县", "花莲县", "台东县", "澎湖县", "金门县", "连江县"],
            "香港特别行政区": ["中西区", "湾仔区", "东区", "南区", "油尖旺区", "深水埗区", "九龙城区", "黄大仙区", "观塘区", "荃湾区", "屯门区", "元朗区", "北区", "大埔区", "西贡区", "沙田区", "葵青区", "离岛区"],
            "澳门特别行政区": ["花地玛堂区", "圣安多尼堂区", "大堂区", "望德堂区", "顺势堂区", "嘉模堂区", "圣方济各堂区", "路氹城"]
        }

        # 创建省份选择框
        self.province_combo = QComboBox()
        # 根据DPI缩放调整字体大小
        font_size = int(10 * self.dpi_scale)
        self.province_combo.setFont(QFont("PingFang SC", font_size))
        self.province_combo.addItems(["选择省份"] + list(self.china_regions.keys()))
        self.province_combo.currentTextChanged.connect(self.update_city_combo)
        # 增加下拉框宽度，使用DPI缩放
        min_width = int(150 * self.dpi_scale)
        self.province_combo.setMinimumWidth(min_width)
        # 修改调整策略为AdjustToContents，使其能够根据内容调整大小
        self.province_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # 增加下拉列表宽度，使其能够显示完整内容
        dropdown_width = int(200 * self.dpi_scale)
        self.province_combo.view().setMinimumWidth(dropdown_width)

        # 创建城市选择框
        self.city_combo = QComboBox()
        self.city_combo.setFont(QFont("PingFang SC", font_size))
        self.city_combo.addItem("选择城市")
        # 设置下拉框尺寸
        self.city_combo.setMinimumWidth(min_width)
        # 修改调整策略为AdjustToContents，使其能够根据内容调整大小
        self.city_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # 增加下拉列表宽度，使其能够显示完整内容
        self.city_combo.view().setMinimumWidth(dropdown_width)

        # 更新搜索布局
        search_layout = self.findChild(QHBoxLayout)
        if search_layout:
            # 添加地区选择控件
            search_layout.insertWidget(1, QLabel("省份:"))
            search_layout.insertWidget(2, self.province_combo)
            search_layout.insertWidget(3, QLabel("城市:"))
            search_layout.insertWidget(4, self.city_combo)

    def update_city_combo(self, province):
        """更新城市选择框"""
        self.city_combo.clear()
        if province in self.china_regions:
            self.city_combo.addItems(["选择城市"] + self.china_regions[province])
        else:
            self.city_combo.addItem("选择城市")

    def load_last_query(self):
        """加载上次的查询"""
        last_query = self.config.get('last_query', '')
        if last_query:
            self.query_input.setText(last_query)

        # 加载上次选择的地区
        last_province = self.config.get('last_province', '')
        last_city = self.config.get('last_city', '')
        
        if last_province and last_province in self.china_regions:
            self.province_combo.setCurrentText(last_province)
            if last_city and last_city in self.china_regions[last_province]:
                self.city_combo.setCurrentText(last_city)

    def search(self):
        """执行搜索"""
        # 获取查询参数
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入查询语句")
            return

        # 获取地区参数
        province = self.province_combo.currentText()
        city = self.city_combo.currentText()
        region = ""
        if province != "选择省份":
            if city != "选择城市":
                region = f"{province} {city}"
            else:
                region = province

        # 保存查询参数
        self.config.set('last_query', query)
        self.config.set('last_province', province)
        self.config.set('last_city', city)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.search_button.setEnabled(False)

        if self.current_mode == 0:  # FOFA模式
            # 检查FOFA API是否已配置
            if not self.config.is_fofa_configured():
                QMessageBox.warning(self, "警告", "请先在配置页面设置FOFA API凭证")
                self.progress_bar.setVisible(False)
                self.search_button.setEnabled(True)
                return

            self.status_changed.emit("正在查询FOFA...")

            # 创建并启动搜索线程
            self.search_thread = FofaSearchThread(
                fofa_api=self.fofa_api,
                query=query,
                region=region if region else None,
                page=self.current_page,
                size=self.page_size
            )
        else:  # Quake模式
            # 检查Quake API是否已配置
            if not self.config.is_quake_configured():
                QMessageBox.warning(self, "警告", "请先在配置页面设置Quake API凭证")
                self.progress_bar.setVisible(False)
                self.search_button.setEnabled(True)
                return

            self.status_changed.emit("正在查询Quake...")

            # 创建并启动搜索线程
            self.search_thread = QuakeSearchThread(
                quake_api=self.quake_api,
                query=query,
                page=self.current_page,
                size=self.page_size
            )
        self.search_thread.search_finished.connect(self.handle_search_result)
        self.search_thread.search_error.connect(self.handle_search_error)
        self.search_thread.start()

    def handle_search_result(self, result):
        """处理搜索结果"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)

        # 保存结果
        self.search_results = result

        # 更新状态
        self.status_changed.emit(f"查询完成，共找到 {result.get('size', 0)} 条结果")

        # 显示结果
        self.display_results(result)

        # 启用导出按钮
        self.export_button.setEnabled(True)

        # 更新分页按钮状态
        self.update_pagination()

    def handle_search_error(self, error_message):
        """处理搜索错误"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)

        # 显示错误消息
        QMessageBox.critical(self, "错误", f"查询失败: {error_message}")
        self.status_changed.emit("查询失败")

    def display_results(self, result):
        """显示查询结果"""
        # 清空表格
        self.result_table.clear()

        # 获取结果和字段
        data = result.get("results", [])
        fields = result.get("fields", ["host", "ip", "port", "protocol", "title", "domain", "server", "city"])

        # 英文列名到中文列名的映射
        field_name_map = {
            'host': '主机',
            'ip': 'IP地址',
            'port': '端口',
            'protocol': '协议',
            'title': '标题',
            'server': '服务器',
            'domain': '域名',
            'city': '城市',
            'country': '国家',
            'province': '省份',
            'os': '操作系统',
            'banner': '横幅',
            'cert': '证书',
            'icp': 'ICP备案',
            'version': '版本',
            'type': '类型',
            'product': '产品',
            'lastupdatetime': '更新时间',
            'cname': 'CNAME',
            'header': '头信息',
            'fid': 'FID',
            'structinfo': '结构信息',
            'icon_hash': '图标哈希',
            'certs_valid': '证书有效性',
            'certs_issuer': '证书颁发者',
            'jarm': 'JARM',
            'service': '服务',
            'asn': 'ASN',
            'org': '组织',
            'base_protocol': '基础协议',
            'link': '链接',
            'status_code': '状态码',
            'component': '组件',
            'language': '语言',
            'app': '应用',
            'framework': '框架',
            'body': '正文'
        }
        
        # 转换列名为中文
        chinese_fields = []
        for field in fields:
            if field in field_name_map:
                chinese_fields.append(field_name_map[field])
            else:
                chinese_fields.append(field)  # 如果没有对应的中文名，保留原名
        
        # 设置表格列数和表头
        self.result_table.setColumnCount(len(fields))
        self.result_table.setHorizontalHeaderLabels(chinese_fields)

        # 设置表格行数
        self.result_table.setRowCount(len(data))

        # 填充表格
        for row, item_data in enumerate(data):
            for col, value in enumerate(item_data):
                table_item = QTableWidgetItem(str(value))
                self.result_table.setItem(row, col, table_item)

        # 调整列宽
        self.adjust_table_columns(fields)
        
    def adjust_table_columns(self, fields):
        """调整表格列宽"""
        header = self.result_table.horizontalHeader()
        
        # 根据DPI缩放调整列宽
        scale_factor = self.dpi_scale
        
        # 设置默认大小为内容适应
        default_width = int(120 * scale_factor)
        header.setDefaultSectionSize(default_width)
        
        # 为常用字段设置固定宽度（考虑DPI缩放）
        fixed_width_columns = {
            'host': int(200 * scale_factor),  # 主机列宽
            'ip': int(120 * scale_factor),    # IP列宽
            'port': int(60 * scale_factor),   # 端口列宽
            'protocol': int(80 * scale_factor), # 协议列宽
            'title': int(250 * scale_factor),  # 标题列宽
            'domain': int(150 * scale_factor), # 域名列宽
            'server': int(150 * scale_factor), # 服务器列宽
            'city': int(100 * scale_factor),   # 城市列宽
            'os': int(120 * scale_factor)      # 系统名称列宽
        }
        
        # 先将所有列设置为固定宽度模式
        for col in range(len(fields)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
        # 为每列设置适当的宽度
        for col, field in enumerate(fields):
            if field in fixed_width_columns:
                width = fixed_width_columns[field]
                header.resizeSection(col, width)
            else:
                # 对于未知字段，设置一个合理的默认宽度
                header.resizeSection(col, default_width)
        
        # 设置最后一列为自动拉伸，填充剩余空间
        if len(fields) > 0:
            header.setSectionResizeMode(len(fields) - 1, QHeaderView.Stretch)
        
        # 确保表格在初始显示时能看到所有列
        self.result_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def update_pagination(self):
        """更新分页按钮状态"""
        if not self.search_results:
            return

        total = self.search_results.get("size", 0)
        total_pages = (total + self.page_size - 1) // self.page_size

        # 更新页码标签
        self.page_label.setText(f"第{self.current_page}页 / 共{total_pages}页")

        # 更新按钮状态
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(self.current_page < total_pages)

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.search()

    def next_page(self):
        """下一页"""
        self.current_page += 1
        self.search()

    def export_results(self):
        """导出查询结果"""
        if not self.search_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        # 创建导出菜单
        menu = QMenu(self)
        export_csv_action = QAction("导出为CSV", self)
        export_excel_action = QAction("导出为Excel", self)
        export_json_action = QAction("导出为JSON", self)
        menu.addAction(export_csv_action)
        menu.addAction(export_excel_action)
        menu.addAction(export_json_action)
        action = menu.exec_(QCursor.pos())
        if action == export_csv_action:
            self.export_to_csv()
        elif action == export_excel_action:
            self.export_to_excel()
        elif action == export_json_action:
            self.export_to_json()
    def export_to_csv(self):
        """导出为CSV"""
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录", os.path.expanduser("~"))
        if not output_dir:
            return

        # 导出结果
        exporter = ResultExporter()
        result_file = exporter.export_to_csv(self.search_results.get("results", []), output_dir)

        if result_file:
            QMessageBox.information(self, "导出成功", f"结果已导出到: {result_file}")
        else:
            QMessageBox.critical(self, "导出失败", "导出CSV失败")
    def export_to_excel(self):
        """导出为Excel"""
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录", os.path.expanduser("~"))
        if not output_dir:
            return
        # 导出结果
        exporter = ResultExporter()
        result_file = exporter.export_to_excel(self.search_results.get("results", []), output_dir)
        if result_file:
            QMessageBox.information(self, "导出成功", f"结果已导出到: {result_file}")
        else:
            QMessageBox.critical(self, "导出失败", "导出Excel失败")
    def export_to_json(self):
        """导出为JSON"""
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录", os.path.expanduser("~"))
        if not output_dir:
            return
        # 导出结果
        exporter = ResultExporter()
        result_file = exporter.export_to_json(self.search_results.get("results", []), output_dir)
        if result_file:
            QMessageBox.information(self, "导出成功", f"结果已导出到: {result_file}")
        else:
            QMessageBox.critical(self, "导出失败", "导出JSON失败")
    def show_context_menu(self, pos):
        """显示右键菜单"""
        # 获取选中的行
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            return
        selected_row = selected_items[0].row()
        selected_data = [self.result_table.item(selected_row, col).text() for col in range(self.result_table.columnCount())]
        # 创建菜单
        menu = QMenu(self)
        # scan_nuclei_action = QAction("使用Nuclei扫描", self)
        scan_afrog_action = QAction("使用Afrog扫描", self)
        # menu.addAction(scan_nuclei_action)
        menu.addAction(scan_afrog_action)
        action = menu.exec_(self.result_table.viewport().mapToGlobal(pos))
        if action == scan_afrog_action:
            self.scan_with_afrog(selected_data)

    def scan_with_nuclei(self, target):
        """使用Nuclei扫描"""
        if not self.nuclei_scanner.is_available():
            QMessageBox.warning(self, "警告", "Nuclei工具未配置或不可用")
            return
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.status_changed.emit("正在使用Nuclei扫描...")
        # 创建并启动扫描线程
        self.scan_thread = ScanThread(
            scanner=self.nuclei_scanner,
            target=target[0]  # 假设第一个字段是目标地址
        )
        self.scan_thread.scan_finished.connect(self.handle_scan_result)
        self.scan_thread.scan_error.connect(self.handle_scan_error)
        self.scan_thread.start()
    def scan_with_afrog(self, target):
        """使用Afrog扫描"""
        if not self.afrog_scanner.is_available():
            QMessageBox.warning(self, "警告", "Afrog工具未配置或不可用")
            return
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.status_changed.emit("正在使用Afrog扫描...")
        # 创建并启动扫描线程
        self.scan_thread = ScanThread(
            scanner=self.afrog_scanner,
            target=target[0]  # 假设第一个字段是目标地址
        )
        self.scan_thread.scan_finished.connect(self.handle_scan_result)
        self.scan_thread.scan_error.connect(self.handle_scan_error)
        self.scan_thread.start()
    def handle_scan_result(self, result):
        """处理扫描结果"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 显示扫描结果
        if "error" in result:
            QMessageBox.critical(self, "扫描错误", result["error"])
            self.status_changed.emit("扫描失败")
            return
            
        # 检查是否有有效结果
        if not result.get("success", False) or "results" not in result:
            QMessageBox.information(self, "扫描结果", "没有找到任何结果")
            self.status_changed.emit("扫描完成，无结果")
            return
            
        # 处理Afrog扫描结果
        scan_results = result["results"]
        if not isinstance(scan_results, list):
            QMessageBox.information(self, "扫描结果", "没有找到任何结果")
            self.status_changed.emit("扫描完成，无结果")
            return
        QMessageBox.information(self, "扫描完成", "扫描已完成，正在处理结果...")
        # 提取需要显示的字段
        display_data = []
        for item in scan_results:
            if not isinstance(item, dict):
                continue
                
            display_item = {
                "目标": item.get("target", ""),
                "漏洞名称": item.get("pocinfo", {}).get("infoname", ""),
                "风险等级": item.get("pocinfo", {}).get("infoseg", ""),
                "描述": item.get("pocinfo", {}).get("infodescription", ""),
                "作者": item.get("pocinfo", {}).get("infoauthor", ""),
                "URL": item.get("fulltarget", "")
            }
            display_data.append(display_item)
            
        # 将结果传递给漏洞页
        main_window = self.window()
        if main_window and hasattr(main_window, 'get_tab'):
            vulnerability_page = main_window.get_tab("vulnerability")
            if vulnerability_page and hasattr(vulnerability_page, 'update_results'):
                vulnerability_page.update_results(display_data)

            
        # 转换为DataFrame
        df = pd.DataFrame(display_data)
        
        # 显示结果
        if df.empty:
            QMessageBox.information(self, "扫描结果", "没有找到任何结果")
            self.status_changed.emit("扫描完成，无结果")
            return
            
        # 显示结果表格
        self.result_table.clear()
        self.result_table.setRowCount(len(df))
        self.result_table.setColumnCount(len(df.columns))
        self.result_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(len(df)):
            for col, col_name in enumerate(df.columns):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.result_table.setItem(row, col, item)
                
        # 调整列宽
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        
        # 更新状态
        self.status_changed.emit(f"扫描完成，共找到 {len(df)} 条结果")
        
        # 启用导出按钮
        self.export_button.setEnabled(True)

    def handle_scan_error(self, error_message):
        """处理扫描错误"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        # 显示错误消息
        QMessageBox.critical(self, "扫描错误", f"扫描失败: {error_message}")
        self.status_changed.emit("扫描失败")
    def show_fingerprint_tab(self):
        """批量检索漏洞指纹"""
        # 获取当前窗口的父窗口（主窗口）
        main_window = self.window()
        
        # 获取漏洞指纹标签页
        fingerprint_tab = None
        for i in range(main_window.tab_widget.count()):
            tab = main_window.tab_widget.widget(i)
            if hasattr(tab, 'fingerprints') and hasattr(tab, 'fingerprint_file'):
                fingerprint_tab = tab
                break
        
        if not fingerprint_tab:
            QMessageBox.warning(self, "警告", "未找到漏洞指纹标签页")
            return
            
        # 检查是否有保存的指纹
        if not fingerprint_tab.fingerprints:
            QMessageBox.warning(self, "警告", "没有保存的漏洞指纹，请先在指纹标签页添加指纹")
            # 切换到漏洞指纹标签页
            main_window.switch_to_tab("vulnerability_fingerprint")
            return
            
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.status_changed.emit("正在批量检索漏洞指纹...")
        
        # 执行批量检索
        self.batch_search_fingerprints(fingerprint_tab.fingerprints)

    def batch_search_fingerprints(self, fingerprints):
        """批量检索漏洞指纹"""
        # 检查FOFA API是否已配置
        if not self.config.is_fofa_configured():
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "警告", "请先在配置页面设置FOFA API凭证")
            return

        # 获取地区参数
        province = self.province_combo.currentText()
        city = self.city_combo.currentText()
        region = ""
        if province != "选择省份":
            if city != "选择城市":
                region = f"{province} {city}"
            else:
                region = province

        # 创建一个线程来执行批量检索，避免界面卡顿
        self.batch_search_thread = QThread()
        self.batch_search_worker = BatchSearchWorker(self.fofa_api, fingerprints, region)
        self.batch_search_worker.moveToThread(self.batch_search_thread)

        # 连接信号
        self.batch_search_thread.started.connect(self.batch_search_worker.run)
        self.batch_search_worker.search_progress.connect(self.update_batch_search_progress)
        self.batch_search_worker.search_finished.connect(self.handle_batch_search_result)
        self.batch_search_worker.search_error.connect(self.handle_batch_search_error)
        self.batch_search_worker.finished.connect(self.batch_search_thread.quit)

        # 启动线程
        self.batch_search_thread.start()
        
    def update_batch_search_progress(self, current, total, fingerprint_name):
        """更新批量检索进度"""
        self.status_changed.emit(f"正在检索 ({current}/{total}): {fingerprint_name}")
        
    def handle_batch_search_result(self, results):
        """处理批量检索结果"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 检查是否有结果
        if not results:
            QMessageBox.information(self, "检索完成", "批量检索完成，但没有找到任何结果")
            self.status_changed.emit("批量检索完成，无结果")
            return
            
        # 合并所有结果
        all_results = []
        for result in results:
            if "results" in result and result["results"]:
                all_results.extend(result["results"])

        if not all_results:
            QMessageBox.information(self, "检索完成", "批量检索完成，但没有找到任何结果")
            self.status_changed.emit("批量检索完成，无结果")
            return

        # 保存合并后的结果
        self.search_results = {
            "results": all_results,
            "fields": results[0].get("fields", ["host", "ip", "port", "protocol", "title", "domain", "server", "city"]),
            "size": len(all_results)
        }
        
        # 显示结果
        self.display_results(self.search_results)
        
        # 启用导出按钮
        self.export_button.setEnabled(True)
        
        # 更新状态
        self.status_changed.emit(f"批量检索完成，共找到 {len(all_results)} 条结果")
        
    def handle_batch_search_error(self, error_message):
        """处理批量检索错误"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 显示错误消息
        QMessageBox.critical(self, "检索错误", f"批量检索失败: {error_message}")
        self.status_changed.emit("批量检索失败")

    def toggle_search_mode(self):
        """切换搜索模式"""
        self.current_mode = 1 - self.current_mode  # 在0和1之间切换
        mode_name = "FOFA" if self.current_mode == 0 else "Quake"
        self.mode_button.setText(f"切换模式({mode_name})")
        
        # 根据模式更新UI状态
        if self.current_mode == 0:  # FOFA模式
            self.province_combo.setEnabled(True)
            self.city_combo.setEnabled(True)
            self.status_changed.emit("已切换至FOFA模式，支持按地区筛选")
        else:  # Quake模式
            self.province_combo.setEnabled(True)
            self.city_combo.setEnabled(True)
            self.status_changed.emit("已切换至Quake模式，支持按地区筛选(使用province:\"省份\" city:\"城市\"语法)")
        
    def closeEvent(self, event):
        """关闭事件处理"""
        """保存配置"""
        if self.config.save_config():
            print("配置已保存")
        else:
            print("配置保存失败")
        event.accept()
    def show(self):
        """显示主页面"""
        # 显示窗口
        super().show()

        # 扫描结果展示
        result_group = QGroupBox("最近扫描结果")
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["目标", "风险等级", "发现时间", "状态"])
        
        # 添加风险等级颜色标记
        self.result_table.itemChanged.connect(self.apply_risk_color)

        # 添加统计图表
        chart_widget = QWidget()
        chart_layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget(title="漏洞分布统计")
        chart_layout.addWidget(self.plot_widget)
        chart_widget.setLayout(chart_layout)

        # 使用QSplitter实现可调节布局
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.result_table)
        splitter.addWidget(chart_widget)
        splitter.setSizes([400, 200])

    def apply_risk_color(self, item):
        if item.column() == 1:  # 风险等级列
            text = item.text().lower()
            colors = {
                'critical': '#ff4444',
                'high': '#ffa500',
                'medium': '#ffff00',
                'low': '#00ff00'
            }
            item.setBackground(QColor(colors.get(text, '#ffffff')))
