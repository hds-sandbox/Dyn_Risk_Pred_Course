# Workshop 1 - data management

import os
new_directory = r"C:\Users\p90j\Desktop\Jakob\MedicinPred2Sandbox\Day 1\Workshop - data management-20230817\Formatted data"
os.chdir(new_directory)

current_directory = os.getcwd()
print("Current working directory:", current_directory)

import pandas as pd
import numpy as np
import random
random.seed(42)

data_folder = r"C:\Users\p90j\Desktop\Jakob\MedicinPred2Sandbox\Day 1\Workshop - data management-20230817\Formatted data\Data"

baseline = pd.read_csv(f"{data_folder}/baseline_data.csv")
diag = pd.read_csv(f"{data_folder}/diag_data.csv")
dict_data = pd.read_csv(f"{data_folder}/dict_data.csv")
quest = pd.read_csv(f"{data_folder}/quest_data.csv")
blood = pd.read_csv(f"{data_folder}/blood_data.csv").rename(columns={"..record.id": "id"})
treat = pd.read_csv(f"{data_folder}/treat_data.csv").rename(columns={"record_id": "id"})
visits = pd.read_csv(f"{data_folder}/visit_date.csv").rename(columns={"visit_date": "date"})
visits["visit"] = True

events = pd.read_csv(f"{data_folder}/events.csv")

### Translate diagnosis codes

diag = diag.merge(dict_data, on="code").drop(columns=["code"])

### Removing variable with >20% missing (for a more rigorous approach this should be evaluated based on training data only, but here for simplicity done on all available data)

threshold = 0.2
baseline = baseline.dropna(thresh=len(baseline) * (1 - threshold), axis=1)
blood = blood.dropna(thresh=len(blood) * (1 - threshold), axis=1)
quest = quest.dropna(thresh=len(quest) * (1 - threshold), axis=1)
treat = treat.dropna(thresh=len(treat) * (1 - threshold), axis=1)

### Training, validation, calibration, and test set

split_probabilities = [0.8, 0.05, 0.05, 0.1]
idx = np.random.choice(["train", "validation", "calibration", "test"], size=len(baseline), replace=True, p=split_probabilities)
splits = pd.DataFrame({"id": baseline["id"], "split": idx})

### One dataset with a row per time stamp to contain all observed features

timevar = pd.merge(blood, diag, on=["id", "sample_date"], how="outer")
timevar = timevar.drop(columns=["Unnamed: 0", "Unnamed: 0_x", "Unnamed: 0_y"])
quest.rename(columns={"date.x": "sample_date"}, inplace=True)
#print("After pd.merge(blood, diag)")
#print(timevar)

timevar = timevar.merge(quest, how="outer", on=["id", "sample_date"])
timevar = timevar.drop(columns=["Unnamed: 0"])
treat.rename(columns={"treat_start_date": "sample_date"}, inplace=True)
#print("After pd.merge(quest)")
#print(timevar)

timevar = timevar.merge(treat, how="outer", on=["id", "sample_date"])
timevar = timevar.drop(columns=["Unnamed: 0"])
#print("After pd.merge(treat)")
#print(timevar)

timevar = pd.merge(timevar, visits, left_on=["id", "sample_date"], right_on=["id", "date"], how="outer")
timevar = timevar.drop(columns=["Unnamed: 0"])
#print("After pd.merge(visits)")
#print(timevar)

timevar = pd.merge(timevar, baseline, on="id", how="outer")
#print("After pd.merge(baseline)")
#print(timevar)

timevar = timevar.rename(columns={"sample_date": "date"})
#print("After renaming")
#print(timevar)

timevar = pd.merge(timevar, splits, on="id", how="left")
#print("After pd.merge(splits)")
#print(timevar)

### Mean values and standard deviation for imputation and normalization

filtered_data = timevar[timevar["split"] == "train"]
#print("Filtered Data:")
#print(filtered_data)

data_without_diag = filtered_data.drop(columns=["diag"])

#print("Data without diag:")
#print(data_without_diag)

mean_columns = data_without_diag.mean()
mean_rounded_columns = data_without_diag[["systolic", "diastolic", "hemoglobin", "platelets", "creatine",
                                          "anxiety", "vegetable", "aspirin", "statins"]].mean().round()

mean_columns_pp = mean_columns.append(mean_rounded_columns)
mean_columns = mean_columns.append(mean_rounded_columns)
mean_columns.rename(index=lambda col: f"mean_{col}", inplace=True)


#print("Mean Columns:")
#print(mean_columns)

q1_columns = data_without_diag.quantile(0.01)

q1_columns.rename(index=lambda col: f"q1_{col}", inplace=True)

#print("Q1 Columns:")
#print(q1_columns)

q99_columns = data_without_diag.quantile(0.99)

q99_columns.rename(index=lambda col: f"q99_{col}", inplace=True)

#print("Q99 Columns:")
#print(q99_columns)

summaries = pd.concat([mean_columns, q1_columns, q99_columns])

#print("Final Summaries:")
#print(summaries)

### Feature engineering

timevar = timevar.loc[:,~timevar.columns.duplicated()].copy()

timevar["date"] = pd.to_datetime(timevar["date"])
timevar["d.birth"] = pd.to_datetime(timevar["d.birth"])

final_data = timevar.sort_values(by=["id", "date"])

#print("Data after arranging:")
#print(final_data)

def calculate_age(row):
    birth_date = pd.Timestamp(row["d.birth"])
    return (row["date"] - birth_date).days / 365.25 #leap year

final_data["visit"] = final_data["visit"].fillna(False)
final_data["age"] = final_data.apply(calculate_age, axis=1)
final_data["male"] = np.where(final_data['sex'] == "male", 1, 0)
final_data["smoker_current"] = np.where(final_data["smoking"] == "current", 1, 0)
final_data["smoker_former"] = np.where(final_data["smoking"] == "former", 1, 0)

#print("Data after mutation:")
#print(final_data)

diagnoses = ["diabetes", "hyperlipidemia", "hypertension"]
for diagnosis in diagnoses:
    final_data[diagnosis] = np.where(final_data["diag"] == diagnosis, 1, 0)
    final_data[diagnosis] = final_data.groupby("id")[diagnosis].cumsum()

final_data = final_data.drop(columns=["diag", "d.birth", "sex", "smoking"])
columns_to_fill = ["systolic", "diastolic", "ldl", "hdl", "statins"]
final_data[columns_to_fill] = final_data[columns_to_fill].fillna(method='ffill')

#print("Data after column selection and filling missing values:")
#print(final_data)

final_data = final_data.copy()
final_data.fillna(mean_columns_pp, inplace=True)
#print("Data after replacing missing values with means:")
#print(final_data)

start_column = "systolic"
end_column = "statins"

columns_to_transform = final_data.columns[final_data.columns.get_loc("systolic"):final_data.columns.get_loc("statins")+1]

for col in columns_to_transform:
    final_data[col] = final_data[col].apply(lambda x: max(x, summaries[f"q1_{col}"]))
    final_data[col] = final_data[col].apply(lambda x: min(x, summaries[f"q99_{col}"]))
    final_data[col] = (final_data[col] - final_data[col].min()) / (final_data[col].max() - final_data[col].min())

#print("Data after capping and normalizing values:")
#print(final_data)

final_data = final_data[final_data["visit"]]
final_data.drop(columns=["visit"], inplace=True)
final_data = final_data[["id", "split"] + [col for col in final_data.columns if col not in ["id", "split"]]]

#print("Data after filtering and selecting columns:")
#print(final_data)

final_data["date"] = pd.to_datetime(final_data["date"])
events["date"] = pd.to_datetime(events["date"])

deaths = events[events["type"] == "death"].rename(columns={"date": "d.death"})[["d.death", "id"]]

final_data = pd.merge(final_data, deaths, on="id", how="left")

final_data["died_1y"] = ((final_data["d.death"] - final_data["date"]) / pd.Timedelta(days=365)) <= 1
final_data["died_1y"] = final_data["died_1y"].astype(int)

#print("Data after joining with events and calculating 1-year mortality:")
#print(final_data)

final_data.drop(columns=["d.death"], inplace=True)

print("Final Data:")
print(final_data)
#print(final_data.describe())
#print(final_data.shape)