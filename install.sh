#!/bin/bash
# ============================================
# 快分享 - Debian 服务器一键安装脚本
# 适用于 root 用户
# ============================================

set -e

# ── 配置 ──
DEPLOY_PATH="/opt/fileshare"
SERVICE_NAME="fileshare"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"
GITHUB_REPO="https://github.com/dakerclaw/fileshare.git"
PORT=5200

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo "========================================"
echo "  快分享 - Debian 一键安装"
echo "========================================"
echo ""

# ── 1. 检查 root ──
if [ "$(id -u)" -ne 0 ]; then
    error "请使用 root 用户运行此脚本，或加 sudo"
fi

# ── 2. 安装系统依赖 ──
info "安装系统依赖（Python3, pip, git）..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip git > /dev/null 2>&1
info "系统依赖安装完成"

# ── 3. 克隆项目 ──
info "克隆项目到 ${DEPLOY_PATH}..."
if [ -d "${DEPLOY_PATH}" ]; then
    warn "目录已存在，将执行 git pull 更新..."
    cd "${DEPLOY_PATH}"
    git pull origin main
else
    git clone "${GITHUB_REPO}" "${DEPLOY_PATH}"
fi
info "项目就绪"

# ── 4. 创建虚拟环境 ──
info "创建 Python 虚拟环境..."
cd "${DEPLOY_PATH}"
if [ -d "venv" ]; then
    warn "虚拟环境已存在，先删除..."
    rm -rf venv
fi
python3 -m venv venv

# ── 5. 安装 Python 依赖 ──
info "安装 Python 依赖..."
source venv/bin/activate
python3 -m ensurepip > /dev/null 2>&1
pip install --quiet flask qrcode pillow
info "依赖安装完成"

# ── 6. 配置 systemd 服务 ──
info "配置 systemd 服务..."
cat > "${DEPLOY_PATH}/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=快分享 File Share Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${DEPLOY_PATH}
ExecStart=${DEPLOY_PATH}/venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cp "${DEPLOY_PATH}/${SERVICE_NAME}.service" "${SYSTEMD_SERVICE}"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}" > /dev/null 2>&1
info "服务已设置开机自启"

# ── 7. 启动服务 ──
info "启动服务..."
systemctl restart "${SERVICE_NAME}"
sleep 1

if systemctl is-active --quiet "${SERVICE_NAME}"; then
    IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo "========================================"
    info  "安装成功！"
    echo "========================================"
    echo "  访问地址：http://${IP}:${PORT}"
    echo "  管理命令："
    echo "    systemctl status ${SERVICE_NAME}   # 查看状态"
    echo "    systemctl restart ${SERVICE_NAME}  # 重启"
    echo "    journalctl -u ${SERVICE_NAME} -f    # 查看日志"
    echo "========================================"
else
    error "服务启动失败，请执行 journalctl -u ${SERVICE_NAME} -f 查看日志"
fi
