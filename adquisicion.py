import serial
import threading
import time


class AdquisicionECG:
    def __init__(self, puerto="COM3", baudrate=115200):
        self.puerto = puerto
        self.baudrate = baudrate
        self.ser = None
        self.activa = False
        self.hilo = None

    def conectar(self):
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()

            self.ser = serial.Serial(
                port=self.puerto,
                baudrate=self.baudrate,
                timeout=1
            )

            # Esperar el reinicio del microcontrolador
            time.sleep(2)
            self.ser.reset_input_buffer()

            print(f"ECG conectado en {self.puerto}")
            return True

        except serial.SerialException as error:
            self.ser = None
            print(f"Error al conectar el ECG: {error}")
            return False

    def leer_muestra(self):
        """Lee muestra ADC"""
        if self.ser is None or not self.ser.is_open:
            return None

        try:
            linea = self.ser.readline().decode(
                "utf-8", errors="ignore"
            ).strip()

            if not linea or linea == "ECG_START":
                return None

            return int(linea)

        except (ValueError, serial.SerialException):
            return None

    def desconectar(self):
        """Detiene la adquisición y cierra el puerto serial."""
        self.activa = False

        if self.ser is not None and self.ser.is_open:
            self.ser.close()

        self.ser = None
        print("ECG desconectado")
