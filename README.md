# VRST
本工具是一个用于解决红队进行攻防演练时快速检索漏洞储备中涉及靶标的资产，主要功能包括: 
* 通过FOFA API进行网络资产搜索 
* 对漏洞储备进行定向检索 
* 集成Afrog漏洞扫描器 
* 支持自定义配置和批量操作 
* 提供友好的图形用户界面 
* 支持多种操作系统 
* 开源项目，欢迎社区贡献 
* 使用Python编写，基于PyQt5框架 
* 支持多种漏洞指纹库 
* 提供详细的操作文档和使用指南 
* 易于扩展和定制 
* 集成社区支持和反馈渠道 
* 持续更新和维护 
* 提供安全的漏洞检索和管理功能 
* 支持多种数据格式导入和导出 

## 使用方法
```
python3 main.py
```

## 界面
### 主页面

<img width="1000" height="728" alt="image" src="https://github.com/user-attachments/assets/97761351-d4f1-4908-af47-84363292c148" />

### 指纹页面

<img width="1000" height="728" alt="image" src="https://github.com/user-attachments/assets/d5e9c6d0-acda-4f9a-85b0-d93e958a5f4e" />

### 漏洞页面

<img width="1000" height="728" alt="image" src="https://github.com/user-attachments/assets/95f72842-e690-4630-809f-6d5a8ba8e483" />


### 配置页面

<img width="1000" height="728" alt="image" src="https://github.com/user-attachments/assets/7e351456-88ec-4089-8824-31d09d5cfb2b" />

## 更新日志

```
v1.0.2 (2025-08-03) 
增加已添加指纹复制功能，方便检索某单个指纹。(@麒麟兔) 
优化查询界面，增加批量检索后系统名称显示。 
修复夸克的使用，调用API需要积分请注意。 
修复已知bug 
v1.0.1 (2025-07-12) 
增加远程更新漏洞储备指纹，团队协作。(@ppp) 
优化查询界面 
优化任务异步操作 
修复部分UI显示问题 
暂停夸克的使用，后续优化 
修复已知bug 
v1.0.0 (2025-07-10) 
初始版本发布 
实现基础漏洞检索功能 
集成FOFA API 
添加图形用户界面
```

## TodoList
* 打包可执行文件
* 优化360夸克检索
* 多线程检索
* 后续添加

