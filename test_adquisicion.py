
import csv
import time
import numpy as np
import matplotlib.pyplot as plt

from adquisicion import AdquisicionECG

DURACION = 10
FS_ESTIMADA = 250

ecg = AdquisicionECG(puerto="/dev/ttyACM0", baudrate=115200)
#ecg = AdquisicionECG(puerto="COM3", baudrate=115200)

tiempos = []
valores = []

if not ecg.conectar():
    raise SystemExit("No se pudo conectar con el XIAO.")

try:
    print(f"Registrando durante {DURACION} segundos...")

    inicio = time.perf_counter()

    while time.perf_counter() - inicio < DURACION:
        muestra = ecg.leer_muestra()

        if muestra is not None:
            tiempos.append(time.perf_counter() - inicio)
            valores.append(muestra)

finally:
    ecg.desconectar()

if not valores:
    raise SystemExit("No se recibieron muestras.")

valores_np = np.asarray(valores)

print(f"Muestras recibidas: {len(valores)}")
print(f"Mínimo ADC: {valores_np.min()}")
print(f"Máximo ADC: {valores_np.max()}")
print(f"Media ADC: {valores_np.mean():.2f}")
print(f"Desviación estándar: {valores_np.std():.2f}")

with open("ecg_validacion.csv", "w", newline="") as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(["seg", "data"])
    escritor.writerows(zip(tiempos, valores))

plt.figure(figsize=(12, 4))
plt.plot(tiempos, valores, linewidth=0.8)
plt.xlabel("Tiempo (s)")
plt.ylabel("Lectura ADC")
plt.title("Validación de adquisición XIAO + AD8232")
plt.grid(True)
plt.tight_layout()
plt.show()
