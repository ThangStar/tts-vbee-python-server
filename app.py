# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from models import db, AdminKey, TTSQueue
from sqlalchemy import text
from flask_socketio import SocketIO, emit
from datetime import datetime
import sys

print("=== APP.PY LOADED ===",)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")

# Khởi tạo DB với app
db.init_app(app)

# @app.before_request
# def create_tables():
#     with app.app_context():
#         db.create_all()
        
#         # Add remaining_chars column to admin_key table if it doesn't exist
#         try:
#             db.session.execute(text("ALTER TABLE admin_key ADD COLUMN remaining_chars INTEGER DEFAULT 0"))
#             db.session.commit()
#         except Exception as e:
#             print(f"Column remaining_chars already exists or error: {e}")
        
#         # Add content column to tts_queue table if it doesn't exist
#         try:
#             db.session.execute(text("ALTER TABLE tts_queue ADD COLUMN content TEXT"))
#             db.session.commit()
#         except Exception as e:
#             print(f"Column content already exists or error: {e}")
        
#         # Add connection_id column to tts_queue table if it doesn't exist
#         try:
#             db.session.execute(text("ALTER TABLE tts_queue ADD COLUMN connection_id VARCHAR(100)"))
#             db.session.commit()
#         except Exception as e:
#             print(f"Column connection_id already exists or error: {e}")
        
#         # Add url column to tts_queue table if it doesn't exist
#         try:
#             db.session.execute(text("ALTER TABLE tts_queue ADD COLUMN url VARCHAR(500)"))
#             db.session.commit()
#         except Exception as e:
#             print(f"Column url already exists or error: {e}")

@app.route('/')
def index():
    print("=== ROUTE / CALLED ===",)
    return render_template('index.html')


# ---------- Web pages ----------
@app.route('/login')
def login():
    return render_template('login.html')



@app.route('/manager/key')
def manager_key():
    return render_template('manager/key.html', page_title='Quản lý Key')


@app.route('/manager/tts')
def manager_tts():
    return render_template('manager/tts.html', page_title='Danh sách chờ TTS')


# ---------- AdminKey APIs ----------
@app.route('/api/keys', methods=['GET'])
def list_keys():
    keys = AdminKey.query.order_by(AdminKey.id.desc()).all()
    return jsonify([
        {
            'id': k.id,
            'key': k.key,
            'remaining_chars': k.remaining_chars,
            'createdAt': k.created_at.isoformat(),
            'updatedAt': k.updated_at.isoformat() if k.updated_at else None,
        } for k in keys
    ])


@app.route('/api/verifyKey', methods=['POST', 'GET'])
def verify_key():
    """Verify if a key exists and return key information"""
    try:
        # Handle both POST (JSON body) and GET (query parameter) requests
        if request.method == 'POST':
            data = request.get_json(force=True)
            key_value = data.get('key')
        else:  # GET request
            key_value = request.args.get('key')
        
        if not key_value:
            return jsonify({'error': 'key is required', 'valid': False}), 400
        
        # Find the admin key
        admin_key = AdminKey.query.filter_by(key=key_value).first()
        
        if not admin_key:
            return jsonify({'error': 'Key not found', 'valid': False}), 404
        
        return jsonify({
            'valid': True,
            'id': admin_key.id,
            'key': admin_key.key,
            'remaining_chars': admin_key.remaining_chars,
            'createdAt': admin_key.created_at.isoformat(),
            'updatedAt': admin_key.updated_at.isoformat() if admin_key.updated_at else None,
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'valid': False}), 500


@app.route('/api/keys', methods=['POST'])
def create_key():
    data = request.get_json(force=True)
    key_value = data.get('key')
    remaining_chars = int(data.get('remaining_chars', 0))
    if not key_value:
        return jsonify({'error': 'key is required'}), 400
    key = AdminKey(key=key_value, remaining_chars=remaining_chars)
    db.session.add(key)
    db.session.commit()
    return jsonify({'id': key.id, 'key': key.key, 'remaining_chars': key.remaining_chars, 'createdAt': key.created_at.isoformat(), 'updatedAt': key.updated_at.isoformat()}), 201


@app.route('/api/keys/<int:key_id>', methods=['PUT'])
def update_key(key_id: int):
    key = AdminKey.query.get_or_404(key_id)
    data = request.get_json(force=True)
    new_value = data.get('key')
    if not new_value:
        return jsonify({'error': 'key is required'}), 400
    key.key = new_value
    if 'remaining_chars' in data:
        key.remaining_chars = int(data['remaining_chars'])
    db.session.commit()
    return jsonify({'id': key.id, 'key': key.key, 'remaining_chars': key.remaining_chars, 'createdAt': key.created_at.isoformat(), 'updatedAt': key.updated_at.isoformat()})


@app.route('/api/keys/<int:key_id>', methods=['DELETE'])
def delete_key(key_id: int):
    key = AdminKey.query.get_or_404(key_id)
    db.session.delete(key)
    db.session.commit()
    return jsonify({'ok': True})


# ---------- TTSQueue APIs ----------
@app.route('/api/tts', methods=['GET'])
def list_tts():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get paginated TTS items
        pagination = TTSQueue.query.order_by(TTSQueue.id.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'key': item.admin_key.key if item.admin_key else None,
                'text_char_count': item.text_char_count,
                'status': item.status,
                'content': item.content,
                'connection_id': item.connection_id,
                'url': item.url,
                'createdAt': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
                'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else None
            })
        
        return jsonify({
            'items': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_tts_history():
    """Get paginated TTS history for a specific user key"""
    try:
        key = request.args.get('key')
        page = request.args.get('page', 1, type=int)
        per_page = 5
        
        if not key:
            return jsonify({'error': 'key is required'}), 400
        
        # Find the admin key
        admin_key = AdminKey.query.filter_by(key=key).first()
        if not admin_key:
            return jsonify({'error': 'Key not found'}), 404
        
        # Get paginated TTS items for this key
        pagination = TTSQueue.query.filter_by(key_id=admin_key.id)\
            .order_by(TTSQueue.id.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'key': admin_key.key,
                'text_char_count': item.text_char_count,
                'status': item.status,
                'content': item.content,
                'connection_id': item.connection_id,
                'url': item.url,
                'createdAt': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
                'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else None
            })
        
        return jsonify({
            'items': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_new_tts', methods=['GET'])
def get_new_tts():
    try:
        item = TTSQueue.query.filter_by(status='processing').order_by(TTSQueue.created_at.asc()).first()
        if not item:
            return jsonify({'message': 'No processing TTS items found'}), 404
        
        result = {
            'id': item.id,
            'key': item.admin_key.key if item.admin_key else None,
            'text_char_count': item.text_char_count,
            'status': item.status,
            'content': item.content,
            'connection_id': item.connection_id,
            'url': item.url,
            'createdAt': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
            'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else None
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def create_tts():
    try:
        data = request.get_json()
        key = data.get('key')
        content = data.get('content')
        
        print(f"Received data - key: {key}, content length: {len(content) if content else 0}",)
        
        text_char_count = data.get('text_char_count', 0)
        status = data.get('status', 'pending')
        url = data.get('url', '')
        
        # Find the admin key
        admin_key = AdminKey.query.filter_by(key=key).first()
        if not admin_key:
            return jsonify({'error': 'Key not found'}), 404
        
        new_tts = TTSQueue(
            key_id=admin_key.id,
            text_char_count=text_char_count,
            status=status,
            content=content,
            url=url
        )
        
        db.session.add(new_tts)
        db.session.commit()
        
        return jsonify({
            'id': new_tts.id,
            'key': admin_key.key,
            'text_char_count': new_tts.text_char_count,
            'status': new_tts.status,
            'content': new_tts.content,
            'url': new_tts.url,
            'createdAt': new_tts.created_at.strftime('%Y-%m-%d %H:%M:%S') if new_tts.created_at else None,
            'updatedAt': new_tts.updated_at.strftime('%Y-%m-%d %H:%M:%S') if new_tts.updated_at else None
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts/<int:tts_id>', methods=['PUT'])
def update_tts(tts_id):
    try:
        data = request.get_json()
        tts = TTSQueue.query.get_or_404(tts_id)
        
        if 'key' in data:
            admin_key = AdminKey.query.filter_by(key=data['key']).first()
            if not admin_key:
                return jsonify({'error': 'Key not found'}), 404
            tts.key_id = admin_key.id
        
        if 'text_char_count' in data:
            tts.text_char_count = data['text_char_count']
        if 'status' in data:
            tts.status = data['status']
        if 'content' in data:
            tts.content = data['content']
        if 'url' in data:
            tts.url = data['url']
        
        tts.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': tts.id,
            'key': tts.admin_key.key if tts.admin_key else None,
            'text_char_count': tts.text_char_count,
            'status': tts.status,
            'content': tts.content,
            'url': tts.url,
            'createdAt': tts.created_at.strftime('%Y-%m-%d %H:%M:%S') if tts.created_at else None,
            'updatedAt': tts.updated_at.strftime('%Y-%m-%d %H:%M:%S') if tts.updated_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts/<int:item_id>', methods=['DELETE'])
def delete_tts(item_id: int):
    item = TTSQueue.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/tts/delete-all', methods=['DELETE'])
def delete_all_tts():
    try:
        # Delete all TTS items
        TTSQueue.query.delete()
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Đã xóa tất cả TTS'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emit_socket', methods=['POST'])
def emit_socket_event():
    """HTTP endpoint to trigger socket emissions"""
    try:
        data = request.get_json(force=True)
        target_socket_id = data.get('socket_id')
        event_name = data.get('event_name', 'custom_event')
        event_data = data.get('event_data', {})

        print("event_data", event_data.get('id'))

        # update tts where id == event_data.get('id') set status done, url
        if event_data.get('id') and event_data.get('status') == 'done':
            try:
                tts_item = TTSQueue.query.get(event_data.get('id'))
                if tts_item:
                    tts_item.status = 'done'
                    tts_item.url = event_data.get('url')
                    tts_item.updated_at = datetime.utcnow()
                    db.session.commit()
                    print(f"Updated TTS item {tts_item.id}: status='done', url='{event_data.get('url')}'")
                else:
                    print(f"TTS item with ID {event_data.get('id')} not found")
            except Exception as e:
                print(f"Error updating TTS item: {e}")
        
        if not target_socket_id:
            return jsonify({'ok': False, 'error': 'Missing socket_id'}), 400
        
        print(f"HTTP triggered: Emitting to socket {target_socket_id}: {event_name} with data {event_data}")
        
        # Emit to the target socket
        socketio.emit(event_name, event_data, to=target_socket_id)
        
        return jsonify({'ok': True, 'message': f'Event {event_name} sent to socket {target_socket_id}'})
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ---------- Socket.IO ----------
@socketio.on('connect')
def handle_connect():
    print("=== CLIENT CONNECTED ===",)

@socketio.on('disconnect')
def handle_disconnect():
    print("=== CLIENT DISCONNECTED ===",)

@socketio.on('enqueue_tts')
def handle_enqueue_tts(data):
    print("\n" + "="*50,)
    print("SOCKET.IO EVENT: enqueue_tts",)
    print("="*50,)
    
    try:
        key = data.get('key')
        content = data.get('content')
        
        print(f"Received data - key: {key}, content length: {len(content) if content else 0}",)
        
        if not key or not content:
            emit('enqueue_tts_result', {'ok': False, 'error': 'Missing key or content'}, to=request.sid)
            return
        
        # Find the admin key
        admin_key = AdminKey.query.filter_by(key=key).first()
        if not admin_key:
            emit('enqueue_tts_result', {'ok': False, 'error': 'Invalid key'}, to=request.sid)
            return
        
        # Kiểm tra xem admin key có đủ ký tự không
        if admin_key.remaining_chars < len(content):
            emit('enqueue_tts_result', {'ok': False, 'error': 'Số ký tự còn lại không đủ để sử dụng'}, to=request.sid)
            return
        
        # Create TTS queue item
        print("Creating TTS queue item...",)
        
        item = TTSQueue(
            key_id=admin_key.id,
            text_char_count=len(content),
            status='processing',
            content=content,
            connection_id=request.sid
        )
        
        print(f"TTS item created with ID: {item.id}",)
        
        # Trừ số ký tự từ admin key
        admin_key.remaining_chars -= len(content)
        admin_key.updated_at = datetime.utcnow()
        
        db.session.add(item)
        db.session.commit()
        print("Đã thêm vào hàng đợi TTS", item.id)
        emit('enqueue_tts_result', {
            'ok': True, 
            'id': item.id, 
            "status": 'Đang xử lý'
        }, to=request.sid)
        
        # Start processing - no callback needed
        # process_tts.start_tts()
        
    except Exception as e:
        emit('enqueue_tts_result', {'ok': False, 'error': str(e)}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)