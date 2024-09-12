import pymysql
from datetime import datetime
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

# #### patients_master_table ####
# sample_data = [
#     ('John Doe', '1990-05-15', 'A+', 'john.doe@example.com', '1234567890',
#      'Jane Doe', '9876543210', '123 Sample St, Sample City', 'password_hash_1',
#      '{"allergies": ["Pollen", "Penicillin"], "medications": ["Aspirin"]}'),
#     ('Alice Smith', '1985-08-22', 'B-', 'alice.smith@example.com',
#      '9876543210', 'Bob Smith', '1234567890', '456 Test Ave, Test City',
#      'password_hash_2', '{"allergies": ["Dust"], "medications": []}'),
#     ('Michael Johnson', '1978-12-10', 'O+', 'michael.johnson@example.com',
#      '5555555555', 'Emily Johnson', '9999999999', '789 Main St, Main City',
#      'password_hash_3', '{"allergies": [], "medications": ["Insulin"]}'),
#     ('Sarah Williams', '1995-03-28', 'AB+', 'sarah.williams@example.com',
#      '1111111111', 'David Williams', '2222222222', '101 Oak St, Oak City',
#      'password_hash_4', '{"allergies": [], "medications": ["Antihistamine"]}'),
# ]
# sql_insert_query = '''
# INSERT INTO patients_master_table (fullName, dob, bloodGroup, email, phone, relativeName, relativeNumber, address, passwordHash, attributes) 
# VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
# '''
# for data in sample_data:
#   cur.execute(sql_insert_query, data)


# #### doctors_master_table ####
# sql_query = '''
# INSERT INTO doctors_master_table (doctorId,fullName, regNo, email, hospital, department, passwordHash, attributes) 
# VALUES 
# (1,'John Doe', 'DR123', 'john.doe@example.com', 'Hospital A', 'Cardiology', 'password_hash_1', '{"specialization": "Cardiologist", "experience_years": 10}'),
# (2,'Jane Smith', 'DR456', 'jane.smith@example.com', 'Hospital B', 'Orthopedics', 'password_hash_2', '{"specialization": "Orthopedic Surgeon", "experience_years": 8}');
# '''
# cur.execute(sql_query)

# #### hospitals_master_table ####
sql_query = '''
INSERT INTO hospitals_master_table (hospitalId, name, address, contactPerson, numberOfBeds, medicalStaff, nonMedicalStaff, email, passwordHash, attributes) 
VALUES (
    1001,
    'AIIMS JNU',
    '123 Sample Street, Sample City',
    'John Doe',
    100,
    50,
    20,
    'samplehospital@example.com',
    'samplePassword123',
    '{"weekdays": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "departments": ["Surgery", "Cardiology", "Orthology", "Neurology", "Gastroenterology", "Psychiatry", "Ophthalmo"]}'
);'''
cur.execute(sql_query)


#### appointments_table ####
# sample_data = [
#   (1, 9, '2024-04-15', '10:00 AM', 'Akhilesh das gupta hospital', 'Cardiology', 'Smith', 'upcoming'),
#   (2, 9, '2024-04-18', '02:30 PM', 'Sample Hospital', 'Orthopedics', 'Johnson', 'visited'),
#   (3, 9, '2024-04-20', '11:15 AM', 'City Medical Center', 'Dermatology', 'Patel', 'upcoming'),
#   (4, 9, '2024-04-22', '09:45 AM', 'Healthcare Clinic', 'Pediatrics', 'Williams', 'missed')
# ]

# for i in range(len(sample_data)):
#     date_str, time_str = sample_data[i][1], sample_data[i][2]
#     time_24hr = datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M')
#     sample_data[i] = (sample_data[i][0], date_str, time_24hr, sample_data[i][3], sample_data[i][4], sample_data[i][5], sample_data[i][6])

# sql_insert_query = '''
# INSERT INTO appointments_table (patientId, date, time, hospitalName, department, doctorName, status) 
# VALUES (%s, %s, %s, %s, %s, %s, %s)
# '''
# for data in sample_data:
#   cur.execute(sql_insert_query, data)






conn.commit()
conn.close()