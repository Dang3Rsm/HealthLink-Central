import sqlite3

conn = sqlite3.connect("HealthLinkDB.sqlite")
cur = conn.cursor()
######## patients login ########
sql_query = '''CREATE TABLE IF NOT EXISTS patients_master_table (
    patientId INTEGER PRIMARY KEY AUTOINCREMENT,
    fullName VARCHAR(255),
    dob DATE,
    bloodGroup VARCHAR(5),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(15) UNIQUE,
    relativeName VARCHAR(255),
    relativeNumber VARCHAR(15),
    address TEXT,
    passwordHash TEXT,
    attributes JSON
);'''
cur.execute(sql_query)


######## doctors login ########
sql_query = '''CREATE TABLE IF NOT EXISTS doctors_master_table (
    doctorId INTEGER PRIMARY KEY AUTOINCREMENT,
    fullName VARCHAR(255),
    regNo VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    hospital VARCHAR(15),
    department VARCHAR(255),
    passwordHash TEXT,
    attributes JSON
);'''
cur.execute(sql_query)



######## hospital login ########
sql_query = '''
CREATE TABLE IF NOT EXISTS hospitals_master_table (
    hospitalId INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    address VARCHAR(255),
    contactPerson VARCHAR(255),
    numberOfBeds INT,
    medicalStaff INT,
    nonMedicalStaff INT,
    email VARCHAR(255),
    passwordHash TEXT,
    attributes JSON
);'''
cur.execute(sql_query)



######## appointments_table ########
sql_query = '''CREATE TABLE IF NOT EXISTS appointments_table (
    appointmentId INTEGER PRIMARY KEY AUTOINCREMENT,
    patientId INT,
    date DATE,
    time TIME,
    hospitalName VARCHAR(255),
    department VARCHAR(255),
    doctorName VARCHAR(255),
    status VARCHAR(100)
);'''
cur.execute(sql_query)



######## patients_diagnosis_table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS patients_diagnosis_table (
    diagnoseID INTEGER PRIMARY KEY AUTOINCREMENT,
    appointmentID INT,
    patientID INT,
    date DATE,
    time TIME,
    Diagnosis TEXT,
    recommendations TEXT,
    medicines TEXT,
    FOREIGN KEY (appointmentID) REFERENCES appointments_table(appointmentID),
    FOREIGN KEY (patientID) REFERENCES master_patient_table(patientID)
);
'''
cur.execute(sql_query)


conn.commit()
conn.close()
