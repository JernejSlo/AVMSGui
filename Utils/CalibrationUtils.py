import os
import sqlite3
from datetime import datetime
import pyvisa

class CalibrationUtils():

    def __init__(self,db_name):
        # database stuff
        self.db_name = db_name
        self.conn = None
        self.ensure_connection()

        # actual calibration stuff
        self.rm = pyvisa.ResourceManager()

        self.index = 0

        total_values = len(self.upper_panel.value_display.value_labels)

        self.current_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        self.difference_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]


        self.measParameters = {
            "numOfMeas": 5,
            "references": [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000],
            "range": [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000],
            "units": ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"],
            "measurements": [None, None, None, None, None, None, None, None, None, None, None],
            #"frequencies": ["10 Hz", "None", None, None, None, None, None, None, None, None],
            "diffMeas": [None, None, None, None, None, None, None, None, None, None, None],
            "stdVars": [None, None, None, None, None, None, None, None, None, None, None],
            "linearRefs": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "linearMeas": [None, None, None, None, None, None, None, None, None, None],
            "diffLinearMeas": [None, None, None, None, None, None, None, None, None, None],
            "linearStdVars": [None, None, None, None, None, None, None, None, None, None],
            "measType": "",
            "dirType": ""
        }

        pass

    def log_everything(self,idx=0):

        unit = self.measParameters["units"][idx]
        measurement = self.measParameters["measurements"][idx]
        if measurement is None:
            measurement = "--"
        diff = self.measParameters["diffMeas"][idx]
        if diff is None:
            diff = "--"
        std = self.measParameters["stdVars"][idx]
        if std is None:
            std = "--"

        # Generate new value
        self.current_values[idx] = {"Value": measurement, "Label": unit}
        # Compute difference and update
        self.difference_values[idx] = {"Value": diff, "Label": unit}

        self.upper_panel.value_display.labels_values["diffMeas"][idx] = diff

        # Update display
        self.upper_panel.value_display.update_values(self.current_values, self.difference_values)


        self.terminal.log(f'{measurement}')

    def waitForSettled(self):
        SETTLED = 12
        while not (int(self.F5522A.query('ISR?')) & (1 << SETTLED)):
            pass

    def measurement(self,numOfMeas: int, measRange: float):
        # inicializacija lista z dimenzijo numOfMeas
        MeasArray = [None] * numOfMeas

        # ponovitev meritev tolikokrat kot je vrednost numOfMeas
        for SameMeasNum in range(numOfMeas):
            HP34401A_string = f"MEASure:{self.measType}:{self.dirType}? {str(measRange)}"
            self.terminal.log(HP34401A_string)
            Meas = float(self.HP34401A.query(HP34401A_string))
            self.terminal.log(str(Meas))
            MeasArray[SameMeasNum] = Meas

        # izračun povprečne vrednosti meritev
        MeasAverage = sum(MeasArray) / numOfMeas

        # izračun standardne deviacije meritev
        stdVar = (sum((Meas - MeasAverage) ** 2 for Meas in MeasArray) / (numOfMeas - 1)) ** (1 / 2)

        return MeasAverage, stdVar

    def calibrate(self):

        self.HP34401A = self.rm.open_resource('GPIB0::22::INSTR')
        self.F5522A = self.rm.open_resource('GPIB0::4::INSTR')
        self.HP34401A.timeout = 2500
        self.F5522A.timeout = 2500
        rangeVDC = [0.1, 1, 10, 100, 1000]

        self.changeMeasParam(self.selected_mode)
        self.measProcess()

    def changeMeasParam(self,typeOfMeas: str):
        match typeOfMeas:
            case 'DCV':
                self.measParameters["references"] = [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000]
                self.measParameters["range"] = [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000]
                self.measParameters["units"] = ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"]
                self.measParameters["measType"] = "VOLTage"
                self.measParameters["dirType"] = "DC"
                pass

            case 'ACV':
                self.measParameters["references"] = [0, 100, -100, 1, -1, 10, -10, 100, -100, 750, -750]
                self.measParameters["range"] = [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 750, 750]
                self.measParameters["units"] = ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"]
                self.measParameters["measType"] = "VOLTage"
                self.measParameters["dirType"] = "AC"
                pass

            case 'DCI':
                self.measParameters["references"] = [0, 10, -10, 100, -100, 1, -1, 2.99999, -2.99999]
                self.measParameters["range"] = [0.01, 0.01, 0.01, 0.1, 0.1, 1, 1, 3, 3]
                self.measParameters["units"] = ["mA", "mA", "mA", "mA", "mA", "A", "A", "A", "A"]
                self.measParameters["measType"] = "CURRent"
                self.measParameters["dirType"] = "DC"
                pass

            case 'ACI':
                self.measParameters["references"] = [0, 1, -1, 3, -3]
                self.measParameters["range"] = [1, 1, 1, 3, 3]
                self.measParameters["units"] = ["A", "A", "A", "A", "A"]
                self.measParameters["measType"] = "CURRent"
                self.measParameters["dirType"] = "AC"
                pass

            case 'OHM':
                self.measParameters["references"] = [100, 1, 10, 100, 1, 10, 100]  # PROBLEM MOGOČ
                self.measParameters["range"] = [100, 1, 10, 100, 1, 10, 100] # PROBLEM MOGOČ
                self.measParameters["units"] = ["Ω", "kΩ", "kΩ", "kΩ", "MΩ", "MΩ", "MΩ"]
                self.measParameters["measType"] = "FRESistance" # RESistance od vključno 100 kΩ naprej
                self.measParameters["dirType"] = ""
                pass

            case 'FRE':
                self.measParameters["references"] = [3, 30, 300, 3, 30, 300]
                self.measParameters["range"] = ""   # The Agilent 34401A automatically selects an appropriate range based on the frequency of the signal it is measuring.
                self.measParameters["units"] = ["Hz", "Hz", "Hz", "kHz", "kHz", "kHz"]
                self.measParameters["measType"] = "FREQuency"
                self.measParameters["dirType"] = ""
                pass

            case _: # default
                pass

        measParameters = {
            "references": [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000],
            "range": [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000],
            "units": ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"],
            "measurements": [None, None, None, None, None, None, None, None, None, None, None],
            "diffMeas": [None, None, None, None, None, None, None, None, None, None, None],
            "stdVars": [None, None, None, None, None, None, None, None, None, None, None],
            "numOfMeas": 5,
            "linearRefs": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "linearMeas": [None, None, None, None, None, None, None, None, None, None],
            "diffLinearMeas": [None, None, None, None, None, None, None, None, None, None],
            "linearStdVars": [None, None, None, None, None, None, None, None, None, None],
            "measType": "",
            "dirType": ""
        }


    def measProcess(self):
        for i in range(16):
            self.F5522A.query('ERR?')
        self.measType = self.measParameters['measType']
        self.dirType = self.measParameters['dirType']
        # prvi del kalibracije
        for MeasNum in range(len(self.measParameters["references"])):
            # konfiguracija meritve na multimetru HP34401A

            HP34401A_string = f"{'CONFigure:'}{self.measType}{':'}{self.dirType} {self.measParameters['range'][MeasNum]}"
            print(HP34401A_string)
            self.terminal.log(f'IN HP34401A: {HP34401A_string}')
            self.HP34401A.write(HP34401A_string)

            # konfiguracija referenčne vrednosti na kalibratorju F5522A

            F5522A_string = f"{'OUT'} {self.measParameters['references'][MeasNum]} {self.measParameters['units'][MeasNum]}"
            self.terminal.log(f'IN F5522A: {F5522A_string}')

            self.F5522A.write(F5522A_string)

            # vklop referenčne vrednosti na kalibratorju F5522A
            F5522A_string = 'OPER'
            self.terminal.log(f'IN F5522A: {F5522A_string}')
            self.F5522A.write(F5522A_string)

            # čakanje na izravnavo referenčne vrednosti
            self.waitForSettled()

            # izračun in zapis meritve
            [MeasAverage, stdVar] = self.measurement(self.measParameters["numOfMeas"], self.measParameters["range"][MeasNum])
            unitConv = self.convertMeasurments(self.measParameters["units"][MeasNum])
            self.measParameters["measurements"][MeasNum] = MeasAverage / unitConv
            self.measParameters["diffMeas"][MeasNum] = self.measParameters["references"][MeasNum] - MeasAverage / unitConv
            self.measParameters["stdVars"][MeasNum] = stdVar / unitConv

            self.log_everything(MeasNum)

            # izklop referenčne vrednosti na kalibratorju F5522A
            F5522A_string = 'STBY'
            self.terminal.log(F5522A_string)
            self.F5522A.write(F5522A_string)

        if self.measType == "VOLTage":
            # konfiguracija meritve na multimetru HP34401A
            HP34401A_string = f"CONFigure:{self.measType}:{self.dirType} 10"
            self.terminal.log(f'IN HP34401A: {HP34401A_string}')
            self.HP34401A.write(HP34401A_string)

            for MeasNum in range(len(self.measParameters["linearRefs"])):

                unit = self.measParameters['units'][MeasNum]

                # konfiguracija referenčne vrednosti na kalibratorju F5522A
                F5522A_string = f"{'OUT'} {str(self.measParameters['linearRefs'][MeasNum])} {'V'}"
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

                # vklop referenčne vrednosti na kalibratorju F5522A
                F5522A_string = 'OPER'
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

                # čakanje na izravnavo referenčne vrednosti
                self.waitForSettled()

                # izračun in zapis meritve
                HP34401A_string = f"MEASure:{self.measType}:{self.dirType}? 10"
                [MeasAverage, stdVar] = self.measurement(self.measParameters["numOfMeas"], measRange = 10)
                self.measParameters["linearMeas"][MeasNum] = MeasAverage
                self.measParameters["linearStdVars"][MeasNum] = stdVar

                # izklop referenčne vrednosti na kalibratorju F5522A
                F5522A_string = 'STBY'
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

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

    def convertMeasurments(self, unit):
        unitConv = 1
        if unit[0] == "m":
            unitConv = 1e-3
        if unit[0] == "k":
            unitConv = 1e3
        if unit[0] == "M":
            unitConv = 1e6
        return unitConv


