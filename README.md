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

> 需要 Python 3.8+（Linux/macOS 请确认使用 `python3` 命令）。

```bash
# 1. 克隆仓库
git clone https://github.com/dakerclaw/fileshare.git
cd fileshare

# 2. 创建并激活虚拟环境
python3 -m venv venv

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

> **提示**：每次重新打开终端后，需先执行 `source venv/bin/activate`（macOS/Linux）或 `venv\Scripts\activate`（Windows）激活虚拟环境，再运行 `python app.py`。

### Windows 双击启动

直接双击项目目录下的 `start.bat`，服务自动启动并打印访问地址（无需手动激活虚拟环境）。

---

## 部署到 Linux/macOS 服务器（后台运行）

使用 systemd 配置为系统服务，支持开机自启、自动重启。

### Debian / Ubuntu 一键安装（root 用户）

```bash
# 下载并执行安装脚本
curl -fsSL https://raw.githubusercontent.com/dakerclaw/fileshare/main/install.sh | bash
```

安装脚本会自动完成：安装依赖 → 克隆项目 → 配置 systemd → 启动服务。

> 如需手动安装，参考下方「手动部署」章节。

### 手动部署

> **注意**：以下路径以 `/opt/fileshare` 为例，如实际安装位置不同，请将路径替换为实际路径，并同步修改 `fileshare.service` 中的对应配置。

#### 1. 上传项目

```bash
# 在服务器上，克隆到实际路径（如 ~/fileshare 或 /opt/fileshare）
git clone https://github.com/dakerclaw/fileshare.git /opt/fileshare
cd /opt/fileshare
python3 -m venv venv
source venv/bin/activate
python3 -m ensurepip
pip install flask qrcode pillow
```

#### 2. 安装 systemd 服务

编辑 `fileshare.service`，按实际路径修改后，再执行后续命令：

```
# fileshare.service 示例（/opt/fileshare 路径）
[Service]
WorkingDirectory=/opt/fileshare
ExecStart=/opt/fileshare/venv/bin/python app.py
```

```bash
# 将服务文件复制到 systemd 目录（需 sudo）
sudo cp fileshare.service /etc/systemd/system/fileshare.service

# 重载配置并启动
sudo systemctl daemon-reload
sudo systemctl enable fileshare
sudo systemctl start fileshare
```

#### 3. 管理服务

```bash
sudo systemctl status fileshare    # 查看状态
sudo systemctl stop fileshare      # 停止
sudo systemctl start fileshare    # 启动
sudo systemctl restart fileshare   # 重启
sudo journalctl -u fileshare -f   # 查看实时日志
```

访问 **http://服务器IP:5200** 即可使用。如需外网访问，请确保防火墙开放 5200 端口。

---

## 更新服务

当 GitHub 仓库有新版本时，在服务器上执行：

```bash
# 1. 进入项目目录（替换为实际路径）
cd ~/fileshare

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 拉取最新代码
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt

# 5. 重启服务
sudo systemctl restart fileshare

# 6. 确认服务正常运行
sudo systemctl status fileshare
```

> **提示**：如修改了 `fileshare.service` 文件，需执行 `sudo systemctl daemon-reload` 后再重启服务。

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

### Debian / Ubuntu（root 用户）

```bash
curl -fsSL https://raw.githubusercontent.com/dakerclaw/fileshare/main/uninstall.sh | bash
```

或手动卸载：

```bash
# 1. 停止并删除 systemd 服务
systemctl stop fileshare
systemctl disable fileshare
rm /etc/systemd/system/fileshare.service
systemctl daemon-reload

# 2. 删除项目目录（含虚拟环境、数据库和上传文件）
rm -rf /opt/fileshare
```

---

## 文件结构

```
fileshare/
├── app.py              # Flask 后端
├── start.bat           # Windows 一键启动（本地）
├── install.sh          # Linux 一键安装脚本（root）
├── uninstall.sh        # Linux 卸载脚本（root）
├── fileshare.service   # systemd 服务文件（Linux/macOS）
├── requirements.txt   # Python 依赖列表
├── data.db             # SQLite 数据库（自动创建）
├── uploads/            # 上传文件存储目录（自动创建）
├── static/
│   └── index.html      # 前端 SPA
└── README.md
```

---

## API 接口

| 方法   | 路径                        | 说明         |
|--------|-----------------------------|--------------|
| POST   | `/api/text`                 | 创建文字分享  |
| POST   | `/api/files`                | 上传文件分享  |
| GET    | `/api/share/:id`            | 获取分享详情  |
| GET    | `/api/download/:file_id`    | 下载文件      |
| DELETE | `/api/share/:id`            | 删除分享      |
| GET    | `/api/stats`                | 存储使用情况  |

---

## 技术栈

- **后端**：Python + Flask + SQLite（WAL 模式）
- **前端**：纯 HTML / CSS / JS（无框架）
- **二维码**：qrcode + Pillow

---

## License

MIT
