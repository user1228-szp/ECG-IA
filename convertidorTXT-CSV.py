
import pandas as pd
import numpy as np

archivo_txt = r"data\01.txt"
archivo_csv = r"data\p5.csv"
intervalo = 0.004  

data = np.loadtxt(archivo_txt)

df = pd.DataFrame({
    "seg": np.arange(len(data)) * intervalo,
    "data": data
})

# Guardar como CSV
df.to_csv(archivo_csv, index=False)

print(f"Done, saved as: {archivo_csv}")
print(df.head())
