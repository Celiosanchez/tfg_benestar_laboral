# TFG: Disseny i implementació d'una arquitectura Business Intelligence End-to-End per a l'anàlisi i predicció del benestar laboral en el sector tecnològic.

Aquest repositori conté el codi font, els models de dades i els quadres de comandament desenvolupats per al Treball Final de Grau (TFG) del grau en Enginyeria Informàtica (Business Intelligence) de la Universitat Oberta de Catalunya (UOC).

## Objectiu del Projecte
El projecte proposa una arquitectura de dades *End-to-End* per mesurar, analitzar i predir l'impacte del *burnout* i la salut mental en el compte de resultats de les empreses tecnològiques. Aquest sistema quantifica mètriques de RRHH com el **Cost de Pèrdua de Productivitat (CPP)** i el **Risc de Fuga de Talent**, combinant dades clíniques (OSMI) amb dades organitzatives sintètiques.

## Stack Tecnològic
*   **Extracció, Transformació i Càrrega (ETL):** Python (Pandas, NumPy, ydata-profiling).
*   **Base de Dades / Data Warehouse:** PostgreSQL (Arquitectura Serverless a Neon) modelat en Esquema en Estrella (Star Schema).
*   **Machine Learning:** Scikit-Learn (Random Forest Classifier).
*   **Business Intelligence / Visualització:** Microsoft Power BI (DAX).

## Estructura del Repositori
L'ecosistema d'scripts està dividit en 5 mòduls seqüencials:
1.  `00_data_profiling.py`: Anàlisi exploratòria i diagnòstic de qualitat de dades (EDA).
2.  `01_Crea_Database.py`: Definició de l'esquema DDL relacional a la base de dades remota.
3.  `02_etl.py`: Motor d'integració principal que resol l'Schema Drift històric, neteja els registres i hi injecta distribucions probabilístiques (Mock Data).
4.  `03_MachineLearning.py`: Entrenament del model predictiu i extracció del *Feature Importance* (importància de l'anonimat).
5.  `04_PoC_MachineLearning.py`: Prova de Concepte (PoC) sobre Predictive HR Analytics.

## Resultats Clau
*   Reducció de dimensionalitat d'un 92% (de 214 preguntes caòtiques a 17 variables netes).
*   Acuradesa predictiva del 75% (Recall 82%) per detectar empleats amb risc sever.
*   Creació d'un panell de control interactiu per monitorar el cost econòmic estructural de l'estrès als departaments d'IT.

## Autor
**Celio Sánchez Bañuls**  
Estudiant de l'assignatura de Treball Final de Grau (TFG) - Business Intelligence.  
*Universitat Oberta de Catalunya (UOC) - Juny 2026*
