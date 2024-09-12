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
          'appointmentId': appointment['appointmentId'],
          'date': appointment['date'],
          'time': appointment['time'],
          'hospitalName': appointment['hospitalName'],
          'department': appointment['department'],
          'doctorName': appointment['doctorName'],
          'status': appointment['status']
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
    cursor.execute("SELECT fullName, dob, email, bloodGroup, address, phone FROM patients_master_table WHERE patientId = %s", (patientId, ))
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
            selectedRelativeId = data.get("selectRelative")  # Get selected relative's ID if any

            # If the appointment is for a relative, set the relative as the patient
            if selectedRelativeId != patientId:
                relativeType = data.get("relativeType")
            else:
                appointmentPatientId = patientId  # Appointment for the logged-in patient

            # Collect form data
            Patient_name = data["fullName"]
            dob = data["dob"]
            bloodGroup = data["bloodGroup"]
            email = data["email"]
            phone = data["phone"]
            hospitalName = data["hospital"]
            department = data["department"]
            visitDate = data["visitDate"]
            addRelative = data["patientRelative"]

            if addRelative:
                # Insert into patients_relatives_table
                cursor.execute(
                    "INSERT INTO patients_relatives_table (patientId, relationship, fullName, dob, bloodGroup) VALUES (%s, %s, %s, %s, %s)", (patientId, relativeType, Patient_name, dob, bloodGroup)
                )
                conn.commit()
                cursor.execute("SELECT relationId FROM patients_relatives_table WHERE patientId=%s AND relationship=%s", (patientId, relativeType))
                relationId = cursor.fetchone()
                if relationId:
                  appointmentPatientId = relationId['relationId']  # Appointment for the relative
                else:
                  appointmentPatientId = patientId  # Appointment for the logged-in patient

                cursor.execute(
                  "INSERT INTO appointments_table (patientId, relationId, date, hospitalName, department) VALUES (%s, %s, %s, %s, %s)",
                  (patientId, appointmentPatientId, visitDate, hospitalName, department)
                  )
                conn.commit()
            else:
                cursor.execute(
                  "INSERT INTO appointments_table (patientId, relationId, date, hospitalName, department) VALUES (%s, %s, %s, %s, %s)",
                  (patientId, selectedRelativeId, visitDate, hospitalName, department)
                  )
                conn.commit()

            # Insert into appointments_table
            

            return redirect(url_for('patient_dashboard_appointments'))


        if request.method == "GET":
            # Fetch patient details for the logged-in user
            cursor.execute("SELECT fullName, dob, bloodGroup, email, phone FROM patients_master_table WHERE patientId=%s", (patientId,))
            patient = cursor.fetchone()

            # Fetch the logged-in patient's relatives
            cursor.execute("""
                SELECT pr.relationId, pr.relationship, pr.fullName, pr.dob, pr.bloodGroup
                FROM patients_relatives_table pr
                JOIN patients_master_table p ON pr.relativePatientId = p.patientId
                WHERE pr.patientId = %s
            """, (patientId,))
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