from flask import Flask, request, jsonify, render_template, session, send_file
from flask import redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import json
import bcrypt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pymysql
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.secret_key = 'mysecretpassword'
load_dotenv()
####################################### Functions
##### Password Hashing
def generate_hash_password(password):
  salt = bcrypt.gensalt()
  hashed_password = bcrypt.hashpw(password.encode(), salt)
  return hashed_password.decode()

def check_password(password, hashed_password):
  try:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
  except ValueError as e:
    print("Error checking password:", e)
    return False
  
# def start_scheduler():
#     if not scheduler.running:
#         scheduler.start()

def calculate_age(dob):
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def update_missed_appointments():
    conn = db_connection()
    cursor = conn.cursor()
    print("Updating missed appointments...")
    # Get the current datetime
    current_datetime = datetime.now()

    # Fetch all appointments that are "upcoming" and have passed the current date and time
    query = """
        SELECT appointmentId, appointmentDate, appointmentTime 
        FROM appointments_table 
        WHERE status = 'upcoming' AND appointmentDate < %s
    """
    cursor.execute(query, (current_datetime,))
    missed_appointments = cursor.fetchall()

    # Loop through and update the status to "missed"
    for appointment in missed_appointments:
        appointmentId = appointment['appointmentId']

        # Update the status of missed appointments
        update_query = """
            UPDATE appointments_table
            SET status = 'missed'
            WHERE appointmentId = %s
        """
        cursor.execute(update_query, (appointmentId,))
        conn.commit()  # Commit the update to the database

    cursor.close()
    conn.close()

# Scheduler setup
# scheduler = BackgroundScheduler()

# # Schedule the task to run every day at midnight
# scheduler.add_job(func=update_missed_appointments, trigger='cron', hour=0, minute=0)

# # Start the scheduler
# scheduler.start()

##### Database Connection
def db_connection():
  conn = None
  timeout = 10
  try:
    conn = pymysql.connect(
    charset=os.getenv('DB_CHARSET'),
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db=os.getenv('DB_NAME'),
    host=os.getenv('DB_HOST'),
    password=os.getenv('DB_PASSWORD'),
    read_timeout=timeout,
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    write_timeout=timeout,
  )
  except pymysql.Error as e:
    print("Error connecting to MySQL:", e)
  return conn

##### appointment data extraction
def get_appointment_data(id):
  conn = db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM patients_master_table WHERE patientId = %s", (id, ))
  patient = cursor.fetchone()
  pname = patient['fullName']
  cursor.execute("SELECT * FROM appointments_table WHERE patientId = %s ORDER BY date DESC", (id, ))
  appointments = cursor.fetchall()
  # get doctor name from doctorId
  for appointment in appointments:
      doctorId = appointment['doctorId']
      cursor.execute("SELECT fullName FROM doctors_master_table WHERE doctorId = %s", (doctorId, ))
      doctor = cursor.fetchone()
      appointment['doctorId'] = doctor
      if appointment['relationId']:
          cursor.execute("SELECT fullName FROM patients_relatives_table WHERE relationId = %s", (appointment['relationId'], ))
          relative = cursor.fetchone()
          appointment['relativeId'] = relative['fullName']
      else:
          appointment['relativeId'] = pname
  appointment_list = []
  for appointment in appointments:
      appointment_data = {
          'appointmentId': appointment['appointmentId'],
          'date': appointment['date'],
          'time': appointment['time'],
          'hospitalName': appointment['hospitalName'],
          'department': appointment['department'],
          'doctorName': appointment['doctorId'],
          'tokenNumber': appointment['tokenNumber'],
          'patientName': appointment['relativeId'],
          'status': appointment['status']
      }
      appointment_list.append(appointment_data)
  patient_data = {
      'pname': pname,
      'appointments': appointment_list
  }
  conn.close()
  return patient_data

@app.route("/get_appointment_details/<int:appointment_id>", methods=["GET"])
def get_appointment_details(appointment_id):
    doctor_id = session.get('doctor_id')  # Get the logged-in doctor ID
    patient_id = session.get('patient_id')  # Get the logged-in patient ID
    # Ensure user is logged in
    if not doctor_id and not patient_id:
        return jsonify({"success": False, "message": "You must be logged in to view appointment details."}), 401

    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Fetch the appointment details
        cursor.execute("SELECT * FROM appointments_table WHERE appointmentId = %s", (appointment_id,))
        appointment = cursor.fetchone()

        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found."}), 404

        # Fetch patient or relative details based on relationId or patientId
        fullName, dob, phone, bloodGroup = None, None, None, None
        if appointment['relationId']:
            cursor.execute("SELECT fullName, dob, bloodGroup FROM patients_relatives_table WHERE relationId = %s", (appointment['relationId'],))
            patient_data = cursor.fetchone()
            if patient_data:
                fullName, dob, bloodGroup = patient_data['fullName'], patient_data['dob'], patient_data['bloodGroup']
        else:
            cursor.execute("SELECT fullName, dob, phone, bloodGroup FROM patients_master_table WHERE patientId = %s", (appointment['patientId'],))
            patient_data = cursor.fetchone()
            if patient_data:
                fullName, dob, phone, bloodGroup = patient_data['fullName'], patient_data['dob'], patient_data['phone'], patient_data['bloodGroup']

        # Fetch diagnosis details if available
        cursor.execute("SELECT * FROM patients_diagnosis_table WHERE appointmentID = %s", (appointment_id,))
        diagnosis = cursor.fetchone()

        # Fetch the doctor's name
        cursor.execute("SELECT fullName FROM doctors_master_table WHERE doctorId = %s", (appointment['doctorId'],))
        doctor = cursor.fetchone()

        # Prepare the diagnosis data
        diagnosis_data = {
            "diagnosis": diagnosis['diagnosis'] if diagnosis else None,
            "recommendations": diagnosis['recommendations'] if diagnosis else None,
            "medicines": diagnosis['medicines'] if diagnosis else None,
            "time": diagnosis['time'] if diagnosis else "Not Visited Yet"
        }

        # Return JSON response without authentication checks
        return jsonify({
            "success": True,
            "appointment": {
                "appointmentId": appointment['appointmentId'],
                "date": appointment['date'],
                "hospital": appointment['hospitalName'],
                "department": appointment['department'],
                "doctor": doctor['fullName'] if doctor else None,
                "tokenNumber": appointment['tokenNumber'],
                "patient": {
                    "fullName": fullName,
                    "dob": dob,
                    "bloodGroup": bloodGroup,
                    "phone": phone
                },
                "diagnosis": diagnosis_data
            }
        })

    except Exception as e:
        print(f"Error fetching appointment details: {e}")
        return jsonify({"success": False, "message": "Error fetching appointment details."}), 500


@app.route("/update_diagnosis/<int:appointment_id>", methods=["POST"])
def update_diagnosis(appointment_id):
    doctor_id = session.get('doctor_id')  # Get the logged-in doctor ID

    if not doctor_id:
        return jsonify({"success": False, "message": "You must be logged in as a doctor to update diagnosis."}), 401

    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Fetch the appointment details to ensure the doctor is associated with this appointment
        cursor.execute("""
            SELECT * FROM appointments_table WHERE appointmentId = %s
        """, (appointment_id,))
        appointment = cursor.fetchone()

        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found."}), 404

        if appointment['doctorId'] != doctor_id:
            return jsonify({"success": False, "message": "You do not have permission to update this appointment."}), 403

        # Get the data from the request
        data = request.get_json()
        time = datetime.now().time()
        diagnosis = data.get('diagnosis')
        recommendations = data.get('recommendations')
        medicines = data.get('medicines')

        # Check if diagnosis already exists for the appointment
        cursor.execute("""
            SELECT * FROM patients_diagnosis_table WHERE appointmentID = %s
        """, (appointment_id,))
        existing_diagnosis = cursor.fetchone()

        if existing_diagnosis:
            # Update the existing diagnosis
            cursor.execute("""
                UPDATE patients_diagnosis_table
                SET diagnosis = %s, recommendations = %s, medicines = %s, time=%s
                WHERE appointmentID = %s
            """, (diagnosis, recommendations, medicines, appointment_id, time))
        else:
            # Insert a new diagnosis record
            cursor.execute("""
                INSERT INTO patients_diagnosis_table (appointmentID, patientID, date, time, diagnosis, recommendations, medicines)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (appointment_id, appointment['patientId'], appointment['date'], time, diagnosis, recommendations, medicines))

        conn.commit()
        return jsonify({"success": True, "message": "Diagnosis updated successfully."})

    except Exception as e:
        print(f"Error updating diagnosis: {e}")
        return jsonify({"success": False, "message": "Error updating diagnosis."}), 500

@app.route("/complete_appointment/<int:appointment_id>", methods=["POST"])
def complete_appointment(appointment_id):
  doctor_id = session.get('doctor_id')
  if not doctor_id:
    return jsonify({"success": False, "message": "You must be logged in as a doctor to complete appointments."}), 401
  try:
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments_table WHERE appointmentId = %s", (appointment_id,))
    appointment = cursor.fetchone()
    if not appointment:
      return jsonify({"success": False, "message": "Appointment not found."}), 404
    if appointment['doctorId'] != doctor_id:
      return jsonify({"success": False, "message": "You do not have permission to complete this appointment."}), 403
    try:
      cursor.execute("UPDATE appointments_table SET status = 'completed' WHERE appointmentId = %s", (appointment_id,))
      conn.commit()
      return jsonify({"success": True, "message": "Appointment completed successfully."})
    except:
      return jsonify({"success": False, "message": "Error completing appointment."}), 500
  except Exception as e:
    return jsonify({"success": False, "message": "Error completing appointment."}), 500


def public_appointment_details(appointment_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Fetch the appointment details
        cursor.execute("SELECT * FROM appointments_table WHERE appointmentId = %s", (appointment_id,))
        appointment = cursor.fetchone()

        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found."}), 404

        # Fetch patient or relative details based on relationId or patientId
        fullName, dob, phone, bloodGroup = None, None, None, None
        if appointment['relationId']:
            cursor.execute("SELECT fullName, dob, bloodGroup FROM patients_relatives_table WHERE relationId = %s", (appointment['relationId'],))
            patient_data = cursor.fetchone()
            if patient_data:
                fullName, dob, bloodGroup = patient_data['fullName'], patient_data['dob'], patient_data['bloodGroup']
        else:
            cursor.execute("SELECT fullName, dob, phone, bloodGroup FROM patients_master_table WHERE patientId = %s", (appointment['patientId'],))
            patient_data = cursor.fetchone()
            if patient_data:
                fullName, dob, phone, bloodGroup = patient_data['fullName'], patient_data['dob'], patient_data['phone'], patient_data['bloodGroup']

        # Fetch diagnosis details if available
        cursor.execute("SELECT * FROM patients_diagnosis_table WHERE appointmentID = %s", (appointment_id,))
        diagnosis = cursor.fetchone()

        # Fetch the doctor's name
        cursor.execute("SELECT fullName FROM doctors_master_table WHERE doctorId = %s", (appointment['doctorId'],))
        doctor = cursor.fetchone()

        # Prepare the diagnosis data
        diagnosis_data = {
            "diagnosis": diagnosis['diagnosis'] if diagnosis else None,
            "recommendations": diagnosis['recommendations'] if diagnosis else None,
            "medicines": diagnosis['medicines'] if diagnosis else None,
            "time": diagnosis['time'] if diagnosis else "Not Visited Yet"
        }

        # Return JSON response without authentication checks
        return jsonify({
            "success": True,
            "appointment": {
                "appointmentId": appointment['appointmentId'],
                "date": appointment['date'],
                "hospital": appointment['hospitalName'],
                "department": appointment['department'],
                "doctor": doctor['fullName'] if doctor else None,
                "tokenNumber": appointment['tokenNumber'],
                "patient": {
                    "fullName": fullName,
                    "dob": dob,
                    "bloodGroup": bloodGroup,
                    "phone": phone
                },
                "diagnosis": diagnosis_data
            }
        })

    except Exception as e:
        print(f"Error fetching appointment details: {e}")
        return jsonify({"success": False, "message": "Error fetching appointment details."}), 500


@app.route("/download_report/<int:appointment_id>", methods=["GET"])
def download_report(appointment_id):
    doctor_id = session.get('doctor_id')  
    patient_id = session.get('patient_id')

    if not doctor_id and not patient_id:
        return jsonify({"success": False, "message": "You must be logged in to download the report."}), 401

    with app.test_request_context():
        response = public_appointment_details(appointment_id)

    if response.status_code != 200:
        return jsonify({"success": False, "message": "Failed to fetch appointment data."}), response.status_code

    appointment_data = response.get_json()

    # Create a PDF in-memory buffer
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Setting margins
    x_margin = 1 * inch
    y_position = height - 1 * inch

    # Report Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_margin, y_position, f"Hospital: {appointment_data['appointment']['hospital']} Appointment")
    y_position -= 0.5 * inch

    # Appointment Information
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y_position, "Appointment Information")
    c.setFont("Helvetica", 10)
    y_position -= 0.3 * inch
    c.drawString(x_margin, y_position, f"Appointment ID: {appointment_data['appointment']['appointmentId']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Date: {appointment_data['appointment']['date']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Hospital: {appointment_data['appointment']['hospital']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Department: {appointment_data['appointment']['department']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Doctor: {appointment_data['appointment']['doctor']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Token Number: {appointment_data['appointment']['tokenNumber']}")

    # Patient Information
    y_position -= 0.4 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y_position, "Patient Information")
    c.setFont("Helvetica", 10)
    y_position -= 0.3 * inch
    patient = appointment_data['appointment']['patient']
    c.drawString(x_margin, y_position, f"Name: {patient['fullName']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Date of Birth: {patient['dob']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Blood Group: {patient['bloodGroup']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Phone: {patient['phone']}")

    # Diagnosis Information
    y_position -= 0.4 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y_position, "Diagnosis Information")
    c.setFont("Helvetica", 10)
    y_position -= 0.3 * inch
    diagnosis = appointment_data['appointment']['diagnosis']
    c.drawString(x_margin, y_position, f"Diagnosis: {diagnosis['diagnosis']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Recommendations: {diagnosis['recommendations']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Medicines: {diagnosis['medicines']}")
    y_position -= 0.2 * inch
    c.drawString(x_margin, y_position, f"Visit Time: {diagnosis['time']}")
    y_position -= 0.4 * inch
    c.drawString(x_margin, y_position, f"Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Finalize and Save PDF
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="appointment_report.pdf", mimetype='application/pdf')
####################################### Routes
##### index 
@app.route("/")
def index():
  return render_template('index.html')

@app.route("/register")
def registerTableRender():
  return render_template('RegisterTable.html')

@app.route("/hospitals")
def hospitals():
  conn = db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM hospitals_master_table")
  hospitals = cursor.fetchall()
  hospitals_list = []
  for row in hospitals:
    hospital = {
      "hospitalId": row['hospitalId'],
      "name": row['name'],
      "address": row['address'],
      "contactPerson": row['contactPerson'],
      "numberOfBeds": row['numberOfBeds'],
      "medicalStaff": row['medicalStaff'],
      "nonMedicalStaff": row['nonMedicalStaff'],
      "email": row['email'],
    }
    attributes = row['attributes']
    if attributes is not None:
      attributes_dict = json.loads(attributes)
      hospital['weekdays'] = attributes_dict.get('weekdays', [])
      hospital['departments'] = attributes_dict.get('departments', [])
    else:
      hospital['weekdays'] = []
      hospital['departments'] = []
    hospitals_list.append(hospital)
  return render_template('HospitalTable.html', hospitals=hospitals_list)

@app.route("/patient_register", methods=["GET", "POST"])
def patient_register():
  if request.method == "POST":
    data = request.form
    fullName = data["fullName"]
    dob = data["dob"]
    bloodGroup = data["bloodGroup"]
    email = data["email"]
    phone = data["phone"]
    relativeName = data["relativeName"]
    relativeNumber = data["relativeNumber"]
    address = data["address"]
    password = data["password"]
    hashed_password = generate_hash_password(password)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients_master_table WHERE email=%s OR phone=%s", (email, phone))
    existing_patient = cursor.fetchone()
    if existing_patient:
      return render_template('error.html', message="Patient already exists")
    cursor.execute("""INSERT INTO patients_master_table (fullName, dob, bloodGroup, email, phone,relativeName, relativeNumber, address, passwordHash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",(fullName, dob, bloodGroup, email, phone, relativeName, relativeNumber,address, hashed_password))
    conn.commit()
    conn.close()
    return redirect('/patient_login')
  else:
    return render_template('patient_register.html')


@app.route("/doctor_register", methods=["GET", "POST"])
def doctor_register():
  if request.method == "POST":
    data = request.form
    docName = data["fullName"]
    docNo = data["registrationNumber"]
    docEmail = data["email"]
    docHospital = data["hospital"]
    docDept = data["department"]
    docPass = data["password"]
    hashed_password = generate_hash_password(docPass)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE email=%s OR regNo=%s",(docEmail, docNo))
    existing_doctor = cursor.fetchone()
    if existing_doctor:
      return render_template('error.html',message="Doctor already exists")
    cursor.execute("""INSERT INTO doctors_master_table (fullName,regNo,email,hospital,department,passwordHash) VALUES (%s, %s, %s, %s, %s, %s)""",(docName, docNo, docEmail, docHospital, docDept, hashed_password))
    conn.commit()
    conn.close()
    return redirect('/doctor_login')
  else:
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, attributes FROM hospitals_master_table")
    hospitals = cursor.fetchall()
    hospital_list = []
    for hospital in hospitals:
      hospital_data = {"name": hospital['name']}
      attributes = hospital.get('attributes')

      if attributes is not None:
        attributes_dict = json.loads(attributes)
        hospital_data["departments"] = attributes_dict.get("departments", [])
      else:
        hospital_data["departments"] = []
      hospital_list.append(hospital_data)
    return render_template('doctor_register.html', hospitals=hospital_list)

@app.route("/hospital_register", methods=["GET", "POST"])
def hosital_register():
  if request.method == "POST":
    data = request.form
    hosName = data["name"]
    hosAddress = data["address"]
    hosContactPerson = data["contactPerson"]
    hosNumberOfBeds = data["numberOfBeds"]
    hosMedicalStaff = data["medicalStaff"]
    hosNonMedicalStaff = data["nonMedicalStaff"]
    hosEmail = data["email"]
    hosPass = data["password"]
    hashed_password = generate_hash_password(hosPass)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE email=%s OR name=%s",(hosEmail, hosName))
    existing_hospital = cursor.fetchone()
    if existing_hospital:
      return render_template('error.html',message="Hospital already exists")
    cursor.execute('''INSERT INTO hospitals_master_table (name, address, contactPerson, numberOfBeds, medicalStaff,nonMedicalStaff,email, passwordHash) values(%s,%s,%s,%s,%s,%s,%s,%s)''',(hosName, hosAddress, hosContactPerson, hosNumberOfBeds,hosMedicalStaff, hosNonMedicalStaff, hosEmail, hashed_password))
    conn.commit()
    conn.close()
    return redirect('/hospital_login')
  else:
    return render_template('hospital_register.html')

@app.route("/patient_login", methods=["GET", "POST"])
def patient_login():
  if request.method == "POST":
    data = request.form
    phoneno = data["phone"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients_master_table WHERE phone=%s",(phoneno, ))
    patient = cursor.fetchone()
    if not patient:
      return render_template('error.html', message='No such user found')
    if check_password(password, patient['passwordHash']):
      session['user_type'] = 'patient'
      session['patient_id'] = patient['patientId']
      return redirect('/patient_dashboard')
    else:
      return render_template('error.html', message="Invalid credentials")
  else:
    return render_template('patient_login.html')

@app.route("/doctor_login", methods=["GET", "POST"])
def doctor_login():
  if request.method == "POST":
    data = request.form
    regNo = data["registrationNumber"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE regNo=%s",(regNo, ))
    existing_doctor = cursor.fetchone()
    if not existing_doctor:
      return render_template('error.html', message='No such user found')
    if check_password(password, existing_doctor['passwordHash']):
      session['user_type'] = 'doctor'
      session['doctor_id'] = existing_doctor['doctorId']
      return redirect(url_for('doctor_dashboard'))
    else:
      return render_template('error.html', message='Invalid credentials')
  else:
    return render_template('doctor_login.html')

@app.route("/hospital_login", methods=["GET", "POST"])
def hospital_login():
  if request.method == "POST":
    data = request.form
    email = data["email"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE email=%s",(email, ))
    existing_hospital = cursor.fetchone()
    if not existing_hospital:
      return render_template('error.html', message='No such user found')
    if check_password(password, existing_hospital['passwordHash']):
      session['user_type'] = 'hospital'
      session['hospital_id'] = existing_hospital['hospitalId']
      return redirect(url_for('hospital_dashboard'))
    else:
      return render_template('error.html', message='Invalid credentials')
  else:
    return render_template('hospital_login.html')

######################## DOCTOR DASHBOARD ##############
@app.route('/get_doctors', methods=['GET'])
def get_doctors():
    doctor_id = session.get('doctor_id')
    patient_id = session.get('patient_id')
    hospital_id = session.get('hospital_id')

    if not (doctor_id or patient_id or hospital_id):
        return redirect(url_for('login'))

    hospital_name = request.args.get('hospital')
    department_name = request.args.get('department')

    conn = db_connection()
    cursor = conn.cursor()

    # Query to fetch doctors matching the hospital and department
    cursor.execute("""
        SELECT doctorId, fullName FROM doctors_master_table
        WHERE hospital = %s AND department = %s
    """, (hospital_name, department_name))

    doctors = cursor.fetchall()
    conn.close()

    # Ensure the response is formatted as a list of dictionaries
    return jsonify({'doctors': [{'id': doctor['doctorId'], 'name': doctor['fullName']} for doctor in doctors]})

@app.route("/doctor_dashboard")
def doctor_dashboard():
  if session.get('user_type') == 'doctor':
    doctorId = session.get('doctor_id')
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE doctorId = %s",(doctorId, ))
    doctor = cursor.fetchone()
    doctor_name = doctor['fullName']
    cursor.execute("SELECT * FROM appointments_table WHERE doctorId = %s",(doctorId, ))
    appointments = cursor.fetchall()
    return render_template('doctor_dashboard.html', doctor=doctor, appointments=appointments)
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/profile", methods=["GET", "POST"])
def doctor_dashboard_profile():
    doctorId = session.get('doctor_id')
    
    if not doctorId:
        return redirect(url_for('doctor_login'))  # Replace 'login' with the actual name of your login route
    
    conn = db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        data = request.get_json()

        email = data.get("email")
        phone = data.get("phone")
        hospital = data.get("hospital")
        department = data.get("department")
        password = data.get("password")

        cursor.execute("SELECT passwordHash FROM doctors_master_table WHERE doctorId = %s", (doctorId,))
        password_hash = cursor.fetchone()['passwordHash']
        
        if email and phone and hospital and department and password:
            # Check password validity
            if check_password(password, password_hash):
                # Validate phone number (should be a string of 10 digits)
                if isinstance(phone, str) and phone.isdigit() and len(phone) == 10:
                    try:
                        # Update doctor data in the database
                        cursor.execute("""
                            UPDATE doctors_master_table 
                            SET email = %s, phone = %s, hospital = %s, department = %s
                            WHERE doctorId = %s
                        """, (email, phone, hospital, department, doctorId))  # Correct variable 'doctorId'
                        conn.commit()
                        return jsonify({'success': True, 'message': 'Profile updated successfully'})
                    except Exception as e:
                      return jsonify({'success': False, 'message': 'An error occurred while updating the profile'}), 500
                else:
                  return jsonify({'success': False, 'message': 'Phone number must be 10 digits and numeric'}), 400
            else:
              return jsonify({'success': False, 'message': 'Invalid password'}), 400
        else:
          return jsonify({'success': False, 'message': 'All fields are required'}), 400

    else:
        cursor.execute("SELECT * FROM doctors_master_table WHERE doctorId = %s", (doctorId,))
        doctor = cursor.fetchone()
        
        # Fetching details from the doctor's record
        email = doctor.get('email')
        fullName = doctor.get('fullName')
        hospital = doctor.get('hospital')
        department = doctor.get('department')
        phone = doctor.get('phone')

        data = {
            "email": email,
            "fullName": fullName,
            "hospital": hospital,
            "phone": phone,
            "department": department
        }
        return render_template('doctor_dashboard_profile.html', doctor=doctor, data=data)


@app.route("/doctor_dashboard/appointments")
def doctor_dashboard_appointments():
  if session.get('user_type') == 'doctor':
    doctorId = session.get('doctor_id')
    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT fullName FROM doctors_master_table WHERE doctorId = %s",(doctorId, ))
    doctor = cursor.fetchone()

    cursor.execute("SELECT * FROM appointments_table WHERE doctorId = %s AND date=%s",(doctorId, datetime.now().date()))
    appointments_today = cursor.fetchall()

    cursor.execute("SELECT * FROM appointments_table WHERE doctorId = %s",(doctorId, ))
    appointments = cursor.fetchall()

    for appointment in appointments:
      relationId = appointment['relationId']
      patientId = appointment['patientId']  

      fullName, dob, phone = None, None, None
      if relationId:  # If relation_id exists, fetch from patients_relatives_table
          query = """
              SELECT fullName, dob 
              FROM patients_relatives_table
              WHERE relationId = %s 
            """
          cursor.execute(query, (relationId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
          
          query = """
              SELECT phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          phone_data = cursor.fetchone()
          if phone_data:
              phone = phone_data['phone']
          else:
              phone = None

      else:  # If no relation_id, fetch from patient_master_table using patient_id
          query = """
              SELECT fullName, dob, phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
              phone = patient_data[0]['phone']


        # Fetch the result for the current iteration
      appointment['fullName'] = fullName if fullName else "N/A"
      appointment['age'] = calculate_age(dob) if dob else "N/A"
      appointment['phone'] = phone if phone else "N/A"
      appointment['doctorId'] = doctor['fullName']
      

    for appointment in appointments_today:
      relationId = appointment['relationId']
      patientId = appointment['patientId']  

      fullName, dob, phone = None, None, None
      if relationId:  # If relation_id exists, fetch from patients_relatives_table
          query = """
              SELECT fullName, dob 
              FROM patients_relatives_table
              WHERE relationId = %s 
            """
          cursor.execute(query, (relationId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
          
          query = """
              SELECT phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          phone_data = cursor.fetchone()
          if phone_data:
              phone = phone_data['phone']
          else:
              phone = None

      else:  # If no relation_id, fetch from patient_master_table using patient_id
          query = """
              SELECT fullName, dob, phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
              phone = patient_data[0]['phone']

        # Fetch the result for the current iteration
      appointment['fullName'] = fullName if fullName else "N/A"
      appointment['age'] = calculate_age(dob) if dob else "N/A"
      appointment['phone'] = phone if phone else "N/A"
      appointment['doctorId'] = doctor['fullName']
    return render_template('doctor_dashboard_appointments.html', doctor=doctor,appointments=appointments, appointments_today=appointments_today)
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/patients")
def doctor_dashboard_patients():
  if session.get('user_type') == 'doctor':
    return render_template('doctor_dashboard_patients.html')
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/reports")
def doctor_dashboard_reports():
  if session.get('user_type') == 'doctor':
    return render_template('doctor_dashboard_reports.html')
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/prescriptions")
def doctor_dashboard_prescriptions():
  if session.get('user_type') == 'doctor':
    return render_template('doctor_dashboard_prescriptions.html')
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/diagnose")
def doctor_dashboard_diagnose():
  if session.get('user_type') == 'doctor':
    return render_template('doctor_dashboard_diagnose.html')
  else:
    return redirect(url_for('doctor_login'))

######################## PATIENT DASHBOARD ##############
@app.route("/patient_dashboard")
def patient_dashboard():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    appointments = get_appointment_data(patientId)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fullName, dob, email, bloodGroup, address, phone FROM patients_master_table WHERE patientId = %s ", (patientId, ))
    patientData = cursor.fetchone()
    return render_template('patient_dashboard.html',patientData=patientData, appointments=appointments)
  else:
    return redirect(url_for('patient_login'))

@app.route("/patient_dashboard/new_appointment", methods=["GET", "POST"])
def patient_dashboard_new_appointment():
    if session.get('user_type') == 'patient':
        patientId = session.get('patient_id')

        conn = db_connection()
        cursor = conn.cursor()

        if request.method == "POST":
            data = request.form
            selectedDate = data.get('visitDate')  # The user-selected appointment date (string format)
            selectedDate = datetime.strptime(selectedDate, '%Y-%m-%d').date()

            # Get the current date and the date 7 days later
            current_date = datetime.now().date()
            end_date = current_date + timedelta(days=7)

            # Validate if the selected date is within the range (today and 7 days ahead)
            if selectedDate < current_date or selectedDate > end_date:
                flash("Appointments can only be booked between today and the next 7 days.", "error")
                return redirect(url_for('patient_dashboard_new_appointment'))  # Redirect to the same page

            selectedRelativeId = data.get("selectRelative")  # Get selected relative's ID if any

            fullName = data.get('fullName')
            bloodGroup = data.get('bloodGroup')
            dob = data.get('dob')
            hospital = data.get('hospital')
            department = data.get('department')
            doctorId = data.get('doctor')
            
            visitDate = data.get('visitDate')

            visit_date_formatted = visitDate
            cursor.execute("""
                SELECT COALESCE(MAX(tokenNumber), 0) AS lastToken 
                FROM appointments_table 
                WHERE hospitalName=%s AND date=%s
            """, (hospital, visit_date_formatted))

            result = cursor.fetchone()
            if result and result['lastToken']:
                tokenNumber = result['lastToken'] + 1
            else:
              tokenNumber = 1


            if selectedRelativeId and selectedRelativeId != 'self' and selectedRelativeId != 'new':
              relativeId = selectedRelativeId

            elif selectedRelativeId == 'new':
              relationship = data.get('relativeType')
              try:
                cursor.execute("INSERT INTO patients_relatives_table (patientId, relationship, fullName, bloodGroup, dob) VALUES (%s, %s, %s, %s, %s)", (patientId, relationship, fullName, bloodGroup, dob))
                conn.commit()
              except Exception as e:
                print("Error inserting into patients_relatives_table:", e)

              cursor.execute("SELECT * FROM patients_relatives_table WHERE patientId=%s and fullName=%s", (patientId, fullName))
              relative = cursor.fetchone()
              relativeId = relative['relationId']

            else:
                relativeId = None
            
            try:
              cursor.execute(
                """
                INSERT INTO appointments_table 
                (patientId, relationId, date, hospitalName, department, tokenNumber, doctorId) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (patientId, relativeId, visitDate, hospital, department, tokenNumber, doctorId)
              )
              conn.commit()
            except Exception as e:
              print("Error creating appointment:", e)
              flash("An error occurred while creating the appointment. Please try again.", "error")

            return redirect(url_for('patient_dashboard_appointments'))


        if request.method == "GET":
            # Fetch patient details for the logged-in user
            cursor.execute("SELECT fullName, dob, bloodGroup, email, phone FROM patients_master_table WHERE patientId=%s", (patientId,))
            patient = cursor.fetchone()

            # Fetch the logged-in patient's relatives
            cursor.execute("SELECT * FROM patients_relatives_table WHERE patientId=%s", (patientId,))
            relatives = cursor.fetchall()
            relatives_list = []
            for relative in relatives:
                relative_data = {
                    'relationId': relative['relationId'],
                    'relationship': relative['relationship'],
                    'fullName': relative['fullName'],
                    'dob': relative['dob'],
                    'bloodGroup': relative['bloodGroup']
                }
                relatives_list.append(relative_data)
            # Fetch hospital list and department details
            cursor.execute("SELECT name, attributes FROM hospitals_master_table")
            hospitals = cursor.fetchall()
            hospital_list = []
            for hospital in hospitals:
                hospital_data = {"name": hospital['name']}
                attributes = hospital.get('attributes')
                if attributes is not None:
                    attributes_dict = json.loads(attributes)
                    hospital_data["departments"] = attributes_dict.get("departments", [])
                else:
                    hospital_data["departments"] = []
                hospital_list.append(hospital_data)

            return render_template('patient_new_appointment.html', patient=patient, relatives=relatives_list, hospitals=hospital_list)
    else:
        return redirect(url_for('patient_login'))


@app.route('/get_relative_details', methods=['GET'])
def get_relative_details(relative_id):
    if session.get('user_type') != 'patient':
    
      # Fetch relative details from the database
      cur = conn.cursor()
      query = '''
      SELECT fullName, dob, bloodGroup
      FROM patients_relatives_table
      WHERE patientId = %s;
      '''
      cur.execute(query, (relative_id,))
      relative_details = cur.fetchall()

      if relative_details:
          return jsonify({
              'relationId': relative_details['relationId'],
              'fullName': relative_details['fullName'],
              'dob': str(relative_details['dob']),
              'phone': relative_details['phone'],
              'bloodGroup': relative_details['bloodGroup']
          })
      else:
          return jsonify({'error': 'Relative not found'}), 404
    else:
      return redirect(url_for('patient_login'))

@app.route("/patient_dashboard/appointments")
def patient_dashboard_appointments():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    appointments = get_appointment_data(patientId)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fullName, dob, email, bloodGroup, address, phone FROM patients_master_table WHERE patientId = %s", (patientId, ))
    patientData = cursor.fetchone()
    
    return render_template('patient_dashboard_appointments.html', patientData=patientData, appointments=appointments)
  else:
    return redirect(url_for('patient_login'))



@app.route("/patient_dashboard/reports")
def patient_dashboard_reports():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients_diagnosis_table WHERE patientID=%s",(patientId, ))
    diagnose = cursor.fetchall()
    return render_template('patient_dashboard_reports.html',diagnose=diagnose)
  else:
    return redirect(url_for('patient_login'))


@app.route("/patient_dashboard/prescriptions")
def patient_dashboard_prescriptions():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    if patientId:
      conn = db_connection()
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM patients_diagnosis_table WHERE patientID=%s",(patientId, ))
      diagnose = cursor.fetchall()
      print(diagnose)
      return render_template('patient_dashboard_prescriptions.html',diagnose=diagnose)
  else:
    return redirect(url_for('patient_login'))


######################## HOSPITAL DASHBOARD ##############
@app.route('/search_hospitals', methods=['GET'])
def search_hospitals():
    query = request.args.get('query', '')  # Get search query from URL parameters
    conn = db_connection()
    cursor = conn.cursor()
    
    # MySQL query for fetching hospitals whose names match the search query
    cursor.execute("SELECT hospitalId, name FROM hospitals_master_table WHERE name LIKE %s", ('%' + query + '%',))
    
    # Fetch all matching hospitals
    hospitals = cursor.fetchall()
    
    conn.close()
    
    # Return the list of hospitals as JSON
    return jsonify({'hospitals': [{'id': hospital['hospitalId'], 'name': hospital['name']} for hospital in hospitals]})
@app.route('/get_departments', methods=['GET'])
def get_departments():
    # Get hospital_id from the request arguments
    hospital_id = request.args.get('hospital_id')
    
    # Establish database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Execute the query to fetch the attributes column for the specific hospital_id
    cursor.execute("SELECT attributes FROM hospitals_master_table WHERE hospitalId = %s", (hospital_id,))
    attributes = cursor.fetchone()  # Fetch one record, as hospital_id is presumably unique
    
    # Check if the attributes were found
    if attributes:
        # Parse the JSON data from the 'attributes' column
        departments = json.loads(attributes['attributes']).get('departments', [])
    else:
        departments = []  # If no record found, return an empty list
    
    # Close the database connection
    conn.close()
    
    # Return the departments as a JSON response
    return jsonify({'departments': departments})

@app.route("/hospital_dashboard", methods=["GET", "POST"])
def hospital_dashboard():
  if session.get('user_type') == 'hospital':
    conn = db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":

      data = request.form
      hospitalId = session.get('hospital_id')
      hospitalName = data["name"]
      hospitalAddress = data["address"]
      hospitalContactPerson = data["contact"]
      email = data["email"]
      hospitalNumberOfBeds = data["numberOfBeds"]
      hospitalMedicalStaff = data["medicalStaff"]
      hospitalNonMedicalStaff = data["nonMedicalStaff"]
      hospitalEmail = data["email"]
      attributes_json = data["attributes"]
      attributes = json.loads(attributes_json)
      weekdays = attributes.get('weekdays', [])
      departments = attributes.get('departments', [])

      
      cursor.execute("UPDATE hospitals_master_table SET name=%s, address=%s, contactPerson=%s, numberOfBeds=%s, medicalStaff=%s, nonMedicalStaff=%s, email=%s, attributes=%s WHERE hospitalId=%s",(hospitalName, hospitalAddress, hospitalContactPerson, hospitalNumberOfBeds, hospitalMedicalStaff, hospitalNonMedicalStaff, email, json.dumps({"weekdays": weekdays, "departments": departments}), hospitalId))
      conn.commit()
      hospital = cursor.fetchone()
      return redirect(url_for('hospital_dashboard', hospital=hospital))

    hospitalId = session.get('hospital_id')
    
    cursor.execute("SELECT * FROM hospitals_master_table WHERE hospitalId = %s",(hospitalId, ))
    hospital = cursor.fetchone()
    attributes = json.loads(hospital['attributes'])

    return render_template('hospital_dashboard.html',hospital=hospital, attributes=attributes)
  return redirect(url_for('hospital_login'))

@app.route("/hospital_dashboard/appointments")
def hospital_dashboard_appointments():
  if session.get('user_type') == 'hospital':
    hospitalId = session.get('hospital_id')
    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM hospitals_master_table WHERE hospitalId = %s",(hospitalId, ))
    hospital = cursor.fetchone()

    cursor.execute("SELECT * FROM appointments_table WHERE hospitalName = %s AND date=%s",(hospital['name'], datetime.now().date()))
    appointments_today = cursor.fetchall()

    cursor.execute("SELECT * FROM appointments_table WHERE hospitalName = %s",(hospital['name'], ))
    appointments = cursor.fetchall()

    for appointment in appointments:
      relationId = appointment['relationId']
      patientId = appointment['patientId']  
      cursor.execute('select fullName from doctors_master_table where doctorId=%s', (appointment['doctorId'], ))
      doctorName = cursor.fetchone()
      appointment['doctorId'] = doctorName
      fullName, dob, phone = None, None, None
      if relationId:  # If relation_id exists, fetch from patients_relatives_table
          query = """
              SELECT fullName, dob 
              FROM patients_relatives_table
              WHERE relationId = %s 
            """
          cursor.execute(query, (relationId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
          
          query = """
              SELECT phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          phone_data = cursor.fetchone()
          if phone_data:
              phonea = phone_data['phone']

      else:  # If no relation_id, fetch from patient_master_table using patient_id
          query = """
              SELECT fullName, dob, phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
              phone = patient_data[0]['phone']


        # Fetch the result for the current iteration
      appointment['fullName'] = fullName if fullName else "N/A"
      appointment['age'] = calculate_age(dob) if dob else "N/A"
      appointment['phone'] = phonea if phonea else "N/A"
      

    for appointment in appointments_today:
      relationId = appointment['relationId']
      patientId = appointment['patientId']  

      fullName, dob, phone = None, None, None
      if relationId:  # If relation_id exists, fetch from patients_relatives_table
          query = """
              SELECT fullName, dob 
              FROM patients_relatives_table
              WHERE relationId = %s 
            """
          cursor.execute(query, (relationId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
          
          query = """
              SELECT phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          phone_data = cursor.fetchone()
          if phone_data:
              phonea = phone_data['phone']

      else:  # If no relation_id, fetch from patient_master_table using patient_id
          query = """
              SELECT fullName, dob, phone
              FROM patients_master_table
              WHERE patientId = %s
            """
          cursor.execute(query, (patientId,))
          patient_data = cursor.fetchall()

          if patient_data:
              fullName = patient_data[0]['fullName']
              dob = patient_data[0]['dob']
              phone = patient_data[0]['phone']

        # Fetch the result for the current iteration
      appointment['fullName'] = fullName if fullName else "N/A"
      appointment['age'] = calculate_age(dob) if dob else "N/A"
      appointment['phone'] = phonea if phonea else "N/A"
    return render_template('hospital_dashboard_appointments.html', hospital=hospital, appointments=appointments, appointments_today=appointments_today)
  else:
    return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/patients")
def hospital_dashboard_patients():
    if session.get('user_type') == 'hospital':
        hospitalId = session.get('hospital_id')
        conn = db_connection()
        cursor = conn.cursor()

        # Fetch the hospital name from the database
        cursor.execute("SELECT name FROM hospitals_master_table WHERE hospitalId = %s", (hospitalId,))
        hospital = cursor.fetchone()

        # Fetch all appointments linked with the hospital name
        cursor.execute("SELECT * FROM appointments_table WHERE hospitalName = %s", (hospital['name'],))
        appointments = cursor.fetchall()

        # Initialize a dictionary to store patient data that has already been fetched
        fetched_patients = {}
        unique_patients = {}  # Dictionary to track unique patients
        duplicates = []  # List to store duplicates

        # Loop through appointments to fetch patient details
        for appointment in appointments:
            relationId = appointment['relationId']
            patientId = appointment['patientId']

            # Check if the patient has already been fetched
            if patientId not in fetched_patients:
                fullName, dob, phone, address = None, None, None, None

                if relationId:  # If relation_id exists, fetch from patients_relatives_table
                    query = """
                        SELECT fullName, dob
                        FROM patients_relatives_table
                        WHERE relationId = %s
                    """
                    cursor.execute(query, (relationId,))
                    patient_data = cursor.fetchone()

                    if patient_data:
                        fullName = patient_data['fullName']
                        dob = patient_data['dob']

                    # Fetch phone and address from patient_master_table
                    query = """
                        SELECT phone, address
                        FROM patients_master_table
                        WHERE patientId = %s
                    """
                    cursor.execute(query, (patientId,))
                    additional_data = cursor.fetchone()
                    if additional_data:
                        phone = additional_data['phone']
                        address = additional_data['address']

                else:  # If no relation_id, fetch directly from patient_master_table
                    query = """
                        SELECT fullName, dob, phone, address
                        FROM patient_master_table
                        WHERE patientId = %s
                    """
                    cursor.execute(query, (patientId,))
                    patient_data = cursor.fetchone()

                    if patient_data:
                        fullName = patient_data['fullName']
                        dob = patient_data['dob']
                        phone = patient_data['phone']
                        address = patient_data['address']

                # Calculate age from dob
                age = calculate_age(dob) if dob else "N/A"

                # Create a unique key for the patient based on fullName, phone, and dob
                key = (fullName, phone, dob)

                # Check for duplicates
                if key in unique_patients:
                    duplicates.append({
                        'fullName': fullName,
                        'age': age,
                        'dob' : dob,
                        'phone': phone,
                        'address': address,
                    })
                else:
                    unique_patients[key] = {
                        'patientId': patientId,
                        'fullName': fullName if fullName else "N/A",
                        'age': age,
                        'dob' : dob,
                        'phone': phone if phone else "N/A",
                        'address': address if address else "N/A"
                    }
                    fetched_patients[patientId] = unique_patients[key]  # Store the unique patient

            # Add the patient details from the dictionary to the appointment
            appointment['fullName'] = unique_patients[key]['fullName']
            appointment['age'] = unique_patients[key]['age']
            appointment['dob'] = unique_patients[key]['dob']
            appointment['phone'] = unique_patients[key]['phone']
            appointment['address'] = unique_patients[key]['address']
            print(appointment)
        return render_template('hospital_dashboard_patients.html', hospital=hospital, patients=appointments, duplicates=duplicates, unique_patients=unique_patients)
    else:
        return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/reports_history")
def hospital_dashboard_reports_history():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_reports_history.html')
  else:
    return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/reports_requests")
def hospital_dashboard_reports_requests():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_reports_requests.html')
  else:
    return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/prescriptions")
def hospital_dashboard_prescriptions():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_reports_prescriptions.html')
  else:
    return redirect(url_for('hospital_login'))


######################## LOGOUT SESSION ##############
@app.route('/logout')
def logout():
  session.pop('user_type', None)
  return redirect(url_for('index'))


# @app.teardown_appcontext
# def shutdown_scheduler(exception=None):
#     scheduler.shutdown()

if __name__ == "__main__":
  app.run(debug=True,host='0.0.0.0')
