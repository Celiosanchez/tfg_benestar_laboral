import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ==============================================================
# CONFIGURACIÓ DE LA CONNEXIÓ
# ==============================================================
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# ==============================================================
# DEFINICIÓ DE L'ESQUEMA SQL (DDL)
# ==============================================================
sql_creacio_taules = """
-- 0. NETEJA: Esborrem les taules si ja existeixen 
-- (L'ordre és molt important: primer la de fets, després les dimensions)
DROP TABLE IF EXISTS fets_rendiment_benestar CASCADE;
DROP TABLE IF EXISTS dim_temps CASCADE;
DROP TABLE IF EXISTS dim_demografia CASCADE;
DROP TABLE IF EXISTS dim_entorn_laboral CASCADE;
DROP TABLE IF EXISTS dim_salut_mental CASCADE;
DROP TABLE IF EXISTS dim_cultura_empresa CASCADE;

-- 1. CREACIÓ DE LES TAULES DE DIMENSIONS

CREATE TABLE dim_temps (
    id_temps SERIAL PRIMARY KEY,
    any_enquesta INT NOT NULL UNIQUE, -- UNIQUE és obligatori pel "ON CONFLICT" de l'ETL
    periode VARCHAR(20)
);

CREATE TABLE dim_demografia (
    id_demografia SERIAL PRIMARY KEY,
    edat_franja VARCHAR(20),
    genere VARCHAR(20),
    pais VARCHAR(50)
);

CREATE TABLE dim_entorn_laboral (
    id_entorn SERIAL PRIMARY KEY,
    departament VARCHAR(50),
    mida_empresa VARCHAR(50),
    teletreball VARCHAR(10),
    rol_tecnic VARCHAR(50)
);

CREATE TABLE dim_salut_mental (
    id_salut SERIAL PRIMARY KEY,
    diagnostic_confirmat VARCHAR(100),
    tractament_actiu VARCHAR(100),
    interferencia_laboral VARCHAR(100)
);

CREATE TABLE dim_cultura_empresa (
    id_cultura SERIAL PRIMARY KEY,
    facilitat_baixa VARCHAR(100),
    anonimat_recursos VARCHAR(100),
    por_represalies VARCHAR(100)
);

-- 2. CREACIÓ DE LA TAULA DE FETS (Taula Central)

CREATE TABLE fets_rendiment_benestar (
    id_fet SERIAL PRIMARY KEY,
    id_temps INT REFERENCES dim_temps(id_temps),
    id_demografia INT REFERENCES dim_demografia(id_demografia),
    id_entorn INT REFERENCES dim_entorn_laboral(id_entorn),
    id_salut INT REFERENCES dim_salut_mental(id_salut),
    id_cultura INT REFERENCES dim_cultura_empresa(id_cultura),
    salari_anual DECIMAL(12, 2),
    hores_extres_setmanals INT,
    nota_rendiment INT
);
"""

# ==============================================================
# EXECUCIÓ CAP A NEON
# ==============================================================
print(" Connectant a Neon i configurant el Data Warehouse...")

try:
    # Utilitzem engine.begin() perquè apliqui els canvis de cop (commit automàtic)
    with engine.begin() as conn:
        conn.execute(text(sql_creacio_taules))
    print(" L'Esquema en Estrella s'ha creat correctament a PostgreSQL.")
    print("   Ja es pot executar el script ETL per omplir les taules de dades.")
except Exception as e:
    print(f" Error al crear les taules: {e}")