# 雪球财经爬虫项目总结

## 一句话说明

这个项目演示了：如何登录雪球后，用 Python 模拟浏览器请求，抓取少量股票榜单和股票详情，并保存到 MySQL 数据库，同时输出 CSV 文件。

## 主流程

```text
启动 main.py
  ↓
获取 Cookie
  ↓
创建爬虫对象
  ↓
请求股票榜单接口
  ↓
拿到股票代码 symbol
  ↓
逐个请求股票详情接口
  ↓
保存 MySQL 数据库
  ↓
输出 CSV 文件
  ↓
关闭网络会话
```

## 每个模块负责什么

- `main.py`：总导演，安排先抓榜单、再抓详情、最后保存。
- `config.py`：配置文件，保存接口地址、请求间隔、默认抓取数量。
- `crawler/base.py`：所有爬虫共用的请求能力，比如请求头、Cookie、Session、JSON解析。
- `crawler/stock_list.py`：抓股票榜单。
- `crawler/stock_detail.py`：抓股票详情。
- `storage/db_storage.py`：保存 MySQL 数据库。
- `storage/sqlite_storage.py`：可选保存 SQLite 数据库文件。
- `storage/csv_storage.py`：输出 CSV 文件。
- `utils/retry.py`：请求失败时重试。
- `utils/logger.py`：打印日志，方便看程序运行到哪一步。

## 项目重点

### 1. 网站分析

用浏览器开发者工具的 `Network` 面板找到接口：

- 股票榜单接口：`list.json`
- 股票详情接口：`quote.json`

### 2. 请求还原

代码用这些信息模拟浏览器：

- `User-Agent`
- `Referer`
- `Origin`
- Cookie
- Selenium 可选读取 Cookie
- `requests.Session`

### 3. 反爬识别

如果 Cookie 错了或请求太频繁，可能遇到：

- 403
- 429
- 返回登录页
- 返回验证码页
- JSON 解析失败

这个项目只保留正常的稳定性处理：降低频率、重试、记录日志、失败跳过。

### 4. 数据结构化

接口返回的是 JSON，程序提取字段后保存到 MySQL 数据表，并同步输出 CSV 文件：

- 股票代码
- 股票名称
- 榜单类型
- 当前价
- 涨跌幅
- 市值
- 市盈率
- 抓取时间

## 常用命令

```bash
python3 main.py --explain-strategy
python3 main.py
python3 main.py --cookie-source selenium
python3 main.py --boards gain --max-stocks 5
python3 main.py --boards gain,loss --max-stocks 10
```

运行真正爬虫时，默认从剪贴板读取 Cookie；也可以用 Selenium 打开浏览器登录后读取 Cookie。

## 使用边界

本项目只用于学习和小规模数据抓取，不做商业用途；不涉及验证码破解、封禁规避、代理池对抗、绕过付费或绕过登录限制。
