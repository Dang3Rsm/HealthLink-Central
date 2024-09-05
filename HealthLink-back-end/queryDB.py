import sqlite3
conn = sqlite3.connect("HealthLinkDB.sqlite")
cur = conn.cursor()

# Define SQL queries to insert additional records into hospitals_master_table
sql_queries = [
    '''
    INSERT INTO hospitals_master_table (hospitalId, name, address, contactPerson, numberOfBeds, medicalStaff, nonMedicalStaff, email, passwordHash, attributes) 
    VALUES (
        1004,
        'Fortis Hospital',
        '101 Example Street, Example City',
        'Michael Brown',
        180,
        90,
        35,
        'fortishospital@example.com',
        'fortisHospital123',
        '{"weekdays": ["Monday", "Wednesday", "Friday"], "departments": ["Orthology", "Gastroenterology", "Psychiatry"]}'
    );
    ''',
    '''
    INSERT INTO hospitals_master_table (hospitalId, name, address, contactPerson, numberOfBeds, medicalStaff, nonMedicalStaff, email, passwordHash, attributes) 
    VALUES (
        1005,
        'Columbia Asia Hospital',
        '202 Sample Road, Sample City',
        'Sarah Lee',
        120,
        60,
        25,
        'columbiaasia@example.com',
        'columbiaAsia123',
        '{"weekdays": ["Tuesday", "Thursday", "Saturday"], "departments": ["Cardiology", "Neurology", "Ophthalmology"]}'
    );
    ''',
    '''
    INSERT INTO hospitals_master_table (hospitalId, name, address, contactPerson, numberOfBeds, medicalStaff, nonMedicalStaff, email, passwordHash, attributes) 
    VALUES (
        1006,
        'Apollo Hospital',
        '303 Example Avenue, Example City',
        'David Wilson',
        250,
        120,
        40,
        'apollohospital@example.com',
        'apolloHospital123',
        '{"weekdays": ["Monday", "Wednesday", "Friday"], "departments": ["Surgery", "Cardiology", "Orthology", "Neurology"]}'
    );
    '''
]

# Execute each SQL query to insert additional records into the database
for sql_query in sql_queries:
    cur.execute(sql_query)




conn.commit()
conn.close()