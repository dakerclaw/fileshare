# 快分享

轻量的文件 / 文本中转分享工具，一键安装即可在服务器后台运行。

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?logo=flask)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 功能特性

- **文字分享** — 粘贴任意文本，生成分享链接和二维码
- **文件分享** — 支持拖拽上传多个文件，实时进度显示
- **存储管理** — 单文件最大 2 GB，总存储上限 5 GB，超出自动删除最旧分享
- **后台运行** — systemd 服务，开机自启、自动重启

---

## 一键安装（Debian / Ubuntu）

以 root 用户运行，一行命令完成全部部署：

```bash
curl -fsSL https://raw.githubusercontent.com/dakerclaw/fileshare/main/install.sh | bash
```

安装完成后，访问 **http://服务器IP:5200**

---

## 管理服务

```bash
systemctl status fileshare    # 查看状态
systemctl stop fileshare      # 停止
systemctl start fileshare    # 启动
systemctl restart fileshare   # 重启
journalctl -u fileshare -f    # 实时日志
```

---

## 更新服务

当 GitHub 仓库有新版本时，执行：

```bash
curl -fsSL https://raw.githubusercontent.com/dakerclaw/fileshare/main/install.sh | bash
```

安装脚本会自动 `git pull` 更新代码并重启服务。

---

## 卸载

以 root 用户运行：

```bash
curl -fsSL https://raw.githubusercontent.com/dakerclaw/fileshare/main/uninstall.sh | bash
```

或手动卸载：

```bash
systemctl stop fileshare
systemctl disable fileshare
rm /etc/systemd/system/fileshare.service
systemctl daemon-reload
rm -rf /opt/fileshare
```

---

## 文件结构

```
fileshare/
├── app.py              # Flask 后端
├── install.sh          # 一键安装脚本
├── uninstall.sh        # 卸载脚本
├── fileshare.service   # systemd 服务文件
├── requirements.txt    # Python 依赖
├── data.db             # SQLite 数据库（自动创建）
├── uploads/            # 上传文件存储（自动创建）
├── static/
│   └── index.html      # 前端页面
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
