from datetime import datetime
from app import db

class Guest(db.Model):
    __tablename__ = "guests"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    mac = db.Column(db.String(64))
    ip = db.Column(db.String(64))
    ap_mac = db.Column(db.String(64))
    ssid = db.Column(db.String(128))
    authorized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
