from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, Hospital, BloodInventory, BloodRequest
from datetime import datetime, timedelta
from utils import calculate_distance
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'teal-blood-exchange-secret'
app.config['SQLALCHEMY_DATABASE_DATABASE_URI'] = 'sqlite:///exchange.db'
db.init_app(app)

# Helper: Get current hospital from session
def get_current_hospital():
    if 'hospital_id' not in session: return None
    return Hospital.query.get(session['hospital_id'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = generate_password_hash(data['password'])
    new_hosp = Hospital(
        name=data['name'], email=data['email'], password=hashed_pw,
        phone=data['phone'], address=data['address'],
        lat=data['lat'], lon=data['lon']
    )
    db.session.add(new_hosp)
    db.session.commit()
    return jsonify({"message": "Success"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    hosp = Hospital.query.filter_by(email=data['email']).first()
    if hosp and check_password_hash(hosp.password, data['password']):
        session['hospital_id'] = hosp.id
        return jsonify({"message": "Logged in", "hospital": hosp.to_dict()})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/inventory', methods=['GET', 'POST'])
def manage_inventory():
    hosp = get_current_hospital()
    if not hosp: return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'POST':
        data = request.json
        expiry = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
        item = BloodInventory(
            hospital_id=hosp.id, blood_type=data['blood_type'],
            quantity=data['quantity'], expiry_date=expiry
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({"message": "Added"})

    inventory = BloodInventory.query.filter_by(hospital_id=hosp.id).all()
    return jsonify([i.to_dict() for i in inventory])

@app.route('/api/search', methods=['GET'])
def search_blood():
    hosp = get_current_hospital()
    blood_type = request.args.get('type')
    results = BloodInventory.query.filter(
        BloodInventory.blood_type == blood_type,
        BloodInventory.hospital_id != hosp.id,
        BloodInventory.expiry_date > datetime.now()
    ).all()

    output = []
    for item in results:
        dist = calculate_distance(hosp.lat, hosp.lon, item.owner.lat, item.owner.lon)
        d = item.to_dict()
        d['hospital_name'] = item.owner.name
        d['distance'] = round(dist, 2)
        output.append(d)
    
    # Sort by nearest
    output.sort(key=lambda x: x['distance'])
    return jsonify(output)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
