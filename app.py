import os
import time
import tkinter as tk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib
import serial


from adquisicion import AdquisicionECG
from scipy import signal, stats
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

matplotlib.use("TkAgg")

# =====================================================
# CONFIGURACION GENERAL
# =====================================================

FS = 250                   # Frecuencia de muestreo de prueba (Hz)
UPDATE_MS = 100             # Actualizacion de la interfaz (ms)
SAMPLES_PER_UPDATE = max(1, round(FS * UPDATE_MS / 1000))
DATA_FOLDER = "data"


SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

ecg = AdquisicionECG(
    puerto=SERIAL_PORT,
    baudrate=BAUD_RATE
)

#SERIAL_PORT = "COM3"
#BAUD_RATE = 115200
#ser = None

os.makedirs(DATA_FOLDER, exist_ok=True)


recording = False
simulation = False
start_time = None

times = []
values = []

current_time = np.array([])
current_signal = np.array([])
current_fs = FS
current_filename = "Sin archivo"


def generate_sample(t):
    """Generacion de ECG."""
    phase = t % 1.0

    p_wave = 0.12 * np.exp(-((phase - 0.20) / 0.045) ** 2)
    q_wave = -0.12 * np.exp(-((phase - 0.39) / 0.012) ** 2)
    r_wave = 1.00 * np.exp(-((phase - 0.42) / 0.014) ** 2)
    s_wave = -0.25 * np.exp(-((phase - 0.45) / 0.018) ** 2)
    t_wave = 0.30 * np.exp(-((phase - 0.68) / 0.075) ** 2)

    return p_wave + q_wave + r_wave + s_wave + t_wave


def filter_ecg(y, fs):
    """
    Filtra una señal ECG con un pasa banda Butterworth.
    Devuelve una copia procesada; no modifica la señal original.
    """
    y = np.asarray(y, dtype=float)

    if len(y) < 10:
        raise ValueError(
            "La señal es demasiado corta para filtrarla."
        )

    low_cutoff = 0.5
    high_cutoff = 40.0

    if fs <= 2 * low_cutoff:
        raise ValueError(
            "La frecuencia de muestreo es demasiado baja."
        )

    # Mantener el corte superior por debajo de Nyquist.
    high_cutoff = min(high_cutoff, fs * 0.45)

    sos = signal.butter(
        4,
        [low_cutoff, high_cutoff],
        btype="bandpass",
        fs=fs,
        output="sos"
    )

    try:
        filtered = signal.sosfiltfilt(sos, y)
    except ValueError as exc:
        raise ValueError(
            "La señal es demasiado corta para aplicar "
            "el filtrado sin desfase."
        ) from exc

    return filtered



def validate_filter_10s():
    fs = FS
    duration = 10
    t = np.arange(int(fs * duration)) / fs
    clean = np.array([
        generate_sample(sample_time) for sample_time in t
    ])
    clean_reference = clean - np.mean(clean)

    noise_std = 0.015
    noisy = clean + np.random.normal(
        0, noise_std, size=len(clean)
    )
    noisy_centered = noisy - np.mean(noisy)

    try:
        filtered = filter_ecg(noisy, fs)
    except ValueError as exc:
        messagebox.showerror("Error de filtrado", str(exc))
        return

    rmse_noisy = np.sqrt(
        np.mean((noisy_centered - clean_reference) ** 2)
    )
    rmse_filtered = np.sqrt(
        np.mean((filtered - clean_reference) ** 2)
    )

    improvement = (
        (rmse_noisy - rmse_filtered) / rmse_noisy * 100
        if rmse_noisy > 0 else 0.0
    )
##########################################################
    min_distance = int(0.5 * fs)

    peaks_clean, _ = signal.find_peaks(
        clean_reference,
        distance=min_distance,
        prominence=0.5
    )

    peaks_filtered, _ = signal.find_peaks(
        filtered,
        distance=min_distance,
        prominence=0.5
    )
    
    rr_clean = np.diff(t[peaks_clean])
    rr_filtered = np.diff(t[peaks_filtered])

    bpm_clean = (
        60 / np.median(rr_clean)
        if len(rr_clean) > 0 else 0
    )

    bpm_filtered = (
        60 / np.median(rr_filtered)
        if len(rr_filtered) > 0 else 0
    )

    tolerance = 0.10  # 100 milisegundos
    matched_peaks = 0
    used_filtered = set()

    for peak in peaks_clean:
        differences = np.abs(peaks_filtered - peak)

        if len(differences) == 0:
            continue

        nearest_index = int(np.argmin(differences))

        if (
            differences[nearest_index] <= tolerance * fs
            and nearest_index not in used_filtered
        ):
            matched_peaks += 1
            used_filtered.add(nearest_index)

    total_reference_peaks = len(peaks_clean)

    detection_percentage = (
        matched_peaks / total_reference_peaks * 100
        if total_reference_peaks > 0 else 0
    )

    bpm_difference = abs(bpm_clean - bpm_filtered)

#############################
    validation_window = tk.Toplevel(root)
    validation_window.title("Validación del filtro ECG")
    validation_window.geometry("1250x700")
    validation_window.minsize(950, 550)
    validation_window.columnconfigure(0, weight=3)
    validation_window.columnconfigure(1, weight=2)
    validation_window.rowconfigure(0, weight=1)

    graphs_frame = ttk.LabelFrame(
        validation_window,
        text="Comparación de señales"
    )
    graphs_frame.grid(
        row=0, column=0,
        sticky="nsew",
        padx=(10, 5), pady=10
    )
    graphs_frame.columnconfigure(0, weight=1)
    graphs_frame.rowconfigure(0, weight=1)

    validation_fig, (ax_noisy, ax_filtered_val) = plt.subplots(
        2, 1, figsize=(7, 6), sharex=True
    )
    validation_fig.subplots_adjust(
        left=0.12, right=0.97,
        top=0.93, bottom=0.10,
        hspace=0.38
    )

    ax_noisy.plot(
        t, noisy_centered,
        linewidth=0.8,
        label="ECG con ruido"
    )
    ax_noisy.plot(
        t, clean_reference,
        "--",
        linewidth=1.0,
        label="Referencia limpia"
    )
    
    
    
    ax_noisy.plot(
    t[peaks_clean],
    clean_reference[peaks_clean],
    "ro",
    markersize=4,
    label="Picos R de referencia"
    )
    
    
    
    ax_noisy.set_title("Señal original")
    ax_noisy.set_ylabel("Amplitud (u.a.)")
    ax_noisy.grid(True)
    ax_noisy.legend(fontsize=8)


    ax_filtered_val.plot(
        t, filtered,
        linewidth=0.8,
        label="ECG filtrado"
    )
    ax_filtered_val.plot(
        t, clean_reference,
        "--",
        linewidth=1.0,
        label="Referencia limpia"
    )
    
    
    ax_filtered_val.plot(
    t[peaks_filtered],
    filtered[peaks_filtered],
    "ro",
    markersize=4,
    label="Picos R detectados"
    )
    
    
    
    ax_filtered_val.set_title("Señal filtrada")
    ax_filtered_val.set_xlabel("Tiempo (s)")
    ax_filtered_val.set_ylabel("Amplitud (u.a.)")
    ax_filtered_val.grid(True)
    ax_filtered_val.legend(fontsize=8)

    validation_canvas = FigureCanvasTkAgg(
        validation_fig,
        master=graphs_frame
    )
    validation_canvas.draw()
    validation_canvas.get_tk_widget().grid(
        row=0, column=0, sticky="nsew",
        padx=5, pady=5
    )

    results_frame = ttk.LabelFrame(
        validation_window,
        text="Resultados de la validación"
    )
    results_frame.grid(
        row=0, column=1,
        sticky="nsew",
        padx=(5, 10), pady=10
    )
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(0, weight=1)

    results_text_validation = tk.Text(
        results_frame,
        wrap="word",
        font=("Consolas", 10),
        padx=10,
        pady=10
    )
    results_text_validation.grid(
        row=0, column=0,
        sticky="nsew",
        padx=5, pady=5
    )

    scrollbar = ttk.Scrollbar(
        results_frame,
        orient="vertical",
        command=results_text_validation.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    results_text_validation.configure(
        yscrollcommand=scrollbar.set
    )

    if improvement >= 0:
        conclusion = f"Reducción del error: {improvement:.2f}%"
    else:
        conclusion = f"Aumento del error: {abs(improvement):.2f}%"


    results = (
        "VALIDACIÓN DEL FILTRO ECG\n"
        "==============================\n\n"
        f"Duración: {duration} s\n"
        f"Frecuencia de muestreo: {fs} Hz\n"
        f"Ruido añadido (desv. estándar): {noise_std:.5f}\n\n"
        "ERROR RMS RESPECTO A LA REFERENCIA\n"
        "----------------------------------\n"
        f"Con ruido:   {rmse_noisy:.5f}\n"
        f"Filtrada:    {rmse_filtered:.5f}\n\n"

        "----------------------------------\n"
        "DETECCIÓN DE PICOS R\n"
                        "--------------------\n"
                        f"Picos en referencia: {total_reference_peaks}\n"
                        f"Picos detectados: {len(peaks_filtered)}\n"
                        f"Picos coincidentes: {matched_peaks}\n"
                        f"Coincidencia respecto a referencia: "
                        f"{detection_percentage:.2f}%\n\n"
                        "FRECUENCIA CARDÍACA ESTIMADA\n"
                        "---------------------------\n"
                        f"Referencia: {bpm_clean:.2f} BPM\n"
                        f"Filtrada: {bpm_filtered:.2f} BPM\n"
                        f"Diferencia absoluta: {bpm_difference:.2f} BPM\n\n"
                
        "COMPARACIÓN\n"
        "-----------\n"
        f"{conclusion}\n\n"
        "INTERPRETACIÓN\n"
        "--------------\n"
        "El RMSE mide la diferencia entre cada señal "
        "y la referencia limpia. Una reducción indica "
        "que la señal filtrada se aproxima más a esa "
        "referencia en esta simulación.\n\n"
        "LIMITACIONES\n"
        "------------\n"
        "Esta prueba utiliza una señal sintética. "
        "No demuestra por sí sola que el filtro preserve "
        "todas las características de un ECG real ni "
        "constituye una validación clínica."
    )

    results_text_validation.insert("1.0", results)
    results_text_validation.configure(state="disabled")
    
    def close_validation():
        plt.close(validation_fig)
        validation_window.destroy()

    validation_window.protocol(
        "WM_DELETE_WINDOW",
        close_validation
    )



def validate_filter():
    """Valida toda la señal cargada o adquirida."""

    # 1. Obtener la señal completa de la aplicación
    if current_signal is None or len(current_signal) == 0:
        messagebox.showwarning(
            "Sin señal",
            "Primero adquiere una señal o carga un archivo CSV."
        )
        return

    raw = np.asarray(current_signal, dtype=float).ravel()
    fs = current_fs if current_fs else FS

    if fs <= 80:
        messagebox.showerror(
            "Frecuencia insuficiente",
            "La frecuencia de muestreo debe ser mayor que 80 Hz "
            "para aplicar este filtro de 0.5 a 40 Hz."
        )
        return

    # Usar el tiempo original si corresponde a todas las muestras
    if current_time is not None and len(current_time) == len(raw):
        t = np.asarray(current_time, dtype=float)
        t = t - t[0]
    else:
        t = np.arange(len(raw)) / fs

    duration = len(raw) / fs

    # 2. Filtrar la señal completa
    try:
        filtered = filter_ecg(raw, fs)
    except (ValueError, TypeError) as exc:
        messagebox.showerror("Error de filtrado", str(exc))
        return

    # 3. Calcular diferencia entre señal original y filtrada
    rmse_difference = np.sqrt(
        np.mean((raw - filtered) ** 2)
    )

    # 4. Detectar picos R en ambas señales
    min_distance = max(1, int(0.5 * fs))

    prominence_raw = max(
        0.5 * np.std(raw),
        1e-9
    )
    prominence_filtered = max(
        0.5 * np.std(filtered),
        1e-9
    )

    peaks_raw, _ = signal.find_peaks(
        raw,
        distance=min_distance,
        prominence=prominence_raw
    )

    peaks_filtered, _ = signal.find_peaks(
        filtered,
        distance=min_distance,
        prominence=prominence_filtered
    )

    # 5. Calcular BPM a partir de los intervalos R-R
    rr_raw = np.diff(t[peaks_raw])
    rr_filtered = np.diff(t[peaks_filtered])

    bpm_raw = (
        60 / np.median(rr_raw)
        if len(rr_raw) > 0 else 0
    )

    bpm_filtered = (
        60 / np.median(rr_filtered)
        if len(rr_filtered) > 0 else 0
    )

    # 6. Comparar las posiciones de los picos
    tolerance = 0.10  # 100 ms
    matched_peaks = 0
    used_filtered = set()

    for peak in peaks_raw:
        if len(peaks_filtered) == 0:
            break

        differences = np.abs(peaks_filtered - peak)
        nearest = int(np.argmin(differences))

        if (
            differences[nearest] <= tolerance * fs
            and nearest not in used_filtered
        ):
            matched_peaks += 1
            used_filtered.add(nearest)

    matching_percentage = (
        matched_peaks / len(peaks_raw) * 100
        if len(peaks_raw) > 0 else 0
    )

    bpm_difference = abs(bpm_raw - bpm_filtered)

    # ==========================================
    # 7. Crear ventana independiente
    # ==========================================
    validation_window = tk.Toplevel(root)
    validation_window.title("Validación del filtro ECG")
    validation_window.geometry("1250x700")
    validation_window.minsize(950, 550)

    validation_window.columnconfigure(0, weight=3)
    validation_window.columnconfigure(1, weight=2)
    validation_window.rowconfigure(0, weight=1)

    # ==========================================
    # COLUMNA IZQUIERDA: GRÁFICAS
    # ==========================================
    graphs_frame = ttk.LabelFrame(
        validation_window,
        text="Señal completa"
    )
    graphs_frame.grid(
        row=0, column=0,
        sticky="nsew",
        padx=(10, 5), pady=10
    )
    graphs_frame.columnconfigure(0, weight=1)
    graphs_frame.rowconfigure(0, weight=1)

    fig, (ax_original, ax_filtered) = plt.subplots(
        2, 1, figsize=(7, 6), sharex=True
    )
    fig.subplots_adjust(
        left=0.12, right=0.97,
        top=0.93, bottom=0.10,
        hspace=0.38
    )

    # Señal original
    ax_original.plot(
        t, raw,
        linewidth=0.8,
        label="ECG original"
    )
    ax_original.plot(
        t[peaks_raw],
        raw[peaks_raw],
        "ro",
        markersize=3,
        label="Picos detectados"
    )
    ax_original.set_title("Señal original")
    ax_original.set_ylabel("Amplitud")
    ax_original.grid(True)
    ax_original.legend(fontsize=8)

    # Señal filtrada
    ax_filtered.plot(
        t, filtered,
        linewidth=0.8,
        label="ECG filtrado"
    )
    ax_filtered.plot(
        t[peaks_filtered],
        filtered[peaks_filtered],
        "ro",
        markersize=3,
        label="Picos detectados"
    )
    ax_filtered.set_title("Señal filtrada")
    ax_filtered.set_xlabel("Tiempo (s)")
    ax_filtered.set_ylabel("Amplitud")
    ax_filtered.grid(True)
    ax_filtered.legend(fontsize=8)

    canvas_validation = FigureCanvasTkAgg(
        fig, master=graphs_frame
    )
    canvas_validation.draw()
    canvas_validation.get_tk_widget().grid(
        row=0, column=0, sticky="nsew",
        padx=5, pady=5
    )

    # ==========================================
    # COLUMNA DERECHA: RESULTADOS
    # ==========================================
    results_frame = ttk.LabelFrame(
        validation_window,
        text="Resultados del análisis"
    )
    results_frame.grid(
        row=0, column=1,
        sticky="nsew",
        padx=(5, 10), pady=10
    )
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(0, weight=1)

    results_box = tk.Text(
        results_frame,
        wrap="word",
        font=("Consolas", 10),
        padx=10,
        pady=10
    )
    results_box.grid(
        row=0, column=0, sticky="nsew",
        padx=5, pady=5
    )

    scrollbar = ttk.Scrollbar(
        results_frame,
        orient="vertical",
        command=results_box.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    results_box.configure(yscrollcommand=scrollbar.set)

    # 8. Mostrar resultados
    results = (
        "ANÁLISIS DE LA SEÑAL COMPLETA\n"
        "==============================\n\n"
        f"Muestras: {len(raw)}\n"
        f"Duración: {duration:.3f} s\n"
        f"Frecuencia de muestreo: {fs:.2f} Hz\n\n"
        "FILTRADO\n"
        "------------------------------\n"
        f"RMSE original-filtrada: {rmse_difference:.5f}\n\n"
        "DETECCIÓN DE PICOS R\n"
        "------------------------------\n"
        f"Picos en señal original: {len(peaks_raw)}\n"
        f"Picos en señal filtrada: {len(peaks_filtered)}\n"
        f"Picos coincidentes: {matched_peaks}\n"
        f"Coincidencia respecto a original: "
        f"{matching_percentage:.2f}%\n\n"
        "FRECUENCIA CARDÍACA ESTIMADA\n"
        "------------------------------\n"
        f"Original: {bpm_raw:.2f} BPM\n"
        f"Filtrada: {bpm_filtered:.2f} BPM\n"
        f"Diferencia: {bpm_difference:.2f} BPM\n\n"
        "LIMITACIONES\n"
        "------------------------------\n"
        "El RMSE mostrado representa la diferencia entre "
        "la señal original y la filtrada; no mide por sí solo "
        "la reducción del ruido respecto a una referencia limpia.\n"
        "La coincidencia de picos es una comparación aproximada. "
        "La detección debe verificarse visualmente, especialmente "
        "en señales ECG reales."
    )

    results_box.insert("1.0", results)
    results_box.configure(state="disabled")

    # Cerrar la figura al cerrar la ventana
    def close_validation():
        plt.close(fig)
        validation_window.destroy()

    validation_window.protocol(
        "WM_DELETE_WINDOW",
        close_validation
    )


def start_acquisition():
    global recording, simulation, start_time
    global times, values

    if recording:
        return

    if not ecg.conectar():
        status_var.set("Error de conexión con la XIAO.")
        messagebox.showerror(
            "Error de conexión",
            f"No se pudo abrir el puerto {SERIAL_PORT}."
        )
        return

    times = []
    values = []
    start_time = time.perf_counter()
    recording = True
    simulation = False

    status_var.set("Adquiriendo datos reales de la XIAO...")
    acquire_samples()


def acquire_samples():
    if not recording:
        return

    # Leer un bloque pequeño para mantener la interfaz responsiva.
    for _ in range(10):
        if not recording:
            break

        value = ecg.leer_muestra()
        if value is not None:
            elapsed = len(values) / FS
            times.append(elapsed)
            values.append(value)

    update_plot()

    if recording:
        root.after(5, acquire_samples)


def update_plot():
    if recording and values:
        t = np.asarray(times)
        y = np.asarray(values)

        line_signal.set_data(t, y)

        right = max(10.0, t[-1])
        left = max(0.0, right - 10.0)

        ax_signal.set_xlim(left, right)

        ymin = min(-0.5, float(np.min(y)) - 0.1)
        ymax = max(1.2, float(np.max(y)) + 0.1)
        ax_signal.set_ylim(ymin, ymax)

        canvas.draw_idle()


def stop_acquisition():
    global recording, simulation
    global current_time, current_signal, current_fs
    global current_filename

    recording = False
    simulation = False
    ecg.desconectar()

    if times and values:
        current_time = np.asarray(times, dtype=float)
        current_signal = np.asarray(values, dtype=float)
        current_fs = FS
        current_filename = "Adquisición XIAO"

    status_var.set("Adquisición detenida.")

    if values:
        save_signal()



def save_signal():
    if not times or not values:
        messagebox.showwarning(
            "Sin datos",
            "No hay muestras disponibles para guardar."
        )
        return

    contador = 1

    while True:
        filename = (
            f"ecg_{datetime.now().strftime('%Y%m%d')}"
            f"_prueba_{contador}.csv"
        )

        filepath = os.path.join(DATA_FOLDER, filename)

        if not os.path.exists(filepath):
            break

        contador += 1

    df = pd.DataFrame({
        "seg": times,
        "data": values
    })

    df.to_csv(filepath, index=False)

    status_var.set(f"Archivo guardado: {filename}")

    messagebox.showinfo(
        "Saved",
        f"Se guardaron {len(df)} muestras en:\n{filepath}"
    )


def load_signal(filepath):
    global current_time, current_signal
    global current_fs, current_filename

    df = pd.read_csv(filepath)
    df.columns = [str(c).strip().lower() for c in df.columns]

    time_col = next(
        (c for c in ["seg", "t", "time", "tiempo"] if c in df.columns),
        None
    )

    signal_col = next(
        (c for c in ["data", "v", "voltage", "signal",
                     "value", "valor"] if c in df.columns),
        None
    )

    if time_col and signal_col:
        t = pd.to_numeric(df[time_col], errors="coerce").to_numpy()
        y = pd.to_numeric(df[signal_col], errors="coerce").to_numpy()

        valid = np.isfinite(t) & np.isfinite(y)
        t, y = t[valid], y[valid]

        if len(t) < 2:
            raise ValueError("El archivo contiene muy pocas muestras.")

        current_fs = 1.0 / np.median(np.diff(t))

    else:
        df = pd.read_csv(filepath, header=None)

        if df.shape[1] != 1:
            raise ValueError(
                "El CSV debe tener una columna de muestras "
                "o columnas de tiempo y señal."
            )

        y = pd.to_numeric(df.iloc[:, 0], errors="coerce").to_numpy()
        y = y[np.isfinite(y)]

        if len(y) < 2:
            raise ValueError("POCAS MUESTRAS.")

        current_fs = FS
        t = np.arange(len(y)) / current_fs

    if len(y) < 2 or not np.all(np.isfinite(y)):
        raise ValueError("La señal no contiene datos suficientes.")

    if current_fs <= 0 or not np.isfinite(current_fs):
        raise ValueError("ERROR")

    current_time = t
    current_signal = y
    current_filename = os.path.basename(filepath)

    line_signal.set_data(t, y)
    line_filtered.set_data([], [])
    canvas.draw_idle()
    ax_signal.set_xlim(t[0], max(t[-1], t[0] + 1 / current_fs))

    ymin, ymax = float(np.min(y)), float(np.max(y))
    margin = max((ymax - ymin) * 0.1, 0.01)
    ax_signal.set_ylim(ymin - margin, ymax + margin)

    canvas.draw_idle()

    status_var.set(
        f"Cargado: {current_filename} | "
        f"{len(y)} muestras | Fs = {current_fs:.2f} Hz"
    )


def select_file():
    filepath = filedialog.askopenfilename(
        title="Seleccionar señal ECG",
        filetypes=[
            ("Archivos CSV", "*.csv"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not filepath:
        return

    try:
        load_signal(filepath)
    except Exception as exc:
        messagebox.showerror("Error al cargar", str(exc))

def show_analysis_results(text):
    """Muestra los resultados dentro del panel derecho."""
    results_text.config(state="normal")
    results_text.delete("1.0", tk.END)
    results_text.insert("1.0", text)
    results_text.config(state="disabled")
    
# =====================================================
# =====================================================
# =====================================================
# ANALISIS DE LA SEÑAL
# =====================================================
# =====================================================
# =====================================================


def analyze_signal():
    if recording:
        messagebox.showwarning(
            "Adquisición activa",
            "Detén la adquisición antes de analizar la señal."
        )
        return

    if len(current_signal) < 2:
        messagebox.showwarning(
            "Sin señal",
            "Carga un archivo o adquiere una señal primero."
        )
        return

    y = np.asarray(current_signal, dtype=float)
    fs = current_fs
    
    # Filtrar la señal original
    try:
        filtered = filter_ecg(y, fs)
    except ValueError as exc:
        messagebox.showerror("Error de filtrado", str(exc))
        return

    line_filtered.set_data(current_time, filtered)

    ax_filtered.set_xlim(
        current_time[0],
        max(current_time[-1], current_time[0] + 1 / fs)
    )

    ymin = float(np.min(filtered))
    ymax = float(np.max(filtered))
    margin = max((ymax - ymin) * 0.1, 0.01)

    ax_filtered.set_ylim(
        ymin - margin,
        ymax + margin
    )

    canvas.draw_idle()


    canvas.draw_idle()

    # ==============================
    # ANÁLISIS EN EL DOMINIO TEMPORAL
    # ==============================

    mean = np.mean(y)
    std = np.std(y)
    rms = np.sqrt(np.mean(y ** 2))
    peak_to_peak = np.ptp(y)

    zero_crossings = np.count_nonzero(
        (y[:-1] * y[1:]) < 0
    )

    skewness = stats.skew(y) if std > 0 else 0.0
    kurtosis = stats.kurtosis(y) if std > 0 else 0.0

    # ==============================
    # ANÁLISIS EN EL DOMINIO FRECUENCIAL
    # ==============================

    centered = y - mean
    window = np.hanning(len(centered))

    spectrum = np.abs(
        np.fft.rfft(centered * window)
    )

    freqs = np.fft.rfftfreq(
        len(y),
        d=1 / fs
    )

    if len(spectrum) > 1 and np.any(spectrum[1:] > 0):
        dominant_idx = 1 + np.argmax(spectrum[1:])
        dominant_freq = freqs[dominant_idx]
    else:
        dominant_freq = 0.0

    
    filtered_mean = np.mean(filtered)
    filtered_std = np.std(filtered)
    filtered_rms = np.sqrt(np.mean(filtered ** 2))
    filtered_peak_to_peak = np.ptp(filtered)

    # Diferencia RMS entre señal original y filtrada
    rmse = np.sqrt(np.mean((y - filtered) ** 2))
    
    # ==============================
    # PREPARAR RESULTADOS
    # ==============================

    results = (
        f"ARCHIVO\n"
        f"{current_filename}\n\n"

        
        f"DOMINIO TEMPORAL - FILTRADA\n"
        f"Media: {filtered_mean:.5f}\n"
        f"Desviación estándar: {filtered_std:.5f}\n"
        f"Pico a pico: {filtered_peak_to_peak:.5f}\n"
        f"RMS: {filtered_rms:.5f}\n\n"

        f"COMPARACIÓN\n"
        f"RMSE original-filtrada: {rmse:.5f}\n\n"

        
        f"DATOS DE ADQUISICIÓN\n"
        f"Muestras: {len(y)}\n"
        f"Duración: {(len(y) - 1) / fs:.3f} s\n"
        f"Frecuencia de muestreo: {fs:.2f} Hz\n\n"

        f"DOMINIO TEMPORAL\n"
        f"Media: {mean:.5f}\n"
        f"Desviación estándar: {std:.5f}\n"
        f"Máximo: {np.max(y):.5f}\n"
        f"Mínimo: {np.min(y):.5f}\n"
        f"Pico a pico: {peak_to_peak:.5f}\n"
        f"RMS: {rms:.5f}\n"
        f"Cruces por cero: {zero_crossings}\n"
        f"Asimetría: {skewness:.5f}\n"
        f"Curtosis: {kurtosis:.5f}\n\n"

        f"DOMINIO FRECUENCIAL\n"
        f"Frecuencia dominante: {dominant_freq:.2f} Hz\n\n"

        "Resultados descriptivos; no constituyen "
        "un diagnóstico médico."
    )

    # Mostrar resultados en la columna derecha.
    show_analysis_results(results)

    # ==============================
    # ACTUALIZAR FFT EN LA MISMA VENTANA
    # ==============================

    line_spectrum.set_data(freqs, spectrum)

    ax_spectrum.set_xlim(0, fs / 2)

    positive_spectrum = spectrum[spectrum > 0]

    if len(positive_spectrum):
        ymin = max(float(np.min(positive_spectrum)) * 0.5, 1e-12)
        ymax = float(np.max(positive_spectrum)) * 1.2

        if ymax <= ymin:
            ymax = ymin * 10

        ax_spectrum.set_ylim(ymin, ymax)
    else:
        ax_spectrum.set_ylim(0, 1)

    canvas_spectrum.draw_idle()

    status_var.set(
        f"Análisis completado: {current_filename}"
    )


# =====================================================
# =====================================================
# =====================================================
# 
# INTERFAZ GRAFICA
# 
# =====================================================
# =====================================================
# =====================================================

root = tk.Tk()
root.title("ECG IA - Desarrollo")
root.geometry("1250x750")
root.minsize(900, 550)

toolbar = ttk.Frame(root, padding=10)
toolbar.pack(fill="x")

ttk.Button(
    toolbar,
    text="Iniciar prueba",
    command=start_acquisition
).pack(side="left", padx=4)

ttk.Button(
    toolbar,
    text="Detener",
    command=stop_acquisition
).pack(side="left", padx=4)

ttk.Button(
    toolbar,
    text="Cargar CSV",
    command=select_file
).pack(side="left", padx=4)

ttk.Button(
    toolbar,
    text="Analizar",
    command=analyze_signal
).pack(side="left", padx=4)


ttk.Button(
    toolbar,
    text="Validar filtro",
    command=validate_filter
    #command=validate_filter_10s
).pack(side="left", padx=4)

status_var = tk.StringVar(value="Listo. Esperando una señal.")

ttk.Label(
    root,
    textvariable=status_var,
    padding=(10, 4)
).pack(fill="x")

main_frame = ttk.Frame(root, padding=(10, 5))
main_frame.pack(fill="both", expand=True)
main_frame.columnconfigure(0, weight=3)
main_frame.columnconfigure(1, weight=2)
main_frame.rowconfigure(0, weight=1)

signal_frame = ttk.LabelFrame(
    main_frame,
    text="Señal ECG",
    padding=8
)
signal_frame.grid(
    row=0, column=0, sticky="nsew", padx=(0, 5)
)

signal_frame.rowconfigure(0, weight=1)
signal_frame.columnconfigure(0, weight=1)

fig_signal, (ax_signal, ax_filtered) = plt.subplots(
    2, 1,
    figsize=(7, 6),
    sharex=True
)

# Grap original
line_signal, = ax_signal.plot([], [], linewidth=0.8)
ax_signal.set_title("ECG original")
ax_signal.set_ylabel("Amplitud")
ax_signal.grid(True)

#graph 2
line_filtered, = ax_filtered.plot([], [], linewidth=0.8)
ax_filtered.set_title("ECG filtrado")
ax_filtered.set_xlabel("Tiempo (s)")
ax_filtered.set_ylabel("Amplitud")
ax_filtered.grid(True)

fig_signal.tight_layout()

canvas = FigureCanvasTkAgg(
    fig_signal, master=signal_frame
)
canvas.get_tk_widget().grid(
    row=0, column=0, sticky="nsew"
)
canvas.draw()


analysis_frame = ttk.LabelFrame(
    main_frame,
    text="Análisis de la señal",
    padding=8
)
analysis_frame.grid(
    row=0, column=1, sticky="nsew", padx=(5, 0)
)

analysis_frame.columnconfigure(0, weight=1)
analysis_frame.rowconfigure(0, weight=3)
analysis_frame.rowconfigure(1, weight=2)

# RESULTADOS
results_text = tk.Text(
    analysis_frame,
    wrap="word",
    font=("Consolas", 10),
    height=15,
    width=35,
    state="disabled"
)
results_text.grid(
    row=0, column=0, sticky="nsew", pady=(0, 8)
)

# Espectro FFT
fig_spectrum, ax_spectrum = plt.subplots(figsize=(5, 3))

line_spectrum, = ax_spectrum.plot([], [], linewidth=0.9)

ax_spectrum.set_title("Espectro de amplitud (FFT)")
ax_spectrum.set_xlabel("Frecuencia (Hz)")
ax_spectrum.set_ylabel("Magnitud")
ax_spectrum.grid(False)

fig_spectrum.tight_layout()

canvas_spectrum = FigureCanvasTkAgg(
    fig_spectrum, master=analysis_frame
)
canvas_spectrum.get_tk_widget().grid(
    row=1, column=0, sticky="nsew"
)
canvas_spectrum.draw()


def close_app():
    global recording, simulation

    recording = False
    simulation = False
    ecg.desconectar()

    plt.close("all")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
