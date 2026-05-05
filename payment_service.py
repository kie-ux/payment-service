from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import xml.etree.ElementTree as ET
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

db_url = os.environ.get('DATABASE_URL', '')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('mysql://', 'mysql+pymysql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Payment(db.Model):
    __tablename__ = 'payments'
    id         = db.Column(db.Integer, primary_key=True)
    amount     = db.Column(db.Float, nullable=False)
    status     = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_request
def setup():
    db.create_all()

@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        root   = ET.fromstring(request.data)
        amount = float(root.find('Amount').text)

        response = ET.Element('PaymentResponse')

        if amount > 0:
            new_payment = Payment(amount=amount, status='Success')
            db.session.add(new_payment)
            db.session.commit()
            ET.SubElement(response, 'Status').text    = 'Success'
            ET.SubElement(response, 'PaymentID').text = str(new_payment.id)
        else:
            new_payment = Payment(amount=amount, status='Failed')
            db.session.add(new_payment)
            db.session.commit()
            ET.SubElement(response, 'Status').text  = 'Failed'
            ET.SubElement(response, 'Message').text = 'Invalid amount'

        return Response(ET.tostring(response, encoding='unicode'), mimetype='application/xml')
    except Exception as e:
        response = ET.Element('PaymentResponse')
        ET.SubElement(response, 'Status').text  = 'Error'
        ET.SubElement(response, 'Message').text = str(e)
        return Response(ET.tostring(response, encoding='unicode'), mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)