"""
文件/文本中转站后端 - Flask
功能：文本粘贴分享、文件上传分享，生成分享链接和二维码
限制：单文件最大2GB，总存储5GB，超出优先删除旧文件
"""
import os
import io
import json
import time
import uuid
import sqlite3
import hashlib
import base64
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory, abort

app = Flask(__name__, static_folder='static')

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
DB_PATH = BASE_DIR / 'data.db'

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024   # 2 GB per file
MAX_TOTAL_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB total
SHARE_ID_LEN = 8

UPLOAD_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS shares (
            id          TEXT PRIMARY KEY,
            type        TEXT NOT NULL,       -- 'text' or 'files'
            created_at  INTEGER NOT NULL,
            content     TEXT,                -- for text shares
            title       TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS share_files (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            share_id    TEXT NOT NULL,
            filename    TEXT NOT NULL,
            size        INTEGER NOT NULL,
            stored_name TEXT NOT NULL,
            created_at  INTEGER NOT NULL,
            FOREIGN KEY(share_id) REFERENCES shares(id)
        );
        CREATE INDEX IF NOT EXISTS idx_share_files_share ON share_files(share_id);
        CREATE INDEX IF NOT EXISTS idx_shares_created ON shares(created_at);
        """)

init_db()

# ─────────────────────────────────────────────
# Storage management
# ─────────────────────────────────────────────
def get_total_used():
    with get_db() as db:
        row = db.execute("SELECT COALESCE(SUM(size),0) AS total FROM share_files").fetchone()
    return int(row['total'])

def evict_old_files(needed_bytes):
    """Delete oldest shares until we have enough space."""
    freed = 0
    with get_db() as db:
        # get shares ordered by oldest first
        shares = db.execute(
            "SELECT id FROM shares ORDER BY created_at ASC"
        ).fetchall()
        for share in shares:
            if freed >= needed_bytes:
                break
            sid = share['id']
            files = db.execute(
                "SELECT stored_name, size FROM share_files WHERE share_id=?", (sid,)
            ).fetchall()
            share_size = sum(f['size'] for f in files)
            # delete files on disk
            for f in files:
                fpath = UPLOAD_DIR / f['stored_name']
                try:
                    fpath.unlink(missing_ok=True)
                except Exception:
                    pass
            db.execute("DELETE FROM share_files WHERE share_id=?", (sid,))
            db.execute("DELETE FROM shares WHERE id=?", (sid,))
            freed += share_size

def ensure_space(needed_bytes):
    """Ensure there is enough total storage space."""
    total = get_total_used()
    available = MAX_TOTAL_SIZE - total
    if available < needed_bytes:
        evict_old_files(needed_bytes - available)

# ─────────────────────────────────────────────
# QR code generation (returns base64 PNG)
# ─────────────────────────────────────────────
def make_qr_base64(url: str) -> str:
    try:
        import qrcode
        from PIL import Image
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        return ''

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def new_id():
    return uuid.uuid4().hex[:SHARE_ID_LEN]

def get_base_url():
    """Determine the base URL from request context."""
    return request.host_url.rstrip('/')

# ─────────────────────────────────────────────
# Routes - Static files
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(str(BASE_DIR / 'static'), 'index.html')

@app.route('/s/<share_id>')
def share_page(share_id):
    return send_from_directory(str(BASE_DIR / 'static'), 'index.html')

# ─────────────────────────────────────────────
# API - Text share
# ─────────────────────────────────────────────
@app.route('/api/text', methods=['POST'])
def create_text_share():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    title = data.get('title', '').strip()[:200]
    if not content:
        return jsonify({'error': '内容不能为空'}), 400
    if len(content) > 10 * 1024 * 1024:  # 10MB text limit
        return jsonify({'error': '文本过长（最大10MB）'}), 400

    sid = new_id()
    now = int(time.time())
    with get_db() as db:
        db.execute(
            "INSERT INTO shares(id,type,created_at,content,title) VALUES(?,?,?,?,?)",
            (sid, 'text', now, content, title)
        )

    base_url = get_base_url()
    share_url = f"{base_url}/s/{sid}"
    qr = make_qr_base64(share_url)
    return jsonify({'id': sid, 'url': share_url, 'qr': qr})

# ─────────────────────────────────────────────
# API - File share
# ─────────────────────────────────────────────
@app.route('/api/files', methods=['POST'])
def create_file_share():
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '没有选择文件'}), 400

    # Check individual file sizes and calculate total
    total_new = 0
    file_infos = []
    for f in files:
        # Read into memory to check size (stream friendly)
        data = f.read()
        size = len(data)
        if size > MAX_FILE_SIZE:
            return jsonify({'error': f'文件 {f.filename} 超过单文件2GB限制'}), 400
        total_new += size
        file_infos.append((f.filename, size, data))

    if total_new > MAX_TOTAL_SIZE:
        return jsonify({'error': '本次上传文件总量超过5GB限制'}), 400

    # Ensure storage space
    ensure_space(total_new)

    sid = new_id()
    now = int(time.time())
    title = request.form.get('title', '').strip()[:200]

    with get_db() as db:
        db.execute(
            "INSERT INTO shares(id,type,created_at,title) VALUES(?,?,?,?)",
            (sid, 'files', now, title)
        )
        for orig_name, size, data in file_infos:
            ext = Path(orig_name).suffix
            stored_name = f"{uuid.uuid4().hex}{ext}"
            fpath = UPLOAD_DIR / stored_name
            fpath.write_bytes(data)
            db.execute(
                "INSERT INTO share_files(share_id,filename,size,stored_name,created_at) VALUES(?,?,?,?,?)",
                (sid, orig_name, size, stored_name, now)
            )

    base_url = get_base_url()
    share_url = f"{base_url}/s/{sid}"
    qr = make_qr_base64(share_url)
    return jsonify({'id': sid, 'url': share_url, 'qr': qr})

# ─────────────────────────────────────────────
# API - Get share info
# ─────────────────────────────────────────────
@app.route('/api/share/<share_id>', methods=['GET'])
def get_share(share_id):
    with get_db() as db:
        share = db.execute("SELECT * FROM shares WHERE id=?", (share_id,)).fetchone()
        if not share:
            return jsonify({'error': '链接不存在或已过期'}), 404
        result = {
            'id': share['id'],
            'type': share['type'],
            'title': share['title'],
            'created_at': share['created_at'],
        }
        if share['type'] == 'text':
            result['content'] = share['content']
        else:
            files = db.execute(
                "SELECT filename, size, id FROM share_files WHERE share_id=?",
                (share_id,)
            ).fetchall()
            result['files'] = [
                {'filename': f['filename'], 'size': f['size'], 'file_id': f['id']}
                for f in files
            ]
    return jsonify(result)

# ─────────────────────────────────────────────
# API - Download file
# ─────────────────────────────────────────────
@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM share_files WHERE id=?", (file_id,)
        ).fetchone()
    if not row:
        abort(404)
    fpath = UPLOAD_DIR / row['stored_name']
    if not fpath.exists():
        abort(404)
    return send_file(
        str(fpath),
        as_attachment=True,
        download_name=row['filename']
    )

# ─────────────────────────────────────────────
# API - Storage stats
# ─────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    used = get_total_used()
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) AS c FROM shares").fetchone()['c']
    return jsonify({
        'used': used,
        'total': MAX_TOTAL_SIZE,
        'used_pct': round(used / MAX_TOTAL_SIZE * 100, 1),
        'share_count': count
    })

# ─────────────────────────────────────────────
# API - Delete share
# ─────────────────────────────────────────────
@app.route('/api/share/<share_id>', methods=['DELETE'])
def delete_share(share_id):
    with get_db() as db:
        files = db.execute(
            "SELECT stored_name FROM share_files WHERE share_id=?", (share_id,)
        ).fetchall()
        for f in files:
            fpath = UPLOAD_DIR / f['stored_name']
            try:
                fpath.unlink(missing_ok=True)
            except Exception:
                pass
        db.execute("DELETE FROM share_files WHERE share_id=?", (share_id,))
        db.execute("DELETE FROM shares WHERE id=?", (share_id,))
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=False)
