from flask import Flask, request, jsonify, render_template, session
from flask import redirect, url_for
import json
import bcrypt
from dotenv import load_dotenv
import os
import pymysql

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
  cursor.execute("SELECT * FROM appointments_table WHERE patientId = %s", (id, ))
  appointments = cursor.fetchall()
  appointment_list = []
  for appointment in appointments:
      appointment_data = {
          'appointmentId': appointment[0],
          'date': appointment[2],
          'time': appointment[3],
          'hospitalName': appointment[4],
          'department': appointment[5],
          'doctorName': appointment[6],
          'status': appointment[7]
      }
      appointment_list.append(appointment_data)
  patient_data = {
      'pname': pname,
      'appointments': appointment_list
  }
  conn.close()
  return patient_data

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
        "hospitalId": row[0],
        "name": row[1],
        "address": row[2],
        "contactPerson": row[3],
        "numberOfBeds": row[4],
        "medicalStaff": row[5],
        "nonMedicalStaff": row[6],
        "email": row[7]
    }
    attributes = row[9]
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
      attributes = hospital[1]
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
    if check_password(password, existing_doctor[6]):
      session['user_type'] = 'doctor'
      session['doctor_id'] = existing_doctor[0]
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
    password = data["passwor"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE email=%s",(email, ))
    existing_hospital = cursor.fetchone()
    if not existing_hospital:
      return render_template('error.html', message='No such user found')
    if check_password(password, existing_hospital[8]):
      session['user_type'] = 'hospital'
      session['hospital_id'] = existing_hospital[0]
      return redirect(url_for('hospital_dashboard'))
    else:
      return render_template('error.html', message='Invalid credentials')
  else:
    return render_template('hospital_login.html')

######################## DOCTOR DASHBOARD ##############
@app.route("/doctor_dashboard")
def doctor_dashboard():
  if session.get('user_type') == 'doctor':
    doctorId = session.get('doctor_id')
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE doctorId = %s",(doctorId, ))
    doctor = cursor.fetchone()
    doctor_name = doctor['fullName']
    return render_template('doctor_dashboard.html', doctorName=doctor_name)
  else:
    return redirect(url_for('doctor_login'))

@app.route("/doctor_dashboard/appointments")
def doctor_dashboard_appointments():
  if session.get('user_type') == 'doctor':
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments_table")
    appointments = cursor.fetchall()
    aptmts_list = []
    for row in appointments:
      a = {
          "aId": row[0],
          "pID": row[1],
          "date": row[2],
          "time": row[3],
          "status": row[7],
      }
      cursor.execute("SELECT * FROM patients_master_table WHERE patientId = %s",(row[1], ))
      patient = cursor.fetchone()
      a['pName'] = patient[1]
      aptmts_list.append(a)
    return render_template('doctor_dashboard_appointments.html',aptmts=aptmts_list)
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
    cursor.execute("SELECT fullName, dob, email, bloodGroup, address FROM patients_master_table WHERE patientId = %s", (patientId, ))
    patientData = cursor.fetchone()
    return render_template('patient_dashboard.html',patientData=patientData, appointments=appointments)
  else:
    return redirect(url_for('patient_login'))

@app.route("/patient_dashboard/new_appointment",methods=["GET", "POST"])
def patient_dashboard_new_appointment():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    if request.method == "POST":
      data = request.form
      email = data["email"]
      password = data["password"]
    if request.method == "GET":
      conn = db_connection()
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM patients_master_table WHERE patientId=%s",(patientId,))
      patient = cursor.fetchall()
    return render_template('patient_new_appointment.html',patient=patient)
  else:
    return redirect(url_for('patient_login'))

@app.route("/patient_dashboard/appointments")
def patient_dashboard_appointments():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    return render_template('patient_dashboard_appointments.html')
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
@app.route("/hospital_dashboard")
def hospital_dashboard():
  if session.get('user_type') == 'hospital':
    hospitalId = session.get('hospital_id')
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE hospitalId = %s",(hospitalId, ))
    hospital = cursor.fetchone()
    hospital_name = hospital['name']
    return render_template('hospital_dashboard.html',hospitalName=hospital_name)
  return redirect(url_for('hospital_login'))

@app.route("/hospital_dashboard/appointments")
def hospital_dashboard_appointments():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_appointments.html')
  else:
    return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/patients")
def hospital_dashboard_patients():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_patients.html')
  else:
    return redirect(url_for('hospital_login'))


@app.route("/hospital_dashboard/appointment_requests")
def hospital_dashboard_appointment_requests():
  if session.get('user_type') == 'hospital':
    patientId = session.get('hospital_id')
    return render_template('hospital_dashboard_appointment_requests.html')
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


if __name__ == "__main__":
  app.run(debug=True)