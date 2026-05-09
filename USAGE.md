# 雪球财经爬虫使用指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 先看流程

```bash
python3 main.py --explain-strategy
```

这个命令不会请求网站，只会打印运行流程。

## 3. 获取 Cookie

默认方式：打开雪球并登录，然后在浏览器开发者工具里复制 `Cookie:` 后面的值。

详细步骤见 [COOKIE_GUIDE.md](/Users/benson/Desktop/pachong/COOKIE_GUIDE.md)。

也可以使用 Selenium 打开浏览器登录：

```bash
python3 main.py --cookie-source selenium
```

注意：只在 Selenium 打开的浏览器里登录；看到终端提示 `登录完成后回到这里，按回车继续>` 后再按回车。

## 4. 运行爬虫

```bash
python3 main.py
```

程序会提示你输入：

```text
Cookie>
```

先复制 Cookie，然后在这里直接回车。程序会读取剪贴板里的 Cookie。

## 5. 常用参数

```bash
# 抓5只涨幅榜股票
python3 main.py --boards gain --max-stocks 5

# 抓10只涨幅榜和跌幅榜股票
python3 main.py --boards gain,loss --max-stocks 10

# 用 Selenium 打开浏览器登录后读取 Cookie
python3 main.py --cookie-source selenium --boards gain --max-stocks 5
```

## 6. 输出在哪里

默认会保存到 MySQL 数据库，并在 `data/` 目录同步输出 CSV 文件：

```text
数据库：xueqiu_data
```

数据库里有两张表：

```text
stock_list      # 股票榜单
stock_detail    # 股票详情
```

MySQL连接信息在 [config.py](/Users/benson/Desktop/pachong/config.py) 的 `MYSQL_CONFIG` 中配置。

如果你本机暂时没有 MySQL，可以临时保存到 SQLite：

```bash
python3 main.py --storage sqlite --boards gain --max-stocks 5
```

如果你只想保存 CSV，可以运行：

```bash
python3 main.py --storage csv --boards gain --max-stocks 5
```

## 7. 你需要讲清楚的点

1. 为什么需要 Cookie：因为部分接口需要登录状态。
2. 为什么要设置请求头：让请求更接近浏览器正常访问。
3. 为什么用 Session：复用登录状态和连接。
4. 为什么 Selenium 只负责获取 Cookie：浏览器登录方便，接口请求抓数据更快。
5. 为什么要请求间隔：避免高频访问。
6. 为什么要重试：网络请求可能临时失败。
7. 为什么要保存数据库：把 JSON 结构化成表，方便查询和后续分析。
