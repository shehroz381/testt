from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = "meditrack.db"

# Helper function to get DB connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Function to create table (run once)
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            datetime TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route('/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        
        # Validate JSON body exists
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        # Extract fields
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        appointment_datetime = data.get('appointment_datetime')
        notes = data.get('notes', '')
        
        # DEBUGGING FIX: Notes length validation
        if len(notes) > 500:
            return jsonify({'error': 'Notes are too long. Max 500 characters allowed.'}), 400
        
        # Validate required fields
        if not patient_id or not doctor_id or not appointment_datetime:
            return jsonify({
                "error": "patient_id, doctor_id, and appointment_datetime are required"
            }), 400
        
        # Validate datetime format (ISO) and future time
        try:
            appointment_dt = datetime.fromisoformat(appointment_datetime)
        except ValueError:
            return jsonify({
                "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            }), 400
        
        if appointment_dt <= datetime.now():
            return jsonify({
                "error": "Appointment datetime must be in the future"
            }), 400
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        status = "confirmed"
        
        cursor.execute("""
            INSERT INTO bookings (patient_id, doctor_id, datetime, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, appointment_datetime, notes, status, created_at))
        
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        
        # Success response
        return jsonify({
            "booking_id": booking_id,
            "status": status
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    create_table()  # Create table when app starts
    app.run(debug=True)