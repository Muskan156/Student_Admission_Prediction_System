import pandas as pd
import numpy as np
import joblib

model = joblib.load("models/admission_model.pkl")

data = pd.read_csv(r"C:\StudentAdmissionPrediction\dataset\dataset.csv")

numeric_cols = ['CAP1', 'CAP2', 'CAP3']
categorical_cols = ['Institute_Code', 'Institute', 'Department', 'Category', 'Year']

def fill_cap_rowwise(row):
    cap_cols = ['CAP1', 'CAP2', 'CAP3']
    row_mean = row[cap_cols].mean(skipna=True)
    row[cap_cols] = row[cap_cols].fillna(row_mean)
    return row

data = data.apply(fill_cap_rowwise, axis=1)

category_new = {
    "GOPENH": "OPEN", "GOPENO": "OPEN", "GOPENS": "OPEN",
    "LOPENH": "OPEN", "LOPENO": "OPEN", "LOPENS": "OPEN",
    "PWDOPENS": "OPEN", "DEFOPENS": "OPEN", "DEFOPNS": "OPEN",
    "GOBCH": "OBC", "GOBCO": "OBC", "GOBCS": "OBC",
    "LOBCH": "OBC", "LOBCO": "OBC", "LOBCS": "OBC",
    "GSCH": "SC", "LSCH": "SC", "GSTH": "ST", "LSTH": "ST",
    "GNT1H": "NT1", "GNT2H": "NT2", "GNT3H": "NT3",
    "GVJH": "VJ", "GSEBCH": "SEBC", "EWS": "EWS", "TFWS": "TFWS"
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

#Prediction Function
# def predict_admission(student_percentile, student_category):
#     eligible_colleges = data_transformed[
#         data_transformed["Category"].str.upper() == student_category.upper()
#     ].copy()

#     if eligible_colleges.empty:
#         print("No colleges found for this category.")
#         return []

#     eligible_colleges["Student_Percentile"] = student_percentile

#     X_student = eligible_colleges[[
#         "Student_Percentile", "Category", "Institute",
#         "Department", "Institute_Code", "Round"
#     ]]

#     eligible_colleges["Chance (%)"] = (
#         model.predict(X_student) * 100
#     ).clip(0, 100).round(2)

#     pivot_df = eligible_colleges.pivot_table(
#         index=["Institute", "Department", "Category"],
#         columns="Round",
#         values="Chance (%)",
#         aggfunc="first"
#     ).reset_index()

#     pivot_df = pivot_df.rename(columns={
#         "CAP1": "CAP1 (%)",
#         "CAP2": "CAP2 (%)",
#         "CAP3": "CAP3 (%)"
#     }).fillna(0)

#     pivot_df["Best Chance (%)"] = pivot_df[["CAP1 (%)", "CAP2 (%)", "CAP3 (%)"]].max(axis=1)
#     college_rank = (
#         pivot_df.groupby("Institute")["Best Chance (%)"].max()
#         .rank(ascending=False, method="dense")
#         .astype(int)
#         .rename("College Rank")
#     )
#     pivot_df = pivot_df.merge(college_rank, on="Institute")

#     results_df = pivot_df.sort_values(
#         by=["College Rank", "Institute", "Best Chance (%)"],
#         ascending=[True, True, False]
#     ).reset_index(drop=True)

#     return results_df
def predict_admission(student_percentile, student_category):
    eligible_colleges = data_transformed[
        data_transformed["Category"].str.upper() == student_category.upper()
    ].copy()

    if eligible_colleges.empty:
        print("No colleges found for this category.")
        return []

    eligible_colleges["Student_Percentile"] = student_percentile

    X_student = eligible_colleges[[
        "Student_Percentile", "Category", "Institute",
        "Department", "Institute_Code", "Round"
    ]]

    eligible_colleges["Chance (%)"] = (
        model.predict(X_student) * 100
    ).clip(0, 100).round(2)

    pivot_df = eligible_colleges.pivot_table(
        index=["Institute", "Department", "Category"],
        columns="Round",
        values="Chance (%)",
        aggfunc="first"
    ).reset_index()

    pivot_df = pivot_df.rename(columns={
        "CAP1": "CAP1 (%)",
        "CAP2": "CAP2 (%)",
        "CAP3": "CAP3 (%)"
    }).fillna(0)

    pivot_df["Best Chance (%)"] = pivot_df[
        ["CAP1 (%)", "CAP2 (%)", "CAP3 (%)"]
    ].max(axis=1)

    college_rank = (
        pivot_df.groupby("Institute")["Best Chance (%)"].max()
        .rank(ascending=False, method="dense")
        .astype(int)
        .rename("College Rank")
    )

    pivot_df = pivot_df.merge(college_rank, on="Institute")

    results_df = pivot_df.sort_values(
        by=["College Rank", "Institute", "Best Chance (%)"],
        ascending=[True, True, False]
    ).reset_index(drop=True)

    # ✅ FIX — convert DataFrame to list of dicts
    results = results_df.to_dict(orient="records")
    return results
