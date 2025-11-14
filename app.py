import os
import json
import functools
import datetime
from zoneinfo import ZoneInfo
from flask import (
    Flask, render_template, request, redirect, url_for, session, g,
    jsonify, flash
)
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from waitress import serve
from database import SessionLocal, User, BlockedKeyword, SentMessage, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)

CONFIG_FILE = 'config.json'
DATABASE_FILE = 'bot_data.db'
SH_TZ = ZoneInfo('Asia/Shanghai')

def is_configured():
    return os.path.exists(CONFIG_FILE)

def get_config():
    if not is_configured():
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}

@app.before_request
def load_db_session():
    if is_configured() and request.endpoint not in ['setup', 'static']:
        if not os.path.exists(DATABASE_FILE):
            init_db()
        g.db = SessionLocal()

@app.teardown_request
def close_db_session(exception=None):
    db = g.get('db')
    if db is not None:
        db.close()

@app.before_request
def check_configuration():
    if not is_configured() and request.endpoint not in ['setup', 'static']:
        return redirect(url_for('setup'))
    if is_configured() and request.endpoint == 'setup':
        return redirect(url_for('login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        config = get_config()
        if 'logged_in' not in session:
            if not config.get('WEB_PANEL_USER'):
                return redirect(url_for('login'))
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if is_configured():
        return redirect(url_for('login'))
    if request.method == 'POST':
        config = {}
        config['BOT_TOKEN'] = request.form.get('bot_token')
        config['ADMIN_ID'] = request.form.get('admin_id')
        config['WEB_PANEL_USER'] = request.form.get('web_user')
        config['WEB_PANEL_PASS'] = request.form.get('web_pass')
        if not all([config['BOT_TOKEN'], config['ADMIN_ID'], config['WEB_PANEL_USER'], config['WEB_PANEL_PASS']]):
            flash('所有字段均为必填项。', 'error')
            return render_template('setup.html')
        try:
            int(config['ADMIN_ID'])
        except ValueError:
            flash('管理员 UID 必须是纯数字。', 'error')
            return render_template('setup.html')
        config['SECRET_KEY'] = os.urandom(24).hex()
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            init_db()
            app.secret_key = config['SECRET_KEY']
            flash('配置成功！请登录。', 'success')
            return redirect(url_for('login'))
        except IOError as e:
            flash(f'写入配置文件失败: {e}', 'error')
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    config = get_config()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == config.get('WEB_PANEL_USER') and
                password == config.get('WEB_PANEL_PASS')):
            session['logged_in'] = True
            app.secret_key = config.get('SECRET_KEY')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    config = get_config()
    return render_template('dashboard.html', admin_user=config.get('WEB_PANEL_USER', 'Admin'))

@app.route('/api/stats')
@login_required
def api_stats():
    total_users = g.db.query(User).count()
    blocked_users = g.db.query(User).filter_by(is_blocked=True).count()
    verified_users = g.db.query(User).filter_by(is_verified=True).count()
    total_keywords = g.db.query(BlockedKeyword).count()
    return jsonify({
        'total_users': total_users,
        'blocked_users': blocked_users,
        'verified_users': verified_users,
        'total_keywords': total_keywords
    })

@app.route('/api/today_stats')
@login_required
def api_today_stats():
    now_sh = datetime.datetime.now(SH_TZ)
    start_sh = datetime.datetime(now_sh.year, now_sh.month, now_sh.day, 0, 0, 0, tzinfo=SH_TZ)
    end_sh = start_sh + datetime.timedelta(days=1)
    start_utc = start_sh.astimezone(ZoneInfo('UTC'))
    end_utc = end_sh.astimezone(ZoneInfo('UTC'))
    new_users = g.db.query(User).filter(User.created_at >= start_utc, User.created_at < end_utc).count()
    messages_q = g.db.query(SentMessage).filter(SentMessage.sent_at >= start_utc, SentMessage.sent_at < end_utc)
    messages_count = messages_q.count()
    dialog_users_count = g.db.query(SentMessage.user_id).filter(SentMessage.sent_at >= start_utc, SentMessage.sent_at < end_utc).distinct().count()
    return jsonify({
        'date': start_sh.date().isoformat(),
        'new_users_today': new_users,
        'dialog_users_today': dialog_users_count,
        'messages_today': messages_count
    })

@app.route('/api/message_stats')
@login_required
def api_message_stats():
    days = request.args.get('range', 7, type=int)
    if days <= 0:
        days = 7
    now_sh = datetime.datetime.now(SH_TZ)
    start_sh = (now_sh - datetime.timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_sh = now_sh.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_utc = start_sh.astimezone(ZoneInfo('UTC'))
    end_utc = end_sh.astimezone(ZoneInfo('UTC'))
    msgs = g.db.query(SentMessage).filter(SentMessage.sent_at >= start_utc, SentMessage.sent_at <= end_utc).all()
    counts = {}
    for i in range(days):
        d = (start_sh + datetime.timedelta(days=i)).date().isoformat()
        counts[d] = 0
    for m in msgs:
        if not m.sent_at:
            continue
        m_sh = m.sent_at.astimezone(SH_TZ)
        d = m_sh.date().isoformat()
        if d in counts:
            counts[d] += 1
    data = [{'date': d, 'count': counts[d]} for d in sorted(counts.keys())]
    return jsonify({'range_days': days, 'data': data})

@app.route('/api/messages', methods=['POST'])
@login_required
def api_add_message():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    message_text = data.get('message_text', '')
    sent_at_in = data.get('sent_at')
    if not user_id:
        return jsonify({'error': '缺少 user_id'}), 400
    db = g.db
    user = db.get(User, int(user_id))
    now_sh = datetime.datetime.now(SH_TZ)
    if not user:
        user = User(id=int(user_id), created_at=now_sh, last_seen=now_sh)
        db.add(user)
        db.commit()
        db.refresh(user)
    if sent_at_in:
        try:
            sent_dt = datetime.datetime.fromisoformat(sent_at_in)
            if sent_dt.tzinfo is None:
                sent_dt = sent_dt.replace(tzinfo=SH_TZ)
            sent_dt = sent_dt.astimezone(SH_TZ)
        except Exception:
            sent_dt = now_sh
    else:
        sent_dt = now_sh
    sent_utc = sent_dt.astimezone(ZoneInfo('UTC'))
    msg = SentMessage(user_id=int(user_id), message_text=message_text, sent_at=sent_utc)
    db.add(msg)
    user.last_seen = sent_utc
    db.commit()
    db.refresh(msg)
    return jsonify({'success': True, 'message_id': msg.pk_id, 'sent_at': sent_dt.isoformat()}), 201

@app.route('/api/keywords', methods=['GET'])
@login_required
def api_get_keywords():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query_str = request.args.get('search', '').strip().lower()
    query = g.db.query(BlockedKeyword)
    if query_str:
        search_term = f"%{query_str}%"
        query = query.filter(BlockedKeyword.keyword.like(search_term))
    total = query.count()
    keywords = query.order_by(desc(BlockedKeyword.added_at))\
                    .offset((page - 1) * per_page)\
                    .limit(per_page)\
                    .all()
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'keywords': [
            {'id': kw.id, 'keyword': kw.keyword, 'added_at': kw.added_at.isoformat() if kw.added_at else None}
            for kw in keywords
        ]
    })

@app.route('/api/keywords', methods=['POST'])
@login_required
def api_add_keyword():
    data = request.get_json(force=True, silent=True) or {}
    keywords = data.get('keywords') or data.get('keyword')
    if isinstance(keywords, str):
        keywords = [keywords]
    if not isinstance(keywords, list):
        return jsonify({'error': '无效的参数格式'}), 400
    normalized = []
    seen = set()
    for kw in keywords:
        if isinstance(kw, str):
            k = kw.strip().lower()
            if k and k not in seen:
                seen.add(k)
                normalized.append(k)
    if not normalized:
        return jsonify({'error': '没有有效关键词'}), 400
    db = g.db
    existing_objs = db.query(BlockedKeyword).filter(
        BlockedKeyword.keyword.in_(normalized)
    ).all()
    existing_set = {obj.keyword for obj in existing_objs}
    to_add = [k for k in normalized if k not in existing_set]
    added_objs = []
    if to_add:
        try:
            now = datetime.datetime.now(SH_TZ)
            for k in to_add:
                obj = BlockedKeyword(keyword=k, added_at=now)
                db.add(obj)
                added_objs.append(obj)
            db.commit()
            for obj in added_objs:
                db.refresh(obj)
        except IntegrityError:
            db.rollback()
            all_objs = db.query(BlockedKeyword).filter(
                BlockedKeyword.keyword.in_(normalized)
            ).all()
            return jsonify({
                'added': [],
                'exists': [{
                    'id': o.id,
                    'keyword': o.keyword,
                    'added_at': o.added_at.isoformat() if o.added_at else None
                } for o in all_objs]
            }), 200
        except Exception as e:
            db.rollback()
            return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    return jsonify({
        'added': [{
            'id': o.id,
            'keyword': o.keyword,
            'added_at': o.added_at.isoformat() if o.added_at else None
        } for o in added_objs],
        'exists': [{
            'id': o.id,
            'keyword': o.keyword,
            'added_at': o.added_at.isoformat() if o.added_at else None
        } for o in existing_objs]
    }), (201 if added_objs else 200)

@app.route('/api/keywords/<int:kw_id>', methods=['DELETE'])
@login_required
def api_delete_keyword(kw_id):
    kw = g.db.get(BlockedKeyword, kw_id)
    if not kw:
        return jsonify({'error': '未找到关键词'}), 404
    g.db.delete(kw)
    g.db.commit()
    return jsonify({'success': True})

@app.route('/api/users')
@login_required
def api_get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query_str = request.args.get('search', '')
    filter_by = request.args.get('filter', 'all')
    query = g.db.query(User)
    if filter_by == 'blocked':
        query = query.filter_by(is_blocked=True)
    if query_str:
        search_term = f"%{query_str}%"
        query = query.filter(
            or_(
                User.id.like(search_term),
                User.username.like(search_term),
                User.first_name.like(search_term),
                User.last_name.like(search_term)
            )
        )
    total = query.count()
    users = query.order_by(desc(User.last_seen)).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'lang_code': u.lang_code,
                'is_blocked': u.is_blocked,
                'is_verified': u.is_verified,
                'last_seen': u.last_seen.isoformat() if u.last_seen else None
            } for u in users
        ]
    })

@app.route('/api/users/<int:user_id>/block', methods=['POST'])
@login_required
def api_block_user(user_id):
    user = g.db.get(User, user_id)
    if not user:
        return jsonify({'error': '未找到用户'}), 404
    user.is_blocked = True
    g.db.commit()
    return jsonify({'success': True, 'is_blocked': True})

@app.route('/api/users/<int:user_id>/unblock', methods=['POST'])
@login_required
def api_unblock_user(user_id):
    user = g.db.get(User, user_id)
    if not user:
        return jsonify({'error': '未找到用户'}), 404
    user.is_blocked = False
    g.db.commit()
    return jsonify({'success': True, 'is_blocked': False})

@app.route('/api/user_messages')
@login_required
def api_user_messages():
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    search = request.args.get('search', '', type=str).strip()
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)
    if not user_id:
        return jsonify({'error': '缺少 user_id'}), 400
    q = g.db.query(SentMessage).filter(SentMessage.user_id == user_id)
    if search:
        q = q.filter(SentMessage.message_text.like(f"%{search}%"))
    if start_date:
        try:
            dt = datetime.datetime.fromisoformat(start_date).astimezone(ZoneInfo('UTC'))
            q = q.filter(SentMessage.sent_at >= dt)
        except:
            pass
    if end_date:
        try:
            dt = datetime.datetime.fromisoformat(end_date).astimezone(ZoneInfo('UTC'))
            q = q.filter(SentMessage.sent_at <= dt)
        except:
            pass
    total = q.count()
    msgs = q.order_by(desc(SentMessage.sent_at)) \
            .offset((page - 1) * per_page) \
            .limit(per_page).all()
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'messages': [
            {
                'text': m.message_text,
                'sent_at': m.sent_at.isoformat() if m.sent_at else None
            }
            for m in msgs
        ]
    })

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080
    if not is_configured():
        print("=" * 50)
        print("系统未配置！")
        print(f"请在浏览器中打开 http://{host}:{port}/setup 完成设置。")
        print("=" * 50)
    else:
        app.secret_key = get_config().get('SECRET_KEY', os.urandom(24))
        print("=" * 50)
        print("Web 面板已启动。")
        print(f"访问 http://{host}:{port}/")
        print("=" * 50)
    serve(app, host=host, port=port)
