
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

archivo = filedialog.askopenfilename(
    title="Selecciona tu archivo CSV",
    filetypes=[("Archivos CSV", "*.csv")]
)

root.destroy()

if archivo:
    df = pd.read_csv(archivo)
    df.columns = df.columns.str.strip().str.lower()

    if "seg" not in df.columns or "data" not in df.columns:
        print("Error en columnas, se tiene:", df.columns.tolist())
    else:
        df["seg"] = pd.to_numeric(df["seg"], errors="coerce")
        df["data"] = pd.to_numeric(df["data"], errors="coerce")
        df = df.dropna(subset=["seg", "data"])

        plt.figure(figsize=(14, 5))
        plt.plot(df["seg"], df["data"], linewidth=0.8)
        plt.title("Señal")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Amplitud")
        plt.grid(True)
        plt.tight_layout()
        print(f"Datos: {len(df)}")
        print(f"Inicio: {df['seg'].min()} s")
        print(f"Fin: {df['seg'].max()} s")
        plt.show()

else:
    print("Error")
