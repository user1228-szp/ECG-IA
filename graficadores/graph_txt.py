import numpy as np
import matplotlib.pyplot as plt

archivo_txt = r"data\01.txt"

frecuencia = 100
data = np.loadtxt(archivo_txt)
tiempo = np.arange(len(data)) / frecuencia

plt.figure(figsize=(12, 5))
plt.plot(tiempo, data, linewidth=0.8)
plt.title("Señal")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.show()
