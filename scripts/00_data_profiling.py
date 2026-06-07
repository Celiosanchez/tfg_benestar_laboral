import pandas as pd
import os
# Si no la tens instal·lada: pip install ydata-profiling
from ydata_profiling import ProfileReport 

print("INICIANT DATA PROFILING GLOBAL (OSMI 2014-2023)")

# Ruta base on tens els teus CSV
DATA_PATH = 'D:/UOC/TFG_2026/dades/'

# Diccionari amb tots els arxius
CSV_FILES = {
    2014: "osmi_survey_2014.csv",
    2016: "osmi_survey_2016.csv",
    2017: "osmi_survey_2017.csv",
    2018: "osmi_survey_2018.csv",
    2019: "osmi_survey_2019.csv",
    2020: "osmi_survey_2020.csv",
    2021: "osmi_survey_2021.csv",
    2022: "osmi_survey_2022.csv",
    2023: "osmi_survey_2023.csv",
}

frames = []

print("Llegint i fusionant arxius...")
# Bucle per llegir cada arxiu i afegir-lo a la llista
for any_enquesta, filename in CSV_FILES.items():
    filepath = os.path.join(DATA_PATH, filename)
    
    if os.path.exists(filepath):
        # low_memory=False evita avisos de tipus de dades barrejats
        df_temp = pd.read_csv(filepath, low_memory=False) 
        
        # Afegim una columna amb l'any perquè l'informe mostri la distribució temporal
        df_temp["_any_enquesta"] = any_enquesta 
        
        frames.append(df_temp)
        print(f" {any_enquesta} carregat: {len(df_temp)} registres.")
    else:
        print(f" Avís: No s'ha trobat l'arxiu {filename} a la ruta {DATA_PATH}")

# Fusionem tots els DataFrames en un de sol
df_total = pd.concat(frames, ignore_index=True)

print(f"\n Dataset global creat: {len(df_total)} registres i {len(df_total.columns)} columnes.")
print(" Generant l'informe de Data Profiling (Això pot trigar uns minuts)...")

# CRÍTIC: Mantenim minimal=True. Si no ho fem, analitzar més de 200 columnes 
# de text lliure farà col·lapsar la memòria RAM de l'ordinador.
profile = ProfileReport(
    df_total, 
    title="OSMI Data Profiling Report (Global 2014-2023)", 
    minimal=True
)

# Guardem l'informe global
arxiu_sortida = "OSMI_Report_Global.html"
profile.to_file(arxiu_sortida)

print(f"\n Informe generat amb èxit! Obre l'arxiu '{arxiu_sortida}' al navegador.")