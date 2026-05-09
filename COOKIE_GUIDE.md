# 如何获取雪球 Cookie

Cookie 可以先理解成“登录凭证”。你登录雪球后，浏览器每次请求都会带上 Cookie，网站就知道这是你的登录状态。

## 获取步骤

1. 打开 Chrome 浏览器。
2. 访问 `https://xueqiu.com` 并登录自己的账号。
3. 按 `F12` 打开开发者工具。
4. 点击 `Network`。
5. 刷新页面。
6. 点击任意一个雪球请求。
7. 找到右侧的 `Request Headers`。
8. 找到 `Cookie:` 这一行。
9. 只复制 `Cookie:` 后面的内容。

## 正确格式

类似这样：

```text
xq_a_token=abc123; xq_r_token=def456; xq_id_token=ghi789; u=1234567890
```

## 错误格式

不要复制这个：

```text
Cookie: xq_a_token=abc123; xq_r_token=def456
```

也不要复制这个：

```text
curl 'https://xueqiu.com/' -H 'Cookie: xq_a_token=abc123'
```

## 方式一：剪贴板读取

运行：

```bash
python3 main.py
```

看到提示后直接回车：

```text
Cookie>
```

程序会读取剪贴板里的 Cookie。不要把 Cookie 写进 `config.py`，也不要放进命令行参数。

## 方式二：Selenium 读取

运行：

```bash
python3 main.py --cookie-source selenium
```

程序会打开 Chrome 浏览器。你只在这个浏览器中登录雪球，登录完成后看到终端提示 `登录完成后回到这里，按回车继续>` 再按回车，程序会读取这个浏览器里的 Cookie。

## 安全提醒

- Cookie 包含你的登录信息，不要发给别人。
- 使用后可以退出登录或重新登录刷新 Cookie。
- 本项目只用于学习和小规模数据抓取。
