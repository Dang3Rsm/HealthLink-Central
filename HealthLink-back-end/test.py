# test file for testing the db connection

import pymysql
from datetime import datetime
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

sql_query = '''
INSERT INTO doctors_master_table (doctorId,fullName, regNo, email, hospital, department, passwordHash, attributes) 
VALUES 
(1,'John Doe', 'DR123', 'john.doe@example.com', 'Hospital A', 'Cardiology', 'password_hash_1', '{"specialization": "Cardiologist", "experience_years": 10}'),
(2,'Jane Smith', 'DR456', 'jane.smith@example.com', 'Hospital B', 'Orthopedics', 'password_hash_2', '{"specialization": "Orthopedic Surgeon", "experience_years": 8}');
'''
sol = cur.execute(sql_query)

print(sol)