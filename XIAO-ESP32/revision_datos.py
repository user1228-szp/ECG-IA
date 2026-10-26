import serial
import time
import csv
import numpy as np
import matplotlib.pyplot as plt

PUERTO = "COM3"  
BAUDIOS = 115200
DURACION = 50

datos = []
tiempos = []

with serial.Serial(PUERTO, BAUDIOS, timeout=1) as ser:
    ser.reset_input_buffer()
    print("Preparando adquisición...")
    time.sleep(2)

    print("Grabando")
    inicio = time.perf_counter()

    while time.perf_counter() - inicio < DURACION:
        linea = ser.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        try:
            valor = int(linea)
            datos.append(valor)
            tiempos.append(time.perf_counter() - inicio)
        except ValueError:
            continue

if len(datos) < 10:
    raise RuntimeError("Llegaron muy pocas muestras. Revisa el puerto.")

datos = np.array(datos)
tiempos = np.array(tiempos)

print(f"Muestras recibidas: {len(datos)}")
print(f"Mínimo ADC: {datos.min()}")
print(f"Máximo ADC: {datos.max()}")
print(f"Media ADC: {datos.mean():.1f}")
print(f"Desviación estándar: {datos.std():.1f}")
print(f"Tasa media recibida: {len(datos) / DURACION:.1f} muestras/s")

with open("ecg_prueba.csv", "w", newline="") as archivo:
    writer = csv.writer(archivo)
    writer.writerow(["seg", "data"])
    writer.writerows(zip(tiempos, datos))

plt.figure(figsize=(12, 4))
plt.plot(tiempos, datos, linewidth=0.8)
plt.xlabel("Time (s)")
plt.ylabel("Lectura ADC")
plt.title("Validación sensor AD8232")
plt.grid(True)
plt.tight_layout()
plt.show()
