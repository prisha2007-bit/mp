from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    
    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "phone": self.phone}

class BloodInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    blood_type = db.Column(db.String(5))
    quantity = db.Column(db.Integer)
    expiry_date = db.Column(db.DateTime)
    owner = db.relationship('Hospital', backref='inventory')

    def to_dict(self):
        days_left = (self.expiry_date - datetime.now()).days
        return {
            "id": self.id,
            "blood_type": self.blood_type,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date.strftime('%Y-%m-%d'),
            "is_urgent": days_left <= 5
        }
