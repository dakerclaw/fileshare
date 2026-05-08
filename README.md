# 快分享

一个轻量的本地文件 / 文本中转分享工具，一行命令即可启动，生成分享链接与二维码，局域网内任何设备均可访问。

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?logo=flask)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 功能特性

- **文字分享** — 粘贴任意文本，一键生成分享链接和二维码
- **文件分享** — 支持拖拽上传单个或多个文件，实时进度显示
- **存储管理** — 单文件最大 2 GB，总存储上限 5 GB，超出自动删除最旧分享
- **无依赖前端** — 纯 HTML/CSS/JS，无需 Node.js 或任何前端构建工具
- **局域网可用** — 监听 `0.0.0.0`，同一网络下其他设备可通过 IP 访问

---

## 一键安装

> 需要 Python 3.8+。

```bash
# 1. 克隆仓库
git clone https://github.com/dakerclaw/fileshare.git
cd fileshare

# 2. 创建并激活虚拟环境
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows CMD / PowerShell
venv\Scripts\activate

# 3. 安装依赖
pip install flask qrcode pillow

# 4. 启动服务
python app.py
```

浏览器访问 **http://localhost:5200** 即可使用。

> **提示**：每次重新打开终端后，需先执行 `source venv/bin/activate`（Linux/macOS）或 `venv\Scripts\activate`（Windows）激活虚拟环境，再运行 `python app.py`。

### Windows 双击启动

直接双击项目目录下的 `start.bat`，服务自动启动并打印访问地址（无需手动激活虚拟环境）。

---

## 局域网访问

服务启动后，其他设备可通过以下地址访问（将 `<IP>` 替换为本机 IP）：

```
http://<本机IP>:5200
```

查看本机 IP：
- **Windows**：`ipconfig`
- **macOS / Linux**：`ip addr` 或 `ifconfig`

---

## 卸载

```bash
# 1. 停止服务（Ctrl+C）

# 2. 删除项目目录（含虚拟环境、数据库和上传文件）
rm -rf fileshare          # macOS / Linux
rd /s /q fileshare        # Windows CMD
```

无需额外卸载 pip 包——删除目录即彻底清除所有内容。

---

## 文件结构

```
fileshare/
├── app.py          # Flask 后端
├── start.bat       # Windows 一键启动
├── data.db         # SQLite 数据库（自动创建）
├── uploads/        # 上传文件存储目录（自动创建）
├── static/
│   └── index.html  # 前端 SPA
└── README.md
```

---

## API 接口

| 方法     | 路径                       | 说明           |
|----------|----------------------------|----------------|
| POST     | `/api/text`                | 创建文字分享   |
| POST     | `/api/files`               | 上传文件分享   |
| GET      | `/api/share/:id`           | 获取分享详情   |
| GET      | `/api/download/:file_id`   | 下载文件       |
| DELETE   | `/api/share/:id`           | 删除分享       |
| GET      | `/api/stats`               | 存储使用情况   |

---

## 技术栈

- **后端**：Python + Flask + SQLite（WAL 模式）
- **前端**：纯 HTML / CSS / JS（无框架）
- **二维码**：qrcode + Pillow

---

## License

MIT
