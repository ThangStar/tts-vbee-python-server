# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AdminKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False, unique=True)
    remaining_chars = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AdminKey {self.id}>'


class TTSQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey('admin_key.id'), nullable=False)
    text_char_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='pending')
    content = db.Column(db.Text, nullable=True)
    connection_id = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    voice = db.Column(db.String(100), default='hn_female_ngochuyen_full_48k-fhg')
    speech = db.Column(db.Integer, default=1)
    punctuation = db.Column(db.String(100), default='0.45,0.25,0.3,0.6')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    admin_key = db.relationship('AdminKey', backref=db.backref('tts_queues', lazy=True))

    def __repr__(self):
        return f'<TTSQueue {self.id} status={self.status}>'