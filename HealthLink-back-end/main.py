from flask import Flask, request, jsonify, render_template, session
from flask import redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import json
import bcrypt
from dotenv import load_dotenv
import os
from datetime import datetime
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
            print(data)

            fullName = data.get('fullName')
            bloodGroup = data.get('bloodGroup')
            dob = data.get('dob')
            hospital = data.get('hospital')
            department = data.get('department')
            visitDate = data.get('visitDate')

            if selectedRelativeId and selectedRelativeId != 'self' and selectedRelativeId != 'new':
              relativeId = selectedRelativeId

            elif selectedRelativeId == 'new':
              relationship = data.get('relativeType')
              cursor.execute("INSERT INTO patients_relatives_table (patientId, relationship, fullName, bloodGroup, dob) VALUES (%s, %s, %s, %s, %s)", (patientId, relationship, fullName, bloodGroup, dob))
              conn.commit()

              cursor.execute("SELECT * FROM patients_relatives_table WHERE patientId=%s and fullName=%s", (patientId, fullName))
              relative = cursor.fetchone()
              relativeId = relative['relationId']

            else:
              relativeId = NULL
            
            cursor.execute(
                """
                INSERT INTO appointments_table 
                (patientId, relationId, date, hospitalName, department) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (patientId, relativeId, visitDate, hospital, department)
            )
            conn.commit()


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
    app.run(debug=True)