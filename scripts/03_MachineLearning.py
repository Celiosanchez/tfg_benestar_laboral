import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

print("INICIANT MACHINE LEARNING (DADES REALS OSMI)")

# 1. CÀRREGA DE DADES
# Agafem el CSV que acaba de generar l'ETL
df = pd.read_csv('data/osmi_unificat_NET_SINTETIC.csv')

# 2. PREPARACIÓ DE DADES (L'Estudi Rigorós)
# Filtrem només els que han respost clarament "Yes" o "No" a tenir tractament
df_ml = df[df['te_tractament'].isin(['Yes', 'No'])].copy()
y = df_ml['te_tractament'].map({'Yes': 1, 'No': 0})

# Variables predictores: NOMÉS LES REALS DE L'ENQUESTA (Ignorem salari i hores)
features = [
    'edat_num', 'genere', 'mida_empresa', 'teletreball', 
    'es_rol_tech', 'facilitat_baixa', 'anonimat', 'por_represalies'
]
X_brut = df_ml[features]

# Transformem el text a columnes numèriques (One-Hot Encoding)
X = pd.get_dummies(X_brut, drop_first=True)

# Omplim les edats buides amb la mitjana
X['edat_num'] = X['edat_num'].fillna(X['edat_num'].mean())

print(f"Entrenant model amb {len(df_ml)} treballadors i {len(X.columns)} variables...")

# 3. ENTRENAMENT (Train/Test Split)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Utilitzem Random Forest (Caixa Blanca per a RRHH)
model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
model.fit(X_train, y_train)

# 4. AVALUACIÓ
y_pred = model.predict(X_test)

print("\n--- RESULTATS DEL MODEL CLÍNIC/CORPORATIU ---")
print(f"Precisió Global (Accuracy): {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
print(classification_report(y_test, y_pred))

# 5. IMPORTÀNCIA DE LES VARIABLES (Què causa el burnout?)
importancies = model.feature_importances_
df_importancies = pd.DataFrame({'Variable': X.columns, 'Importancia': importancies})
df_importancies = df_importancies.sort_values('Importancia', ascending=False)

print("--- TOP FACTORS QUE PREDIUEN LA NECESSITAT DE TRACTAMENT ---")
print(df_importancies.head(10).to_string(index=False))