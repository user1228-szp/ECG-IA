
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox

CARPETA_DATA = Path("data")

def seleccionar_y_graficar():
    archivo = filedialog.askopenfilename(
        title="Selecciona un archivo TXT",
        initialdir=CARPETA_DATA.resolve(),
        filetypes=[("Archivos de texto", "*.txt")]
    )

    if not archivo:
        return

    try:
        datos = np.loadtxt(archivo)

        if datos.ndim > 1:
            datos = datos[:, 0]

        frecuencia = 100  # Cambiar según tu señal

        tiempo = np.arange(len(datos)) / frecuencia

        plt.figure(figsize=(12, 5))
        plt.plot(tiempo, datos, linewidth=0.8)
        plt.title(f"Señal: {Path(archivo).name}")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Amplitud")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    except Exception as error:
        messagebox.showerror(
            "Error al leer el archivo",
            str(error)
        )

ventana = tk.Tk()
ventana.title("Visualizador de señales")
ventana.geometry("350x150")

etiqueta = tk.Label(
    ventana,
    text="Visualizador de señales TXT",
    font=("Arial", 12)
)
etiqueta.pack(pady=15)

boton = tk.Button(
    ventana,
    text="Seleccionar archivo y graficar",
    command=seleccionar_y_graficar,
    font=("Arial", 10)
)
boton.pack(pady=10)
ventana.mainloop()
