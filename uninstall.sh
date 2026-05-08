#!/bin/bash
# ============================================
# 快分享 - Debian 服务器卸载脚本
# ============================================

SERVICE_NAME="fileshare"
DEPLOY_PATH="/opt/fileshare"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "========================================"
echo "  快分享 - 卸载"
echo "========================================"
echo ""

if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} 请使用 root 用户运行此脚本"
    exit 1
fi

# ── 停止并禁用服务 ──
if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    info "停止服务..."
    systemctl stop "${SERVICE_NAME}"
    systemctl disable "${SERVICE_NAME}" > /dev/null 2>&1
fi

# ── 删除 systemd 文件 ──
if [ -f "${SYSTEMD_SERVICE}" ]; then
    info "删除 systemd 服务文件..."
    rm -f "${SYSTEMD_SERVICE}"
    systemctl daemon-reload
fi

# ── 删除项目目录 ──
if [ -d "${DEPLOY_PATH}" ]; then
    warn "删除项目目录 ${DEPLOY_PATH} ..."
    rm -rf "${DEPLOY_PATH}"
fi

echo ""
info "卸载完成，所有相关文件已清除。"
