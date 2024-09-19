import pickle
import mysql.connector
from datetime import datetime
import os
import base64
import pandas as pd
import numpy as np

image_folder = "Employee_Images"
download_folder = "Downloaded_Images"
export_folder = "Attendance_Records"

# MySQL connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'Employee_Details'
}

# Establishing MySQL connection
def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        print("Connected to MySQL database")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Creating a table for employee images if not exists
def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee  
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(100) NOT NULL,
                contact_no INT(10) DEFAULT 0,
                status TINYINT(1) DEFAULT 1,
                faceEncoding BLOB
            );
        """)
        print("Table 'employee' created successfully.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_images  
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id INT NOT NULL,
                employee_name VARCHAR(100) NOT NULL,
                employee_image LONGTEXT,
                capture_datetime DATETIME NOT NULL
            )
        """)
        connection.commit()
        print("Table 'employee_images' created successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def image_exists(cursor, employee_name, capture_date):
    cursor.execute("""
        SELECT COUNT(*) FROM employee_images
        WHERE employee_name = %s AND DATE_FORMAT(capture_datetime,'%Y-%m-%d') = %s
    """, (employee_name, capture_date))
    return cursor.fetchone()[0] > 0

def employee_exists(cursor, employee_name,faceEncoding):
    try:
        serialized_encoding = pickle.dumps(faceEncoding)

        cursor.execute("""
        SELECT COUNT(*) FROM employee WHERE employee_name = %s AND faceEncoding = %s
        """, (employee_name,serialized_encoding))

        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

# Encoding image to Base64
def encode_image_to_base64(realtime_image_path):
    with open(realtime_image_path, 'rb') as image_file:
        image_data = image_file.read()
    return base64.b64encode(image_data).decode('utf-8')

# Inserting captured image data into MySQL database
def insert_image_data(connection, employee_name, realtime_image_path, face_detected): #,imgModeList,imgBackground):
    try:
        if face_detected:
            cursor = connection.cursor()
            capture_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            capture_date = datetime.now().strftime("%Y-%m-%d")

            # Check if the attendance is already marked
            if image_exists(cursor, employee_name, capture_date):
                print("Attendance Already Marked.")
                return {'status': 'already_marked'}
                # imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[3]
                # cv2.imshow('FaceAttendance', imgBackground)
                # return imgModeList[3]
                # return

            # Fetch the employee face encoding from the database
            faceEncoding = get_encoding_from_db(connection, employee_name)
            if faceEncoding is None:
                print(f"No encoding found for {employee_name}. Cannot mark attendance.")
                return

            # Fetch the employee ID if the employee exists with the provided encoding
            if employee_exists(cursor, employee_name,faceEncoding):
                cursor.execute("""
                           SELECT id FROM employee WHERE employee_name = %s
                       """, (employee_name,))
                result = cursor.fetchone()
                emp_id = result[0]
                print(f"Employee ID for {employee_name} found: {emp_id}")
            else:
                print(f"Employee {employee_name} with the provided encoding not found.")
                return

            # Convert the image to base64
            image_data_base64 = encode_image_to_base64(realtime_image_path)
            if image_data_base64:
                # Insert the employee image record
                cursor.execute("""
                    INSERT INTO employee_images (employee_name, emp_id, employee_image, capture_datetime)
                    VALUES (%s, %s, %s, %s)
                """, (employee_name,emp_id,image_data_base64, capture_datetime))
                connection.commit()

                print("Attendance Marked. Image Data Inserted Into Database.")
                return {'status': 'marked'}
                # imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[2]
                # cv2.imshow('FaceAttendance', imgBackground)
                # return imgModeList[2]

            else:
                print("No Valid Image Files Found In The Folder.")

            # cursor.execute("""
            # UPDATE employee_images e
            # LEFT JOIN(
            #     SELECT employee_name, DATE(capture_datetime) as capture_date
            #     FROM employee_images
            #     GROUP BY employee_name, capture_date
            # ) p ON e.employee_name = p.employee_name AND DATE(e.capture_datetime) = p.capture_date
            # SET e.status = 'present'
            # WHERE p.employee_name IS NOT NULL;
            # """)
            # connection.commit()

            # cursor.execute("""
            # UPDATE employee_images e
            # LEFT JOIN (
            #     SELECT employee_name, DATE(capture_datetime) as capture_date
            #     FROM employee_images
            #     GROUP BY employee_name, capture_date
            # ) p ON e.employee_name = p.employee_name AND DATE(e.capture_datetime) = p.capture_date
            # SET e.attendance_status = 'absent'
            # WHERE p.employee_name IS NULL;
            # """)
            # connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def insert_encoding_to_db(connection,employee_name, faceEncoding):
    try:
        cursor = connection.cursor()
        if not employee_exists(cursor, employee_name,faceEncoding):
            serialized_encoding =pickle.dumps(faceEncoding)
            #print(f"Serialized encoding size: {len(serialized_encoding)} bytes")
            query = "INSERT INTO employee (employee_name, faceEncoding) VALUES (%s, %s)"
            cursor.execute(query, (employee_name, serialized_encoding))  # Store encoding as binary data
            connection.commit()
            print(f"Encoding for {employee_name} inserted into database.")
        else:
            print(f"Encoding for {employee_name} already exists in the database.")

    except Exception as e:
        print(f"Failed to insert encoding into database: {e}")

def get_encoding_from_db(connection, employee_name):
    try:
        cursor = connection.cursor()
        query = "SELECT faceEncoding FROM employee WHERE employee_name = %s"
        cursor.execute(query, (employee_name,))
        result = cursor.fetchone()

        if result:
            # Deserialize the face encoding using pickle
            serialized_encoding = result[0]
            #print(f"Retrieved raw binary data: {serialized_encoding[:100]}...")  # Print first 100 bytes for debugging
            face_encoding = pickle.loads(serialized_encoding)
            #print(f"Encoding for {employee_name} retrieved from database.")
            return face_encoding
        else:
            print(f"No encoding found for {employee_name}.")
            return None

    except Exception as e:
        print(f"Failed to fetch encoding from database: {e}")
        return None

def download_image(connection, employee_name, capture_datetime_str, download_folder, image_data_base64):
    try:
        capture_datetime = datetime.strptime(capture_datetime_str,'%Y-%m-%d %H:%M:%S')
        image_data = base64.b64decode(image_data_base64)
        image_filename = f"{employee_name}_{capture_datetime.strftime('%Y-%m-%d_%H-%M-%S%p')}.png"

        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        image_path = os.path.join(download_folder, image_filename)
        with open(image_path, 'wb') as image_file:
            image_file.write(image_data)
        print(f"Image downloaded and saved as {image_path}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Fetch attendance records and export to Excel
def export_attendance_to_excel(connection, capture_date, export_folder,download_folder):
    try:
        cursor = connection.cursor(dictionary=True)
        #cursor = connection.cursor()
        query = """
            #SELECT employee_name,capture_datetime
            SELECT employee_name,employee_image,DATE_FORMAT(capture_datetime, '%Y-%m-%d %H:%i:%S') AS capture_datetime
            FROM employee_images
            WHERE DATE(capture_datetime) = %s
        """
        cursor.execute(query, (capture_date,))
        records = cursor.fetchall()
        #print(f"Debug: fetched records = {records}")

        if records:
            df = pd.DataFrame(records, columns=['employee_name','capture_datetime'])
            #df = pd.DataFrame(records)
            # Debugging: Print DataFrame to verify its content
            print(f"Debug: DataFrame = {df}")
            if not os.path.exists(export_folder):
                os.makedirs(export_folder)
            export_path = os.path.join(export_folder, f"attendance_report_{capture_date}.xlsx")
            df.to_excel(export_path, index=False)
            print(f"Attendance records exported to {export_path}")
            for record in records:
                employee_name = record['employee_name']
                capture_datetime = record['capture_datetime']
                image_data_base64 = record['employee_image']
                download_image(connection,employee_name, capture_datetime,download_folder,image_data_base64)
            print(f"Employee Images Downloaded and saved to {download_folder}")
        else:
            print("No attendance records found for the specified date.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Closing database connection
def close_connection(connection):
    try:
        connection.close()
        print("MySQL connection closed.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
     connection = connect_to_database()
     if connection:
         create_table(connection)
         employee_name = "love"
         # while True:
         #        user_input_date = input("Enter the date (yyyy-mm-dd) for which you want to download attendance records: ")
         #        try:
         #            # Validate date format
         #            datetime.strptime(user_input_date, "%Y-%m-%d")
         #            break
         #        except ValueError:
         #            print("Invalid date format. Please enter the date in yyyy-mm-dd format.")
         # export_attendance_to_excel(connection, user_input_date, export_folder,download_folder)

         # Retrieve the encoding from the database
         retrieved_encoding = get_encoding_from_db(connection, employee_name)

         # Print the result or check if the encoding matches
         if retrieved_encoding is not None:
              # Check if the retrieved encoding matches the original encoding
              faceEncoding = get_encoding_from_db(connection, employee_name)
              if np.allclose(faceEncoding, retrieved_encoding):
                  print(f"Success: Retrieved encoding for {employee_name} matches the original encoding.")
              else:
                  print(f"Error: Retrieved encoding does not match the original encoding.")

              print(f"Retrieved encoding for {employee_name}: {retrieved_encoding}")

         else:
             print(f"Error: No encoding found for {employee_name}.")

     close_connection(connection)
