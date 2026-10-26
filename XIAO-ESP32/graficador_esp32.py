import serial
import matplotlib.pyplot as plt
from collections import deque
from matplotlib.animation import FuncAnimation


PUERTO = "COM3"
BAUDIOS = 115200
VENTANA = 500

datos = deque([0] * VENTANA, maxlen=VENTANA)
ser = serial.Serial(PUERTO, BAUDIOS, timeout=1)
ser.reset_input_buffer()

fig, ax = plt.subplots()
linea, = ax.plot(range(VENTANA), list(datos), linewidth=1)

ax.set_title("ECG - Adquisición en tiempo real")
ax.set_xlabel("Muestras")
ax.set_ylabel("Valor ADC")
ax.set_xlim(0, VENTANA - 1)
ax.set_ylim(0, 4095)
ax.grid(True)


def actualizar(_):
    nuevas = []

    for _ in range(50):
        lectura = ser.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        if lectura.isdigit():
            nuevas.append(int(lectura))

    for valor in nuevas:
        datos.append(valor)

    linea.set_ydata(list(datos))
    return linea,


ani = FuncAnimation(
    fig,
    actualizar,
    interval=50,
    blit=True,
    cache_frame_data=False
)

try:
    plt.show()
finally:
    ser.close()
