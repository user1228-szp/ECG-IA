import serial
import matplotlib.pyplot as plt
from collections import deque
from matplotlib.animation import FuncAnimation

PUERTO = "COM6"
BAUDIOS = 115200
VENTANA = 500

datos = deque([0] * VENTANA, maxlen=VENTANA)

ser = serial.Serial(PUERTO, BAUDIOS, timeout=1)
ser.reset_input_buffer()
fig, ax = plt.subplots()
linea, = ax.plot([], [], linewidth=1)

ax.set_ylim(0, 1023)
ax.set_xlim(0, VENTANA)
ax.set_title("Arduino UNO")
ax.set_xlabel("Muestras")
ax.set_ylabel("ADC")

def actualizar(frame):

    while ser.in_waiting:

        lectura = ser.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        if lectura.isdigit():
            datos.append(int(lectura))

    linea.set_data(range(len(datos)), datos)

    return linea,

ani = FuncAnimation(
    fig,
    actualizar,
    interval=20,
    blit=True,
    cache_frame_data=False
)

plt.show()

ser.close()
