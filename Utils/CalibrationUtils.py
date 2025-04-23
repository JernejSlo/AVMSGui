import os
import sqlite3
from datetime import datetime

class CalibrationUtils():

    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.ensure_connection()

    def ensure_connection(self):
        """ Make sure the database exists and open a connection """
        db_exists = os.path.exists(self.db_name)

        # Allow the connection to be shared across threads
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)

        if not db_exists:
            self.create_tables()

    def create_tables(self):
        """ Create tables if they don't exist (only once) """
        cursor = self.conn.cursor()

        # Table for calibration events
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS calibrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_type VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Table for individual measurements
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calibration_id INTEGER,
            set_value FLOAT,
            calculated_value FLOAT,
            ref_set_diff FLOAT,
            std FLOAT,
            timestamp DATETIME,
            FOREIGN KEY (calibration_id) REFERENCES calibrations(id)
        )
        """)

        self.conn.commit()
        print(f"Database '{self.db_name}' created with 'calibrations' and 'measurements' tables.")

    def log_new_calibration(self, method_type):
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO calibrations (method_type) VALUES (?)",
            (method_type,)
        )
        calibration_id = cursor.lastrowid
        self.conn.commit()
        print(f"New calibration with method '{method_type}' logged with ID {calibration_id}.")

        return calibration_id

    def close(self):
        if self.conn:
            self.conn.close()

    def log_measurement(self, calibration_id, set_value, calculated_value, ref_set_diff, std):
        cursor = self.conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO measurements (calibration_id, set_value, calculated_value, ref_set_diff, std, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (calibration_id, set_value, calculated_value, ref_set_diff, std, timestamp))

        self.conn.commit()
        print(f"Measurement logged for calibration ID {calibration_id}.")

"""utils = CalibrationUtils()

# Step 1: Create database (only needed once)
utils.create_db("calibration.db")

# Step 2: Add a new calibration
calib_id = utils.log_new_calibration("calibration.db", "DCV")

# Step 3: Log a measurement set_value, calculated_value, ref_set_diff, std
utils.log_measurement("calibration.db", calib_id, 297.7, 296.6, 1.1, 0.3)"""
