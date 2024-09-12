########DB connection########
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()
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

# 1. Table: patients_master_table
# Purpose: Stores patient details including personal info, contact, and login credentials.

# 2. Table: doctors_master_table
# Purpose: Stores doctor details such as department, hospital affiliation, and login credentials.

# 3. Table: hospitals_master_table
# Purpose: Stores hospital details, including contact information, bed capacity, and login credentials.

# 4. Table: appointments_table
# Purpose: Stores appointment details for patients, including hospital, doctor, date, time, and status.

# 5. Table: patients_diagnosis_table
# Purpose: Stores diagnosis details for each patient appointment, including recommendations and prescribed medicines.

# 6. Table: billing_table
# Purpose: Stores billing information related to patient appointments, including total amount and payment status.

# 7. Table: inventory_table
# Purpose: Stores hospital inventory items, including quantity, type, and restocking information.

# 8. Table: staff_master_table
# Purpose: Stores staff details, including role (Doctor, Nurse, Admin), contact, and hire information.

# 9. Table: inventory_transactions_table
# Purpose: Tracks inventory transactions such as restocking and consumption, along with staff responsible for transactions.

# 10.Table: admissions_table
# Purpose: Tracks patient admissions, discharge details, and the associated hospital and doctor.

# 11.Table: beds_master_table
# Purpose: Manages hospital bed information, including ward type, availability, and status.


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
    status VARCHAR(100) default 'pending',
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

######## Billing Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS billing_table (
    billId INT AUTO_INCREMENT PRIMARY KEY,
    patientId INT,
    appointmentId INT,
    totalAmount DECIMAL(10, 2),
    paymentMethod VARCHAR(50),
    paymentStatus VARCHAR(50),
    billDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patientId) REFERENCES patients_master_table(patientId),
    FOREIGN KEY (appointmentId) REFERENCES appointments_table(appointmentId)
);
'''
cur.execute(sql_query)

######## Inventory Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS inventory_table (
    inventoryId INT AUTO_INCREMENT PRIMARY KEY,
    hospitalId INT,
    itemName VARCHAR(255),
    quantity INT,
    itemType VARCHAR(50),
    restockThreshold INT,
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expiryDate DATE,
    FOREIGN KEY (hospitalId) REFERENCES hospitals_master_table(hospitalId)
);
'''
cur.execute(sql_query)

######## Staff Master Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS staff_master_table (
    staffId INT AUTO_INCREMENT PRIMARY KEY,
    hospitalId INT,
    fullName VARCHAR(255),
    role VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(15) UNIQUE,
    hireDate DATE,
    department VARCHAR(255),
    attributes JSON,
    FOREIGN KEY (hospitalId) REFERENCES hospitals_master_table(hospitalId)
);
'''
cur.execute(sql_query)

######## Inventory Transactions Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS inventory_transactions_table (
    transactionId INT AUTO_INCREMENT PRIMARY KEY,
    inventoryId INT,
    hospitalId INT,
    itemName VARCHAR(255),
    transactionType VARCHAR(50),
    quantity INT,
    transactionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performedBy INT,
    notes TEXT,
    FOREIGN KEY (inventoryId) REFERENCES inventory_table(inventoryId),
    FOREIGN KEY (hospitalId) REFERENCES hospitals_master_table(hospitalId),
    FOREIGN KEY (performedBy) REFERENCES staff_master_table(staffId)
);
'''
cur.execute(sql_query)

######## Admissions Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS admissions_table (
    admissionId INT AUTO_INCREMENT PRIMARY KEY,
    patientId INT,
    hospitalId INT,
    admissionDate DATE,
    dischargeDate DATE,
    reasonForAdmission TEXT,
    status VARCHAR(50),
    doctorId INT,
    FOREIGN KEY (patientId) REFERENCES patients_master_table(patientId),
    FOREIGN KEY (hospitalId) REFERENCES hospitals_master_table(hospitalId),
    FOREIGN KEY (doctorId) REFERENCES doctors_master_table(doctorId)
);
'''
cur.execute(sql_query)

######## Beds Master Table ########
sql_query = '''
CREATE TABLE IF NOT EXISTS beds_master_table (
    bedId INT AUTO_INCREMENT PRIMARY KEY,
    hospitalId INT,
    bedNumber VARCHAR(50),
    ward VARCHAR(50),
    availabilityStatus VARCHAR(50),
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospitalId) REFERENCES hospitals_master_table(hospitalId)
);
'''
cur.execute(sql_query)

sql_query = '''
CREATE TABLE IF NOT EXISTS patients_relatives_table (
    relationId INT AUTO_INCREMENT PRIMARY KEY,
    patientId INT,                 -- The ID of the logged-in user
    relativePatientId INT,         -- The ID of the new patient being added as a relative
    relationship VARCHAR(255),     -- Type of relationship (e.g., father, mother, sibling, etc.)
    dateAdded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patientId) REFERENCES patients_master_table(patientId),
    FOREIGN KEY (relativePatientId) REFERENCES patients_master_table(patientId)
);
'''
cur.execute(sql_query)


conn.commit()
conn.close()
