# 雪球财经数据爬虫

## 你先把它理解成什么

这是一个 Python 课程项目，只用于学习网站分析、数据抓取和结构化存储，不做商业用途。

它做的事情很简单：

1. 你登录雪球网站。
2. 你可以复制 Cookie，也可以让 Selenium 打开浏览器读取 Cookie。
3. 运行 `python3 main.py`。
4. 程序拿到 Cookie 后开始请求接口。
5. 程序抓取少量股票榜单，再抓每只股票的详情。
6. 程序把数据保存到 MySQL 数据库，同时输出 CSV 文件。

## 项目结构

```text
pachong/
├── main.py                  # 程序入口：从这里开始看
├── config.py                # 配置：接口地址、请求间隔、默认抓取数量
├── crawler/
│   ├── base.py              # 通用请求逻辑：Session、请求头、Cookie、JSON解析
│   ├── stock_list.py        # 抓股票榜单
│   └── stock_detail.py      # 抓股票详情
├── storage/
│   ├── db_storage.py        # 保存 MySQL，默认使用
│   ├── sqlite_storage.py    # 保存 SQLite，可选
│   ├── csv_storage.py       # 保存 CSV，默认会同步输出
├── utils/
│   ├── logger.py            # 日志
│   └── retry.py             # 失败重试
└── data/                    # 输出文件目录
```

## 启动方式

先安装依赖：

```bash
pip install -r requirements.txt
```

只看运行流程，不真正请求网站：

```bash
python3 main.py --explain-strategy
```

### 方式一：剪贴板读取 Cookie

先在浏览器开发者工具里复制完整 Cookie，然后运行：

```bash
python3 main.py
```

程序会提示：

```text
Cookie>
```

这时不要粘贴，直接回车。程序会读取剪贴板里的 Cookie。

常用参数：

```bash
# 抓涨幅榜，数量改成5只
python3 main.py --boards gain --max-stocks 5

# 抓涨幅榜和跌幅榜，总共10只
python3 main.py --boards gain,loss --max-stocks 10

# 抓涨幅榜和跌幅榜，总共20只
python3 main.py --boards gain,loss --max-stocks 20
```

### 方式二：Selenium 打开浏览器登录

运行：

```bash
python3 main.py --cookie-source selenium
```

浏览器打开后，只在 Selenium 打开的这个浏览器里登录雪球；登录完成后，看到终端提示 `登录完成后回到这里，按回车继续>` 再按回车。

也可以同时指定榜单和数量：

```bash
python3 main.py --cookie-source selenium --boards gain,loss --max-stocks 20
```

### 存储方式

默认保存到 MySQL，并同步输出 CSV：

```bash
python3 main.py --boards gain --max-stocks 5
```

如果 MySQL 账号有密码，先设置环境变量：

```bash
export MYSQL_PASSWORD=你的密码
python3 main.py --boards gain --max-stocks 5
```

如果本机没有 MySQL，可以临时保存到 SQLite：

```bash
python3 main.py --storage sqlite --boards gain --max-stocks 5
```

如果只想导出 CSV：

```bash
python3 main.py --storage csv --boards gain --max-stocks 5
```

## 怎么拿 Cookie

1. 打开 Chrome。
2. 访问 `https://xueqiu.com` 并登录。
3. 按 `F12` 打开开发者工具。
4. 点 `Network`。
5. 刷新网页。
6. 随便点一个雪球请求。
7. 在 `Request Headers` 里找到 `Cookie:`。
8. 只复制 `Cookie:` 后面的值。

不要复制 `Cookie:` 这几个字，也不要复制 curl 命令。

## 学习顺序

1. 先看 [main.py](/Users/benson/Desktop/pachong/main.py)：理解程序总流程。
2. 再看 [crawler/base.py](/Users/benson/Desktop/pachong/crawler/base.py)：理解请求是怎么发出去的。
3. 再看 [crawler/stock_list.py](/Users/benson/Desktop/pachong/crawler/stock_list.py)：理解榜单接口参数。
4. 再看 [crawler/stock_detail.py](/Users/benson/Desktop/pachong/crawler/stock_detail.py)：理解如何用股票代码抓详情。
5. 最后看 [storage/db_storage.py](/Users/benson/Desktop/pachong/storage/db_storage.py)：理解数据怎么写入 MySQL。

## 项目讲解重点

- 网站分析：用开发者工具找到接口。
- 请求还原：请求头、Cookie、Session。
- Selenium 配合 requests：浏览器负责登录取 Cookie，接口请求负责抓数据。
- 反爬识别：403、429、验证码页、非 JSON 响应。
- 稳定性：请求间隔、超时、重试、失败跳过。
- 数据结构化：JSON 字段保存到 MySQL 数据表，并同步输出 CSV 文件。

## 使用说明

本项目只用于学习，不做商业用途；只做正常登录后的少量数据抓取，不涉及验证码破解、封禁规避、代理池对抗、绕过付费或绕过登录限制。
