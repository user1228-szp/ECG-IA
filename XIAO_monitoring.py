
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from adquisicion import AdquisicionECG

PUERTO = "/dev/ttyACM0"
BAUDIOS = 115200
FS = 250
VENTANA_SEGUNDOS = 5

MAX_MUESTRAS = FS * VENTANA_SEGUNDOS

tiempos = deque(maxlen=MAX_MUESTRAS)
valores = deque(maxlen=MAX_MUESTRAS)

ecg = AdquisicionECG(puerto=PUERTO, baudrate=BAUDIOS)

if not ecg.conectar():
    raise SystemExit("No se pudo conectar con la XIAO.")

inicio = time.perf_counter()
contador = 0
ultimo_reporte = inicio


def actualizar(_):
    global contador, ultimo_reporte

    muestra = ecg.leer_muestra()
    ahora = time.perf_counter()

    if muestra is not None:
        tiempos.append(ahora - inicio)
        valores.append(muestra)
        contador += 1

    if ahora - ultimo_reporte >= 1:
        print(
            f"Muestras recibidas: {contador} | "
            f"Última lectura: {muestra}"
        )
        contador = 0
        ultimo_reporte = ahora

    if tiempos:
        linea.set_data(tiempos, valores)
        ax.set_xlim(max(0, tiempos[-1] - VENTANA_SEGUNDOS),
                    max(VENTANA_SEGUNDOS, tiempos[-1]))

        ymin = min(valores)
        ymax = max(valores)
        margen = max(50, (ymax - ymin) * 0.1)
        ax.set_ylim(ymin - margen, ymax + margen)

    return linea,


fig, ax = plt.subplots(figsize=(10, 4))
linea, = ax.plot([], [], linewidth=0.8)

ax.set_title("On going")
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("Lectura ADC")
ax.grid(True)

ani = FuncAnimation(
    fig,
    actualizar,
    interval=20,
    blit=False,
    cache_frame_data=False
)


def cerrar(_):
    ecg.desconectar()


fig.canvas.mpl_connect("close_event", cerrar)

try:
    plt.show()
finally:
    ecg.desconectar()
