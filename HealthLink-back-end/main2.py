from flask import Flask, request, jsonify, render_template
from flask import redirect, url_for, session
import json
import bcrypt
import sqlite3

app = Flask(__name__)
app.secret_key = 'mysecretpassword'


# Password Hash
def generate_hash_password(password):
  salt = bcrypt.gensalt()
  hashed_password = bcrypt.hashpw(password.encode(), salt)
  return hashed_password.decode()


def check_password(password, hashed_password):
  try:
    print("Hashed password:", hashed_password)
    print("Input password:", password)
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
  except ValueError as e:
    # Handle invalid salt or other errors
    print("Error checking password:", e)
    return False


# Database connection
def db_connection():
  conn = None
  try:
    conn = sqlite3.connect("HealthLinkDB.sqlite")
  except sqlite3.Error as e:
    print(e)
  return conn


@app.route("/")
def index():
  return render_template('index.html')


@app.route("/patient_register", methods=["GET", "POST"])
def patient_register():
  if request.method == "POST":
    print("POST /patient_register request received")
    data = request.form
    print(data["fullName"])
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
    print("PASS: ", hashed_password)
    conn = db_connection()
    cursor = conn.cursor()
    print("working")
    cursor.execute(
        "SELECT * FROM patients_master_table WHERE email=? OR phone=?",
        (email, phone))
    existing_patient = cursor.fetchone()
    if existing_patient:
      return render_template('error.html', message="Patient already exists")

    cursor.execute(
        """INSERT INTO patients_master_table (fullName, dob, bloodGroup, email, phone,
                        relativeName, relativeNumber, address, passwordHash) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fullName, dob, bloodGroup, email, phone, relativeName, relativeNumber,
         address, hashed_password))
    conn.commit()
    conn.close()
    print("success patient register")
    return redirect('/patient_login')
  else:
    return render_template('patient_register.html')


@app.route("/doctor_register", methods=["GET", "POST"])
def doctor_register():
  if request.method == "POST":
    print("POST /doctor_register request received")
    data = request.form
    print(data["fullName"])
    docName = data["fullName"]
    docNo = data["registrationNumber"]
    docEmail = data["email"]
    docHospital = data["hospital"]
    docDept = data["department"]
    docPass = data["password"]
    hashed_password = generate_hash_password(docPass)
    print("PASS: ", hashed_password)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM doctors_master_table WHERE email=? OR regNo=?",
        (docEmail, docNo))
    existing_patient = cursor.fetchone()
    if existing_patient:
      return render_template('error.html')

    cursor.execute(
        """INSERT INTO doctors_master_table 
        (fullName,regNo,email,hospital,department,passwordHash)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (docName, docNo, docEmail, docHospital, docDept, hashed_password))
    conn.commit()
    conn.close()
    print("success doctor register")
    return redirect('/doctor_login')
  else:
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, attributes FROM hospitals_master_table")
    hospitals = cursor.fetchall()
    hospital_list = []
    for hospital in hospitals:
      hospital_data = {"name": hospital[0]}
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
    print("POST /hospital_register request received")
    data = request.form
    print(data["name"])
    hosName = data["name"]
    hosAddress = data["address"]
    hosContactPerson = data["contactPerson"]
    hosNumberOfBeds = data["numberOfBeds"]
    hosMedicalStaff = data["medicalStaff"]
    hosNonMedicalStaff = data["nonMedicalStaff"]
    hosEmail = data["email"]
    hosPass = data["password"]
    hashed_password = generate_hash_password(hosPass)
    print("PASS: ", hashed_password)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM hospitals_master_table WHERE email=? OR name=?",
        (hosEmail, hosName))
    existing_hospital = cursor.fetchone()
    if existing_hospital:
      return render_template('error.html')
    cursor.execute(
        '''INSERT INTO hospitals_master_table (name, address, contactPerson, numberOfBeds, medicalStaff,nonMedicalStaff,email, passwordHash)
      values(?,?,?,?,?,?,?,?)''',
        (hosName, hosAddress, hosContactPerson, hosNumberOfBeds,
         hosMedicalStaff, hosNonMedicalStaff, hosEmail, hashed_password))
    conn.commit()
    conn.close()
    print("success hospital register")
    return redirect('/hospital_login')
  return render_template('hospital_register.html')


@app.route("/patient_login", methods=["GET", "POST"])
def patient_login():
  if request.method == "POST":
    print("POST /patient_login request received")
    data = request.form
    print(data["phone"])
    phoneno = data["phone"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients_master_table WHERE phone=?",
                   (phoneno, ))
    patient = cursor.fetchone()
    if not patient:
      return render_template('error.html', message='No such user found')
    if check_password(password, patient[9]):
      print("success patient login")
      session['user_type'] = 'patient'
      session['patient_id'] = patient[0]
      return redirect('/patient_dashboard')
    else:
      return render_template('error.html', message="Invalid credentials")
  return render_template('patient_login.html')


@app.route("/doctor_login", methods=["GET", "POST"])
def doctor_login():
  if request.method == "POST":
    print("POST /doctor_login request received")
    data = request.form
    print(data["registrationNumber"])
    print(data["password"])
    regNo = data["registrationNumber"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE regNo=?",
                   (regNo, ))
    existing_doctor = cursor.fetchone()
    if not existing_doctor:
      return render_template('error.html', message='No such user found')

    if check_password(password, existing_doctor[6]):
      print("success doctor login")
      session['user_type'] = 'doctor'
      session['doctor_id'] = existing_doctor[0]
      return redirect(url_for('doctor_dashboard'))
    else:
      print("Invalid password")
      return render_template('error.html', message='Invalid credentials')
  return render_template('doctor_login.html')


@app.route("/hospital_login", methods=["GET", "POST"])
def hospital_login():
  if request.method == "POST":
    print("POST /hospital_login request received")
    data = request.form
    print(data["email"])
    print(data["password"])
    email = data["email"]
    password = data["password"]
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE email=?",
                   (email, ))
    existing_hospital = cursor.fetchone()
    if not existing_hospital:
      return render_template('error.html', message='No such user found')
    if check_password(password, existing_hospital[8]):
      print("success hospital login")
      session['user_type'] = 'hospital'
      session['hospital_id'] = existing_hospital[0]
      return redirect(url_for('hospital_dashboard'))
    else:
      print("Invalid password")
      return render_template('error.html', message='Invalid credentials')
  return render_template('hospital_login.html')


@app.route("/getPatients")
def getPatients():
  conn = db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM patients_master_table")
  patients = cursor.fetchall()
  conn.close()
  patients_list = []
  for row in patients:
    patient = {
        "patientId": row[0],
        "fullName": row[1],
        "dob": row[2],
        "bloodGroup": row[3],
        "email": row[4],
        "phone": row[5],
        "relativeName": row[6],
        "relativeNumber": row[7],
        "address": row[8],
        "passwordHash": row[9]
    }
    patients_list.append(patient)
  print("/getPatients request received")
  return jsonify({"patients": patients_list})


@app.route("/getDoctors")
def getDoctors():
  conn = db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM doctors_master_table")
  doctors = cursor.fetchall()
  conn.close()
  doctors_list = []
  for row in doctors:
    doctor = {
        "doctorId": row[0],
        "fullName": row[1],
        "regNo": row[2],
        "email": row[3],
        "hospital": row[4],
        "department": row[5],
        "passwordHash": row[6],
    }
    doctors_list.append(doctor)
  print("/getDoctors request received")
  return jsonify({"doctors": doctors_list})


############################### INDEX


@app.route('/register')
def registerTableRender():
  return render_template('RegisterTable.html')


@app.route('/hospitals')
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


############################### DASHBORD


############### DOCTOR #################
@app.route("/doctor_dashboard")
def doctor_dashboard():
  if session.get('user_type') == 'doctor':
    doctorId = session.get('doctor_id')
    print(doctorId)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors_master_table WHERE doctorId = ?",
                   (doctorId, ))
    doctor = cursor.fetchone()
    doctor_name = doctor[1]
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
      cursor.execute("SELECT * FROM patients_master_table WHERE patientId = ?",
                     (row[1], ))
      patient = cursor.fetchone()
      a['pName'] = patient[1]
      aptmts_list.append(a)
    return render_template('doctor_dashboard_appointments.html',
                           aptmts=aptmts_list)
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


############### HOSPITAL #################
@app.route("/hospital_dashboard")
def hospital_dashboard():
  if session.get('user_type') == 'hospital':
    hospitalId = session.get('hospital_id')
    print(hospitalId)
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospitals_master_table WHERE hospitalId = ?",
                   (hospitalId, ))
    hospital = cursor.fetchone()
    hospital_name = hospital[1]
    return render_template('hospital_dashboard.html',
                           hospitalName=hospital_name)
  return redirect(url_for('hospital_login'))


############### PATIENT #################

def get_appointment_data(id):
  conn = db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM patients_master_table WHERE patientId = ?", (id, ))
  patient = cursor.fetchone()
  pname = patient[1]
  cursor.execute("SELECT * FROM appointments_table WHERE patientId = ?", (id, ))
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



@app.route("/patient_dashboard")
def patient_dashboard():
  if session.get('user_type') == 'patient':
    patientId = session.get('patient_id')
    appointments = get_appointment_data(patientId)
    return render_template('patient_dashboard.html',
                           patientData=appointments)
  else:
    return redirect(url_for('patient_login'))


############### LOGOUT ##################
@app.route('/logout')
def logout():
  print("logout")
  session.pop('user_type', None)
  return redirect(url_for('index'))


if __name__ == "__main__":
  app.run(debug=True)
