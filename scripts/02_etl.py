# ==============================================================
# PIPELINE ETL COMPLET
# TFG Benestar Laboral - Celio Sánchez Bañuls
# ==============================================================

import os
import re
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ==============================================================
# 0. CONFIGURACIÓ
# ==============================================================
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Ruta on tens els CSV
DATA_PATH = "data/raw/"

# Fitxers per any
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

# ==============================================================
# 1. EXTRACT - Càrrega dels CSV
# ==============================================================
def extract(csv_files: dict) -> pd.DataFrame:
    """Carrega tots els CSV i els concatena en un únic DataFrame."""
    print("\n FASE EXTRACT")
    frames = []
    for year, filename in csv_files.items():
        path = os.path.join(DATA_PATH, filename)
        if not os.path.exists(path):
            print(f" No trobat: {filename} — saltat")
            continue
        df = pd.read_csv(path, low_memory=False)
        df["_any_enquesta"] = year
        frames.append(df)
        print(f"  {year}: {len(df)} registres, {len(df.columns)} columnes")

    raw = pd.concat(frames, ignore_index=True)
    print(f"\n Total brut: {len(raw)} registres, {len(raw.columns)} columnes")
    return raw

# ==============================================================
# 2. TRANSFORM - Neteja i resolució de l'Schema Drift
# ==============================================================

# --- 2a. Diccionari de mapeig semàntic (resolució Schema Drift AMB SMART MATCH) ---
COLUMN_MAPPING = {
    # Demogràfiques
    "edat": ["Age", "What is your age?", "age"],
    "genere": ["Gender", "What is your gender?", "gender"],
    "pais": ["Country", "What country do you live in?", "country", "What country do you work in?"],
    # Entorn laboral
    "mida_empresa": ["no_employees", "How many employees does your company", "How many employees does your employer"],
    "teletreball": ["remote_work", "work remotely"],
    "es_rol_tech": ["tech_company", "primarily a tech", "related to tech/IT"],
    # Salut mental
    "te_tractament": ["treatment", "sought treatment for a mental health"],
    "te_diagnostic": ["mental_health_condition", "currently have a mental health disorder", "diagnosed with a mental health disorder", "have a mental health condition"],
    "interferencia_laboral": ["work_interfere", "interferes with your work"],
    # Cultura d'empresa
    "facilitat_baixa": ["leave", "medical leave for a mental health"],
    "anonimat": ["anonymity", "care your employer provides", "options for mental health care"],
    # Combinem la pregunta antiga (2014-2016) amb la nova pregunta proxy (2017+)
    "por_represalies": [
        "mental health disorder with your employer would have negative",
        "mental health issue with your employer would have negative",
        "comfortable discussing a mental health issue with your direct supervisor",
        "comfortable discussing a mental health disorder with your direct supervisor"
    ]
}

def resolve_schema_drift(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el mapeig semàntic netejant salts de línia ocults """
    result = pd.DataFrame()
    result["_any_enquesta"] = df["_any_enquesta"]

    for standard_name, variants in COLUMN_MAPPING.items():
        result[standard_name] = pd.Series(dtype='object') 
        
        for variant in variants:
            var_clean = " ".join(str(variant).lower().split())
            
            for col in df.columns:
                col_clean = " ".join(str(col).lower().split())
                if var_clean == col_clean or (len(var_clean) > 5 and var_clean in col_clean):
                    mask = result[standard_name].isna() & df[col].notna()
                    result.loc[mask, standard_name] = df.loc[mask, col]

    print(f" Schema Drift resolt: de {len(df.columns)} → {len(result.columns)} columnes")
    return result

def normalitzar_genere(valor: str) -> str:
    if pd.isna(valor):
        return "No especificat"
    v = str(valor).lower().strip()
    masculins = r"\b(male|man|m|cis male|cis man|mail|mal|make)\b"
    femenins  = r"\b(female|woman|f|cis female|cis woman|femail|femake)\b"
    if re.search(masculins, v):
        return "Masculí"
    elif re.search(femenins, v):
        return "Femení"
    else:
        return "Altres/No-Binari"

def normalitzar_edat(valor) -> int | None:
    try:
        edat = int(float(valor))
        return edat if 18 <= edat <= 75 else None
    except (ValueError, TypeError):
        return None

def franja_edat(edat) -> str:
    if pd.isna(edat):
        return "Desconegut"
    edat = int(edat)
    if edat < 25:    return "18-24"
    elif edat < 35:  return "25-34"
    elif edat < 45:  return "35-44"
    elif edat < 55:  return "45-54"
    else:            return "55+"

def normalitzar_booleans(valor) -> str:
    if pd.isna(valor):
        return "No respon/Desconegut"
    v = str(valor).strip().lower()
    if v in ['yes', '1', '1.0', 'true', 'sí', 'some of them']:
        return 'Yes'
    elif v in ['no', '0', '0.0', 'false']:
        return 'No'
    else:
        return 'Maybe/Not Sure'

def transform(raw: pd.DataFrame) -> pd.DataFrame:
    print("\n FASE TRANSFORM")

    df = resolve_schema_drift(raw)

    df["edat_num"] = df["edat"].apply(normalitzar_edat)
    df["edat_franja"] = df["edat_num"].apply(franja_edat)
    invalids = df["edat_num"].isna().sum()
    print(f" Edat: {invalids} registres invàlids eliminats")

    df["genere"] = df["genere"].apply(normalitzar_genere)
    print(f" Gènere normalitzat: {df['genere'].value_counts().to_dict()}")

    cols_a_booleans = ['te_tractament', 'por_represalies']
    for col in cols_a_booleans:
        if col in df.columns:
            df[col] = df[col].apply(normalitzar_booleans)
            
    # L'INVERSIÓ LÒGICA PER AL 2017+ 
    # Com que del 2017 endavant fem servir "Estàs còmode parlant-ho?", hem d'invertir els valors.
    # Si deien "Yes" (Estic còmode) -> Ho passem a "No" (No tinc por).
    if "por_represalies" in df.columns:
        mask_inversio = df["_any_enquesta"] >= 2017
        mapa_invers = {'Yes': 'No', 'No': 'Yes', 'Maybe/Not Sure': 'Maybe/Not Sure'}
        valors_invertits = df.loc[mask_inversio, 'por_represalies'].map(mapa_invers)
        df.loc[mask_inversio, 'por_represalies'] = valors_invertits.fillna(df.loc[mask_inversio, 'por_represalies'])

    print(" Variables booleanes estandarditzades (i invertides per al 2017+).")

    cols_categoriques = [
        "pais", "mida_empresa", "teletreball", "es_rol_tech",
        "te_tractament", "te_diagnostic", "interferencia_laboral",
        "facilitat_baixa", "anonimat", "por_represalies"
    ]
    for col in cols_categoriques:
        if col in df.columns:
            df[col] = df[col].fillna("No respon/Desconegut")

    print(f" Valors nuls imputats en {len(cols_categoriques)} columnes")
    print(f" Dataset net: {len(df)} registres, {len(df.columns)} columnes")
    return df

# ==============================================================
# 3. ENRIQUIMENT - Generació de dades sintètiques (Mock Data)
# ==============================================================
def enriquir(df: pd.DataFrame) -> pd.DataFrame:
    """Injecta variables organitzatives generades sintèticament."""
    print("\n FASE ENRIQUIMENT (Mock Data)")
    np.random.seed(42)  # Reproductibilitat
    n = len(df)

    # Salari anual: distribució Normal N(65000, 15000²) en EUR
    df["salari_anual"] = np.random.normal(loc=65_000, scale=15_000, size=n)
    df["salari_anual"] = df["salari_anual"].clip(25_000, 150_000).round(2)

    # Hores extres setmanals: distribució Poisson P(λ=3)
    df["hores_extres_setmanals"] = np.random.poisson(lam=3, size=n)

    # Departament: selecció ponderada
    departaments = ["Backend", "Frontend", "DevOps", "Data/ML", "HR/Management", "QA/Testing"]
    pesos_dept   = [0.30,      0.25,       0.20,     0.12,      0.08,             0.05]
    df["departament"] = np.random.choice(departaments, size=n, p=pesos_dept)

    # Nota de rendiment: discreta 1-5, distribució realista
    df["nota_rendiment"] = np.random.choice(
        [1, 2, 3, 4, 5], size=n, p=[0.05, 0.10, 0.30, 0.35, 0.20]
    )

    print(f" Salari: mitjana={df['salari_anual'].mean():.0f}€")
    print(f" Hores extres: mitjana={df['hores_extres_setmanals'].mean():.1f}h/setmana")
    print(f" Departaments: {df['departament'].value_counts().to_dict()}")
    print(f" Rendiment: {df['nota_rendiment'].value_counts().sort_index().to_dict()}")
    return df

# ==============================================================
# 4. LOAD - Càrrega al Data Warehouse (Neon PostgreSQL)
# ==============================================================
def load(df: pd.DataFrame):
    """Prepara l'Esquema en Estrella a Neon seguint l'ordre de les FK."""
    print("\nFASE LOAD")

    with engine.connect() as conn:

        # --- dim_temps ---
        anys = df["_any_enquesta"].unique()
        for any_val in sorted(anys):
            periode = "Pre-COVID" if any_val < 2020 else "Post-COVID"
            conn.execute(text("""
                INSERT INTO dim_temps (any_enquesta, periode)
                VALUES (:any, :periode)
                ON CONFLICT (any_enquesta) DO NOTHING
            """), {"any": int(any_val), "periode": periode})
        print(f" dim_temps: {len(anys)} anys inserits")

        # Mapa any → id_temps
        res = conn.execute(text("SELECT id_temps, any_enquesta FROM dim_temps"))
        map_temps = {row[1]: row[0] for row in res}

        # --- dim_demografia ---
        demo_cols = ["edat_franja", "genere", "pais"]
        dim_demo = df[demo_cols].drop_duplicates().reset_index(drop=True)
        demo_ids = {}
        for _, row in dim_demo.iterrows():
            r = conn.execute(text("""
                INSERT INTO dim_demografia (edat_franja, genere, pais)
                VALUES (:ef, :g, :p) RETURNING id_demografia
            """), {"ef": row.edat_franja, "g": row.genere, "p": str(row.pais)[:50]})
            demo_ids[tuple(row)] = r.fetchone()[0]
        print(f" dim_demografia: {len(demo_ids)} combinacions úniques")

       # --- dim_entorn_laboral ---
        entorn_cols = ["departament", "mida_empresa", "teletreball", "es_rol_tech"]
        
        # 1. BLINDATGE: Omplim els nuls amb "Desconegut" i forcem a text pur
        for col in entorn_cols:
            df[col] = df[col].fillna("Desconegut").astype(str).str.strip()
            
        # 2. Creem les combinacions úniques per a la dimensió
        dim_entorn = df[entorn_cols].drop_duplicates().reset_index(drop=True)
        
        entorn_ids = {}
        for _, row in dim_entorn.iterrows():
            r = conn.execute(text("""
                INSERT INTO dim_entorn_laboral
                    (departament, mida_empresa, teletreball, rol_tecnic)
                VALUES (:d, :m, :t, :r) RETURNING id_entorn
            """), {
                "d": row["departament"], 
                "m": row["mida_empresa"][:50],
                "t": row["teletreball"][:10], 
                "r": row["es_rol_tech"][:50]
            })
            entorn_ids[tuple(row)] = r.fetchone()[0]
            
        # 3. ASSIGNACIÓ SEGURA: Assignem l'ID a la taula de fets principal
        df['id_entorn'] = df[entorn_cols].apply(tuple, axis=1).map(entorn_ids)
        
        print(f" dim_entorn_laboral: {len(entorn_ids)} combinacions úniques")
        print(f" Comprovació fets sense id_entorn: {df['id_entorn'].isna().sum()} nuls")

        # --- dim_salut_mental ---
        salut_cols = ["te_diagnostic", "te_tractament", "interferencia_laboral"]
        dim_salut = df[salut_cols].drop_duplicates().reset_index(drop=True)
        salut_ids = {}
        for _, row in dim_salut.iterrows():
            r = conn.execute(text("""
                INSERT INTO dim_salut_mental
                    (diagnostic_confirmat, tractament_actiu, interferencia_laboral)
                VALUES (:d, :t, :i) RETURNING id_salut
            """), {
                "d": str(row.te_diagnostic)[:100],
                "t": str(row.te_tractament)[:100],
                "i": str(row.interferencia_laboral)[:100]
            })
            salut_ids[tuple(row)] = r.fetchone()[0]
        print(f" dim_salut_mental: {len(salut_ids)} combinacions úniques")

        # --- dim_cultura_empresa ---
        cultura_cols = ["facilitat_baixa", "anonimat", "por_represalies"]
        dim_cultura = df[cultura_cols].drop_duplicates().reset_index(drop=True)
        cultura_ids = {}
        for _, row in dim_cultura.iterrows():
            r = conn.execute(text("""
                INSERT INTO dim_cultura_empresa
                    (facilitat_baixa, anonimat_recursos, por_represalies)
                VALUES (:f, :a, :p) RETURNING id_cultura
            """), {
                "f": str(row.facilitat_baixa)[:100],
                "a": str(row.anonimat)[:100],
                "p": str(row.por_represalies)[:100]
            })
            cultura_ids[tuple(row)] = r.fetchone()[0]
        print(f" dim_cultura_empresa: {len(cultura_ids)} combinacions úniques")

        # --- fets_rendiment_benestar ---
        fets_inserits = 0
        batch = []
        for _, row in df.iterrows():
            batch.append({
                "id_temps":    map_temps.get(row["_any_enquesta"]),
                "id_demo":     demo_ids.get((row["edat_franja"], row["genere"], row["pais"])),
                "id_entorn":   entorn_ids.get((row["departament"], row["mida_empresa"], row["teletreball"], row["es_rol_tech"])),
                "id_salut":    salut_ids.get((row["te_diagnostic"], row["te_tractament"], row["interferencia_laboral"])),
                "id_cultura":  cultura_ids.get((row["facilitat_baixa"], row["anonimat"], row["por_represalies"])),
                "salari":      float(row["salari_anual"]),
                "hores":       int(row["hores_extres_setmanals"]),
                "rendiment":   int(row["nota_rendiment"])
            })

        conn.execute(text("""
            INSERT INTO fets_rendiment_benestar
                (id_temps, id_demografia, id_entorn, id_salut, id_cultura,
                 salari_anual, hores_extres_setmanals, nota_rendiment)
            VALUES
                (:id_temps, :id_demo, :id_entorn, :id_salut, :id_cultura,
                 :salari, :hores, :rendiment)
        """), batch)

        fets_inserits = len(batch)
        conn.commit()
        print(f" fets_rendiment_benestar: {fets_inserits} registres inserits")

    print("\nLOAD completat! Data Warehouse complet a Neon.")

# ==============================================================
# 5. EXPORTACIÓ CSV (Single Source of Truth)
# ==============================================================
def exportar_csv(df: pd.DataFrame):
    """Exporta el dataset net com a arxiu mestre."""
    output_path = "data/osmi_unificat_NET_SINTETIC.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n Dataset exportat: {output_path}")
    print(f"   {len(df)} registres × {len(df.columns)} variables")

# ==============================================================
# MAIN - Execució del pipeline
# ==============================================================
if __name__ == "__main__":
    print("  PIPELINE ETL - TFG Benestar Laboral")

    raw_df       = extract(CSV_FILES)
    clean_df     = transform(raw_df)
    enriched_df  = enriquir(clean_df)
    exportar_csv(enriched_df)
    load(enriched_df)

    print("\n Pipeline ETL finalitzat correctament!")