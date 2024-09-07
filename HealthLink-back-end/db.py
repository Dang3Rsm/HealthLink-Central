########DB connection########
import pymysql

timeout = 10
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
  
cur = conn.cursor()

######## patients login ########
sql_query = '''CREATE TABLE IF NOT EXISTS patients_master_table (
    patientId INT AUTO_INCREMENT PRIMARY KEY,
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
    doctorId INT AUTO_INCREMENT PRIMARY KEY,
    fullName VARCHAR(255),
    regNo VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    hospital VARCHAR(255),
    department VARCHAR(255),
    passwordHash TEXT,
    attributes JSON
);'''
cur.execute(sql_query)



######## hospital login ########
sql_query = '''
CREATE TABLE IF NOT EXISTS hospitals_master_table (
    hospitalId INT AUTO_INCREMENT PRIMARY KEY,
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
    appointmentId INT AUTO_INCREMENT PRIMARY KEY,
    patientId INT,
    date DATE,
    time TIME,
    hospitalName VARCHAR(255),
    department VARCHAR(255),
    doctorName VARCHAR(255),
    status VARCHAR(100),
    FOREIGN KEY (patientId) REFERENCES patients_master_table(patientId)
);'''
cur.execute(sql_query)



######## patients_diagnosis_table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS patients_diagnosis_table (
    diagnoseID INT AUTO_INCREMENT PRIMARY KEY,
    appointmentID INT,
    patientID INT,
    date DATE,
    time TIME,
    diagnosis TEXT,
    recommendations TEXT,
    medicines TEXT,
    FOREIGN KEY (appointmentID) REFERENCES appointments_table(appointmentId),
    FOREIGN KEY (patientID) REFERENCES patients_master_table(patientId)
);
'''
cur.execute(sql_query)


conn.commit()
conn.close()
