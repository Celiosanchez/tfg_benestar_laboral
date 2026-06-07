import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

print("INICIANT PROVA DE CONCEPTE (PoC): PREDICTIVE HR ANALYTICS")


# 1. CÀRREGA DE DADES (L'arxiu mestre unificat)
df = pd.read_csv('data/osmi_unificat_NET_SINTETIC.csv')

# Filtrem els que tenen resposta clara al tractament
df_poc = df[df['te_tractament'].isin(['Yes', 'No'])].copy()
y = df_poc['te_tractament'].map({'Yes': 1, 'No': 0})

# ===================================================================
# 2. INJECCIÓ DE REGLES DE NEGOCI (LA SIMULACIÓ)
# Forçem una correlació: La gent amb tractament fa moltes hores extres 
# i té un rendiment més baix (Burnout operatiu).
# ===================================================================
np.random.seed(42)

# Simulem hores extres:
# - Els sans (0) fan de mitjana 2h d'hores extres
# - Els que tenen burnout (1) fan de mitjana 12h d'hores extres
df_poc['hores_extres_simulades'] = np.where(
    y == 1, 
    np.random.normal(loc=12, scale=3, size=len(y)), 
    np.random.normal(loc=2, scale=1, size=len(y))
)

# Simulem caiguda de rendiment (escala 1 a 5):
# - Els sans (0) tenen rendiment alt (mitjana 4)
# - Els que tenen burnout (1) tenen rendiment baix (mitjana 2)
df_poc['rendiment_simulat'] = np.where(
    y == 1, 
    np.random.normal(loc=2.2, scale=0.8, size=len(y)), 
    np.random.normal(loc=4.1, scale=0.6, size=len(y))
)

# Arrodonim per fer-ho realista
df_poc['hores_extres_simulades'] = np.clip(df_poc['hores_extres_simulades'].round(), 0, 40)
df_poc['rendiment_simulat'] = np.clip(df_poc['rendiment_simulat'].round(), 1, 5)

print(" Entorn simulat generat: Correlació forçada entre Hores Extres, Rendiment i Burnout.\n")

# 3. PREPARACIÓ PER A L'ENTRENAMENT
# Barregem variables clíniques i les nostres variables operatives simulades
features = [
    'edat_num', 'salari_anual', 'hores_extres_simulades', 'rendiment_simulat', 
    'mida_empresa', 'teletreball', 'es_rol_tech'
]
X_brut = df_poc[features]

# Transformem el text a columnes numèriques i netegem nuls
X = pd.get_dummies(X_brut, drop_first=True)
X['edat_num'] = X['edat_num'].fillna(X['edat_num'].mean())

# 4. ENTRENAMENT DEL MODEL
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
model.fit(X_train, y_train)

# 5. AVALUACIÓ DEL RENDIMENT
y_pred = model.predict(X_test)

print("--- RESULTATS DE LA PROVA DE CONCEPTE (PoC) ---")
print(f"Precisió Global (Accuracy): {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
print(classification_report(y_test, y_pred))

# 6. FEATURE IMPORTANCE (Què detecta l'algorisme?)
importancies = model.feature_importances_
df_importancies = pd.DataFrame({'Variable': X.columns, 'Importancia': importancies})
df_importancies = df_importancies.sort_values('Importancia', ascending=False)

print("--- TOP FACTORS DETECTATS PER LA INTEL·LIGÈNCIA ARTIFICIAL ---")
print(df_importancies.head(5).to_string(index=False))
print("\n PoC Finalitzada amb èxit!")