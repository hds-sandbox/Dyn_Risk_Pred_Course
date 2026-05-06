import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)


# ==============================================================================
# 1. Load data
# ==============================================================================



baseline = pd.read_csv("../../../exercise_data/raw_data/baseline_data.csv")
diag = pd.read_csv("../../../exercise_data/raw_data/diag_data.csv").drop(columns=["Unnamed: 0"], errors="ignore")
dict_ = pd.read_csv("../../../exercise_data/raw_data/dict_data.csv").drop(columns=["Unnamed: 0"], errors="ignore")
quest = pd.read_csv("../../../exercise_data/raw_data/quest_data.csv").drop(columns=["Unnamed: 0"], errors="ignore")
blood = pd.read_csv("../../../exercise_data/raw_data/blood_data.csv").drop(columns=["Unnamed: 0"], errors="ignore")
treat = pd.read_csv("../../../exercise_data/raw_data/treat_data.csv").drop(columns=["Unnamed: 0"], errors="ignore")
events = pd.read_csv("../../../exercise_data/raw_data/events.csv").drop(columns=["Unnamed: 0"], errors="ignore")
visits = pd.read_csv("../../../exercise_data/raw_data/visit_date.csv")

# ==============================================================================
# Data cleaning: rename columns
# ==============================================================================
blood = blood.rename(columns={"..record.id": "id"})
treat = treat.rename(columns={"record_id": "id"})
quest = quest.rename(columns={"date.x": "date"})

# ==============================================================================
# 2. Translate diagnosis codes
# ==============================================================================
diag = diag.merge(dict_, on="code", how="left").drop(columns=["code"])

# ==============================================================================
# 3. Join feature datasets
# ==============================================================================
# Rename date columns to 'date' for consistent merging
blood = blood.rename(columns={'sample_date': 'date'})
diag = diag.rename(columns={'sample_date': 'date'})
treat = treat.rename(columns={'treat_start_date': 'date'})
visits = visits.rename(columns={'visit_date': 'date'})

# Add visit indicator
visits["visit"] = True

# Merge all feature datasets
feat_merged = blood.merge(diag, on=['id', 'date'], how='outer') \
                 .merge(quest, on=['id', 'date'], how='outer') \
                 .merge(treat, on=['id', 'date'], how='outer') \
                 .merge(visits, on=['id', 'date'], how='outer')

# ==============================================================================
# 4. Add baseline information
# ==============================================================================
full_dat = feat_merged.merge(baseline, on='id', how='outer')

# ==============================================================================
# 5. Train-validation split (70/10/10/10)
# ==============================================================================
np.random.seed(123)
splits = pd.DataFrame({
    'id': baseline['id'],
    'split': np.random.choice(
        ["train", "validation", "calibration", "test"],
        size=len(baseline),
        p=[0.7, 0.1, 0.1, 0.1]
    )
})
full_dat = full_dat.merge(splits, on='id', how='left')

# ==============================================================================
# 6. Remove predictors with >20% missing at patient-level (train only)
# ==============================================================================
train_data = full_dat[full_dat['split'] == 'train']

# For each column (except id, date, split), calculate % of patients with all NA
all_na_counts = {}
for col in train_data.columns:
    if col in ['id', 'date', 'split']:
        continue
    na_check = train_data.groupby('id')[col].apply(lambda x: x.isnull().all())
    all_na_counts[col] = na_check.mean()

# Keep columns where <20% patients have all NA, plus essential columns
cols_to_keep = ['id', 'date', 'split']
cols_to_keep.extend([c for c in all_na_counts if all_na_counts[c] < 0.2])
full_dat = full_dat[cols_to_keep]

# ==============================================================================
# 7. Calculate age at each visit
# ==============================================================================
full_dat['date'] = pd.to_datetime(full_dat['date'], errors='coerce')
full_dat['d.birth'] = pd.to_datetime(full_dat['d.birth'], errors='coerce')
full_dat['age'] = (full_dat['date'] - full_dat['d.birth']).dt.days / 365.242

# Convert integer columns to float (like R's as.double)
int_cols = full_dat.select_dtypes(include=['int64']).columns
full_dat[int_cols] = full_dat[int_cols].astype(float)

# ==============================================================================
# 8. Summaries for imputation and normalization (mean, q1, q99)
# ==============================================================================
train_data = full_dat[full_dat['split'] == 'train']
numeric_cols = train_data.select_dtypes(include=[np.number]).columns

summaries = {}
for col in numeric_cols:
    if col in ['id', 'date', 'split']:
        continue
    summaries[f'mean_{col}'] = train_data[col].mean()
    summaries[f'q1_{col}'] = train_data[col].quantile(0.01)
    summaries[f'q99_{col}'] = train_data[col].quantile(0.99)

# ==============================================================================
# 9. Feature engineering
# ==============================================================================
full_dat = full_dat.sort_values(['id', 'date'])

# Prediction time points
full_dat['visit'] = full_dat['visit'].fillna(False)

# Sex encoding (R creates both male and female)
full_dat['male'] = (full_dat['sex'] == 'male').astype(int)
full_dat['female'] = (full_dat['sex'] == 'female').astype(int)

# Smoking encoding (R creates current, former, never)
full_dat['smoker_current'] = (full_dat['smoking'] == 'current').astype(int)
full_dat['smoker_former'] = (full_dat['smoking'] == 'former').astype(int)
full_dat['smoker_never'] = (full_dat['smoking'] == 'never').astype(int)

# Diagnoses with carry-forward
for cond in ['diabetes', 'hyperlipidemia', 'hypertension']:
    full_dat[cond] = (full_dat['diag'] == cond).astype(int)
    full_dat[cond] = full_dat.groupby('id')[cond].cumsum()

# Drop original columns
full_dat = full_dat.drop(columns=['diag', 'd.birth', 'sex', 'smoking'], errors='ignore')

# Identify measurement columns (numeric, not binary encoded)
binary_encoded = ['male', 'female', 'smoker_current', 'smoker_former', 'smoker_never',
                  'diabetes', 'hyperlipidemia', 'hypertension']
measurement_cols = [c for c in numeric_cols if c not in binary_encoded + ['id', 'date', 'split', 'age']]

# Carry-forward imputation for measurement columns
if measurement_cols:
    full_dat[measurement_cols] = full_dat.groupby('id')[measurement_cols].ffill()

# Impute remaining NA with training means (for measurement columns and age)
impute_cols = measurement_cols + ['age']
for col in impute_cols:
    if f'mean_{col}' in summaries:
        full_dat[col] = full_dat[col].fillna(summaries[f'mean_{col}'])

# Cap at q1 and q99 for measurement columns and age
norm_cols = measurement_cols + ['age']
for col in norm_cols:
    if f'q1_{col}' in summaries and f'q99_{col}' in summaries:
        full_dat[col] = full_dat[col].clip(
            lower=summaries[f'q1_{col}'],
            upper=summaries[f'q99_{col}']
        )

# Min-max normalization for measurement columns and age
for col in norm_cols:
    if f'q1_{col}' in summaries and f'q99_{col}' in summaries:
        q1 = summaries[f'q1_{col}']
        q99 = summaries[f'q99_{col}']
        full_dat[col] = (full_dat[col] - q1) / (q99 - q1)

# ==============================================================================
# 10. Filter to prediction time points only
# ==============================================================================
pred_data = full_dat[full_dat['visit'] == True].copy()
pred_data = pred_data.drop(columns=['visit'])

# Relocate split column after id
cols = pred_data.columns.tolist()
if 'split' in cols:
    cols.remove('split')
    id_idx = cols.index('id')
    cols.insert(id_idx + 1, 'split')
    pred_data = pred_data[cols]

# ==============================================================================
# 11. Define outcome: major event or death within 1 year
# ==============================================================================
# Get first death, major, or minor event per patient
event_oi = events[events['type'].isin(['death', 'major', 'minor'])] \
            .sort_values('date') \
            .groupby('id') \
            .first() \
            .reset_index()[['id', 'date']] \
            .rename(columns={'date': 'd.event'})

pred_data['date'] = pd.to_datetime(pred_data['date'])
event_oi['d.event'] = pd.to_datetime(event_oi['d.event'])

final_data = pred_data.merge(event_oi, on='id', how='left')

# Vectorized calculation: event within 1 year
one_year_later = final_data['date'] + pd.DateOffset(years=1)
final_data['event_1y'] = (
    (final_data['d.event'] >= final_data['date']) &
    (final_data['d.event'] <= one_year_later)
).fillna(False).astype(int)

# Drop unnecessary columns
final_data = final_data.drop(columns=['d.event', 'event', 'type'], errors='ignore')

# Drop duplicates                                                                                                                                 ▁ document comprehensive, but without any redundacy or repeating text. Put the .md file in the same dir as the code and Call it workshop_2_R
final_data = final_data.drop_duplicates(subset=['id', 'date'], keep='first')

print(final_data)
print(final_data.describe())

# ==============================================================================
# 12. Save final data
# ==============================================================================
final_data.to_csv("Data_ready_for_workshop2_pytest.csv", index=False)
print("Data saved to Data_ready_for_workshop2_pytest.csv")
