import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import joblib

#Load and Preprocess Data
import os
data_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "dataset.csv")
data = pd.read_csv(data_path)


numeric_cols = ['CAP1', 'CAP2', 'CAP3']
categorical_cols = ['Institute_Code', 'Institute', 'Department', 'Category', 'Year']

#Fill missing CAPs row-wise
def fill_cap_rowwise(row):
    cap_cols = ['CAP1', 'CAP2', 'CAP3']
    row_mean = row[cap_cols].mean(skipna=True)
    row[cap_cols] = row[cap_cols].fillna(row_mean)
    return row

data = data.apply(fill_cap_rowwise, axis=1)

#Category Simplification
category_new = {
    "GOPENH": "OPEN", "GOPENO": "OPEN", "GOPENS": "OPEN",
    "LOPENH": "OPEN", "LOPENO": "OPEN", "LOPENS": "OPEN",
    "PWDOPENS": "OPEN", "DEFOPENS": "OPEN", "DEFOPNS": "OPEN",
    "GOBCH": "OBC", "GOBCO": "OBC", "GOBCS": "OBC",
    "LOBCH": "OBC", "LOBCO": "OBC", "LOBCS": "OBC",
    "DEFOBCS": "OBC", "DEFROBCS": "OBC", "PWDROBCS": "OBC",
    "GSCH": "SC", "GSCO": "SC", "GSCS": "SC",
    "LSCH": "SC", "LSCO": "SC", "LSCS": "SC",
    "GSTH": "ST", "GSTO": "ST", "GSTS": "ST",
    "LSTH": "ST", "LSTO": "ST", "LSTS": "ST",
    "GVJH": "VJ", "GVJO": "VJ", "GVJS": "VJ",
    "LVJH": "VJ", "LVJO": "VJ", "LVJS": "VJ",
    "GNT1H": "NT1", "GNT1O": "NT1", "LNT1H": "NT1", "LNT1O": "NT1",
    "GNT2H": "NT2", "GNT2O": "NT2", "LNT2H": "NT2", "LNT2O": "NT2",
    "GNT3H": "NT3", "GNT3O": "NT3", "LNT3H": "NT3", "LNT3O": "NT3",
    "GSEBCH": "SEBC", "GSEBCO": "SEBC", "LSEBCH": "SEBC", "LSEBCO": "SEBC",
    "EWS": "EWS", "TFWS": "TFWS"
}
data["Category"] = data["Category"].map(category_new).fillna(data["Category"])

data_transformed = pd.melt(
    data,
    id_vars=categorical_cols,
    value_vars=numeric_cols,
    var_name="Round",
    value_name="Cutoff_Value"
)
data_transformed["Cutoff_Value"] = pd.to_numeric(data_transformed["Cutoff_Value"], errors="coerce")

#Simulate realistic student data
np.random.seed(42)
data_transformed["Student_Percentile"] = (
    data_transformed["Cutoff_Value"] + np.random.randn(len(data_transformed)) * 5
).clip(0, 100)

#Calculate chance using sigmoid
data_transformed["Chance_of_Admit"] = 1 / (1 + np.exp(-(data_transformed["Student_Percentile"] - data_transformed["Cutoff_Value"]) / 2))


X = data_transformed[['Student_Percentile', 'Category', 'Institute', 'Department', 'Institute_Code', 'Round']]
y = data_transformed['Chance_of_Admit']

#Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#Preprocessing + Pipeline
nominal_features = ['Category', 'Institute', 'Department', 'Institute_Code']
ordinal_features = ['Round']
round_order = [['CAP1', 'CAP2', 'CAP3']]
numeric_features = ['Student_Percentile']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', numeric_features),
        ('nom', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), nominal_features),
        ('ord', OrdinalEncoder(categories=round_order), ordinal_features)
    ]
)

pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(n_estimators=200, random_state=42))
])

#Train & Save Model
pipeline.fit(X_train, y_train)

score = pipeline.score(X_test, y_test)
print(f"Model R² Score: {score:.3f}")

os.makedirs("models", exist_ok=True)
joblib.dump(pipeline, "models/admission_model.pkl")

print("Model saved successfully!")
