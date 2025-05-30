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
        self.hpadress = 22
        self.flukeadress = 4
        self.custom_address_chosen = False
        # actual calibration stuff
        self.rm = pyvisa.ResourceManager()

        self.index = 0

        total_values = len(self.upper_panel.value_display.value_labels)

        self.current_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        self.difference_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        self.std_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        self.measParameters = {
            "references": [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000],
            "linearRefs": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],}
        self.measParameters = {
            "references": [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000],
            "range": [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000],
            "frequencies": [element for element in ["100 Hz", "1 kHz", "10 kHz"] for _ in range(len(self.measParameters["references"]))],
            "unique_frequencies": ["100 Hz", "1 kHz", "10 kHz"],
            "units": ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"],
            "measurements": [None] * len(self.measParameters["references"]),
            "diffMeas": [None] * len(self.measParameters["references"]),
            "stdVars": [None] * len(self.measParameters["references"]),
            "numOfMeas": 5,
            "linearRefs": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "linearUnits": "V" * len(self.measParameters["linearRefs"]),
            "linearMeas": [None] * len(self.measParameters["linearRefs"]),
            "diffLinearMeas": [None] * len(self.measParameters["linearRefs"]),
            "linearStdVars": [None] * len(self.measParameters["linearRefs"]),
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

        print(self.measParameters["stdVars"])
        # Generate new value
        self.current_values[idx] = {"Value": measurement, "Label": unit}
        # Compute difference and update
        self.difference_values[idx] = {"Value": diff, "Label": unit}

        self.std_values[idx] = {"Value": std, "Label": unit}

        self.upper_panel.value_display.labels_values["diffMeas"][idx] = diff

        self.upper_panel.value_display.labels_values["stdDevs"][idx] = std
        # Update display
        self.upper_panel.value_display.update_values(self.current_values, self.difference_values, self.std_values)

    def waitForSettled(self):
        SETTLED = 12
        while not (int(self.F5522A.query('ISR?')) & (1 << SETTLED)):
            pass

    def measurement(self,numOfMeas: int, measRange: float):
        # inicializacija lista z dimenzijo numOfMeas
        MeasArray = [None] * numOfMeas

        # ponovitev meritev tolikokrat kot je vrednost numOfMeas
        for SameMeasNum in range(numOfMeas):
            HP34401A_string = f"MEASure:{self.measType}{self.dirType}? {str(measRange)}"
            self.terminal.log(f"IN HP34401A: {HP34401A_string}")
            Meas = float(self.HP34401A.query(HP34401A_string))
            self.terminal.log(f"OUT HP34401A: {str(Meas)}")
            MeasArray[SameMeasNum] = Meas
            if self.interrupt_calib("Measurement interrupted."): return

        # izračun povprečne vrednosti meritev
        MeasAverage = sum(MeasArray) / numOfMeas

        # izračun standardne deviacije meritev
        stdVar = (sum((Meas - MeasAverage) ** 2 for Meas in MeasArray) / (numOfMeas - 1)) ** (1 / 2)

        return MeasAverage, stdVar

    def calibrate(self):
        try:
            self.HP34401A = self.rm.open_resource(f'GPIB0::{self.hpadress}::INSTR')
            self.HP34401A.timeout = 2500

            # Try a simple query to test connection
            idn_hp = self.HP34401A.query("*IDN?")
            print("HP 34401A connected:", idn_hp.strip())

            self.F5522A = self.rm.open_resource(f'GPIB0::{self.flukeadress}::INSTR')
            self.F5522A.timeout = 2500

            # Try a simple query to test connection
            idn_fluke = self.F5522A.query("*IDN?")
            print("FLUKE 5522A connected:", idn_fluke.strip())

        except:
            self.stop_action()
            self.show_input_popup(message="Enter addresses for HP 34401A and FLUKE 5522A (current addresses are broken or machine isn't turned on):", show_default=self.custom_address_chosen)



        self.measProcess()
        self.stop_action()

    def changeMeasParam(self,typeOfMeas: str):

        match typeOfMeas:
            case 'DCV':
                self.measParameters["references"] = [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000]
                self.measParameters["range"] = [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000]
                self.measParameters["units"] = ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["linearRefs"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                self.measParameters["linearUnits"] = ["V"] * len(self.measParameters["linearRefs"])
                self.measParameters["measType"] = "VOLTage"
                self.measParameters["dirType"] = ":DC"
                pass

            case 'ACV':
                unique_freqs = len(self.measParameters["unique_frequencies"])
                self.measParameters["references"] = [element for element in [100, 1, 10, 100, 750] for _ in range(unique_freqs)]
                self.measParameters["range"] = [element for element in [0.1, 1, 10, 100, 750] for _ in range(unique_freqs)]
                self.measParameters["units"] = [element for element in ["mV", "V", "V", "V", "V"] for _ in range(unique_freqs)]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["linearRefs"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                self.measParameters["linearUnits"] = ["Hz"] * len(self.measParameters["linearRefs"])
                self.measParameters["linearMeas"] = [None] * len(self.measParameters["linearRefs"])
                self.measParameters["diffLinearMeas"] = [None] * len(self.measParameters["linearRefs"])
                self.measParameters["linearStdVars"] = [None] * len(self.measParameters["linearRefs"])
                self.measParameters["measType"] = "VOLTage"
                self.measParameters["dirType"] = ":AC"
                pass

            case 'DCI':
                self.measParameters["references"] = [0, 10, -10, 100, -100, 1, -1, 2.99999, -2.99999]
                self.measParameters["range"] = [0.01, 0.01, 0.01, 0.1, 0.1, 1, 1, 3, 3]
                self.measParameters["units"] = ["mA", "mA", "mA", "mA", "mA", "A", "A", "A", "A"]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["measType"] = "CURRent"
                self.measParameters["dirType"] = ":DC"
                pass

            case 'ACI':
                unique_freqs = len(self.measParameters["unique_frequencies"])
                self.measParameters["references"] = [element for element in [1, 2.99999] for _ in range(unique_freqs)]
                self.measParameters["range"] = [element for element in [1, 3] for _ in range(unique_freqs)]
                self.measParameters["units"] = [element for element in ["A", "A"] for _ in range(unique_freqs)]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["measType"] = "CURRent"
                self.measParameters["dirType"] = ":AC"
                pass

            case 'RES':
                self.measParameters["references"] = [100, 1, 10, 100, 1, 10, 100]  # PROBLEM MOGOČ
                self.measParameters["range"] = [100, 1e3, 10e3, 100e3, 1e6, 10e6, 100e6] # PROBLEM MOGOČ
                self.measParameters["units"] = ["OHM", "kOHM", "kOHM", "kOHM", "MOHM", "MOHM", "MOHM"]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["measType"] = "FRESistance" # RESistance do izključno 100 kΩ
                self.measParameters["dirType"] = ""
                pass

            case 'FREQ.':
                self.measParameters["references"] = [3, 30, 300, 3, 30, 300]
                self.measParameters["range"] = [""] * len(self.measParameters["references"])
                self.measParameters["units"] = ["Hz", "Hz", "Hz", "kHz", "kHz", "kHz"]
                self.measParameters["measurements"] = [None] * len(self.measParameters["references"])
                self.measParameters["diffMeas"] = [None] * len(self.measParameters["references"])
                self.measParameters["stdVars"] = [None] * len(self.measParameters["references"])
                self.measParameters["measType"] = "FREQuency"
                self.measParameters["dirType"] = ""
                pass

            case _: # default
                pass

        for i in range(len(self.measParameters["measurements"])):
            self.log_everything(i)


    def interrupt_calib(self, message):
        if not self.running:
            self.terminal.log(message)
            return True

    def measProcess(self):
        for i in range(16):
            self.F5522A.query('ERR?')
        self.measType = self.measParameters['measType']
        self.dirType = self.measParameters['dirType']
        self.freqNum = 0

        self.frequency = self.measParameters["unique_frequencies"][self.freqNum]
        # prvi del kalibracije

        for MeasNum in range(len(self.measParameters["references"])):
            break
            # postavitev frekvence na nič pri meritvah DC veličin
            if self.dirType != ":AC" and self.measType != 'FREQuency' and MeasNum == 0:
                F5522A_string = "OUT 0 Hz"
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

            # postavitev referenčne napetosti na 1 V pri meritvah frekvence
            if self.dirType == ":AC":
                self.frequency = self.measParameters["unique_frequencies"][self.freqNum]
                F5522A_string = f"OUT {self.frequency}"
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)
                self.freqNum = (self.freqNum + 1) % len(self.measParameters["unique_frequencies"])

            # postavitev na dvožični način merjenja upornosti
            if self.measType == 'FRESistance' and MeasNum == 3:
                self.measParameters["measType"] = 'RESistance'
                self.measType = self.measParameters['measType']

            # postavitev referenčne napetosti na 1 V pri meritvah frekvence
            if self.measType == 'FREQuency' and MeasNum == 0:
                F5522A_string = "OUT 1 V"
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

            # konfiguracija meritve na multimetru HP34401A
            HP34401A_string = f"{'CONFigure:'}{self.measType}{self.dirType} {self.measParameters['range'][MeasNum]}"
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

            if self.interrupt_calib("Measurement interrupted."): return
            # čakanje na izravnavo referenčne vrednosti
            self.waitForSettled()
            if self.interrupt_calib("Measurement interrupted."): return

            # izračun in zapis meritve
            [MeasAverage, stdVar] = self.measurement(self.measParameters["numOfMeas"], self.measParameters["range"][MeasNum])
            unitConv = self.convertMeasurments(self.measParameters["units"][MeasNum])
            self.measParameters["measurements"][MeasNum] = MeasAverage / unitConv
            self.measParameters["diffMeas"][MeasNum] = self.measParameters["references"][MeasNum] - MeasAverage / unitConv
            self.measParameters["stdVars"][MeasNum] = stdVar / unitConv

            print(self.measParameters["stdVars"][MeasNum])

            self.log_everything(MeasNum)

            # izklop referenčne vrednosti na kalibratorju F5522A
            F5522A_string = 'STBY'
            self.terminal.log(f'IN F5522A: {F5522A_string}')
            self.F5522A.write(F5522A_string)

            self.terminal.log("")

        if self.measType == "VOLTage":
            # konfiguracija meritve na multimetru HP34401A
            HP34401A_string = f"CONFigure:{self.measType}{self.dirType} 10"
            self.terminal.log(f'IN HP34401A: {HP34401A_string}')
            self.HP34401A.write(HP34401A_string)

            for MeasNum in range(len(self.measParameters["linearRefs"])):

                if self.dirType == ":AC":
                    F5522A_string = "OUT 10 V"
                    self.terminal.log(f'IN F5522A: {F5522A_string}')
                    self.F5522A.write(F5522A_string)

                # konfiguracija referenčne vrednosti na kalibratorju F5522A
                F5522A_string = f"{'OUT'} {str(self.measParameters['linearRefs'][MeasNum])} {self.measParameters['linearUnits'][MeasNum]}"
                print({self.measParameters['linearUnits'][MeasNum]})
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

                # vklop referenčne vrednosti na kalibratorju F5522A
                F5522A_string = 'OPER'
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

                # čakanje na izravnavo referenčne vrednosti
                self.waitForSettled()

                # izračun in zapis meritve
                HP34401A_string = f"MEASure:{self.measType}{self.dirType}? 10"
                [MeasAverage, stdVar] = self.measurement(self.measParameters["numOfMeas"], measRange = 10)
                self.measParameters["linearMeas"][MeasNum] = MeasAverage
                self.measParameters["linearStdVars"][MeasNum] = stdVar

                # izklop referenčne vrednosti na kalibratorju F5522A
                F5522A_string = 'STBY'
                self.terminal.log(f'IN F5522A: {F5522A_string}')
                self.F5522A.write(F5522A_string)

                self.terminal.log("")
                lref = self.measParameters["linearRefs"][MeasNum]
                lmeas = self.measParameters["linearMeas"][MeasNum]
                unit = self.measParameters["linearUnits"][MeasNum]
                self.graph.update_data([{"Value": lmeas, "Label": unit, "Step": lref}])






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
            unit STRING,
            frequency STRING,
            timestamp DATETIME,
            FOREIGN KEY (calibration_id) REFERENCES calibrations(id)
        )
        """)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS colinearity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calibration_id INTEGER,
                    linear_ref FLOAT,
                    measurement FLOAT,
                    linear_diff FLOAT,
                    linear_std FLOAT,
                    unit STRING,
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

    def log_measurement(self, calibration_id, set_value, calculated_value, ref_set_diff, std, frequency, unit):
        cursor = self.conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO measurements (calibration_id, set_value, calculated_value, ref_set_diff, std, unit, frequency, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (calibration_id, set_value, calculated_value, ref_set_diff, std, unit, frequency, timestamp))

        self.conn.commit()
        print(f"Measurement logged for calibration ID {calibration_id}.")

    def log_linear_refs(self, calibration_id, set_value, calculated_value, ref_set_diff, std, unit):
        cursor = self.conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO colinearity (calibration_id, linear_ref, measurement, linear_diff, linear_std, unit, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (calibration_id, set_value, calculated_value, ref_set_diff, std, unit, timestamp))

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


