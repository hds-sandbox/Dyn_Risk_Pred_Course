## -----------------------------------------------------------------------------
## Import packages
## -----------------------------------------------------------------------------

import numpy as np
import pandas as pd
import joblib  # for loading RDS files
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (precision_score, roc_auc_score, average_precision_score, 
                             brier_score_loss, PrecisionRecallDisplay, RocCurveDisplay)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve, CalibrationDisplay
from sklearn.ensemble import RandomForestClassifier
# from xgboost import XGBClassifier # If wanting to run the xgboost model, remove the '# ' and install the package 'pip install xgboost' in the terminal
from sklearn.model_selection import ParameterGrid
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

## -----------------------------------------------------------------------------
## Load and prepare preprocessed data
## -----------------------------------------------------------------------------

# Load data (RDS file can be loaded using joblib or pyreadr)
# Note: You may need to install pyreadr: pip install pyreadr
try:
    import pyreadr
    df = pyreadr.read_r("../Code/exercise_solutions/Data_ready_for_workshop2.rds")[None]
except:
    # Alternative: convert RDS to CSV in R first, or use joblib
    df = joblib.load("../Code/exercise_solutions/Data_ready_for_workshop2.rds")
    if isinstance(df, dict):
        df = df[list(df.keys())[0]]

# Ensure df is a pandas DataFrame
df = pd.DataFrame(df)

# Test and calibration data
df_test = df[df['split'] == 'test']
df_cal = df[df['split'] == 'calibration']
df_train = df[df['split'] == 'train']
df_val = df[df['split'] == 'validation']

# Create train and validation indices for resampling
val_split_indices = {
    'analysis': df_train.index.tolist(),
    'assessment': df_val.index.tolist()
}

# Define features and target
X = df.drop(columns=['event_1y', 'id', 'split', 'date'])
y = df['event_1y']
X_train = df_train.drop(columns=['event_1y', 'id', 'split', 'date'])
y_train = df_train['event_1y']
X_val = df_val.drop(columns=['event_1y', 'id', 'split', 'date'])
y_val = df_val['event_1y']
X_test = df_test.drop(columns=['event_1y', 'id', 'split', 'date'])
y_test = df_test['event_1y']
X_cal = df_cal.drop(columns=['event_1y', 'id', 'split', 'date'])
y_cal = df_cal['event_1y']

# Recipe (preprocessing pipeline)
# Identify categorical and numeric columns
numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ])

## -----------------------------------------------------------------------------
## Logistic regression - model training
## -----------------------------------------------------------------------------

# NB: no hyperparameters for logistic regression

# Setup model
blr_mod = LogisticRegression(
    penalty=None,  # No regularization
    solver='lbfgs',
    max_iter=1000,
    random_state=42
)

# Combine model and recipe into pipeline
blr_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', blr_mod)
])

# Train model
blr_pipeline.fit(X_train, y_train)

# Predictions on validation set
blr_val_pred_proba = blr_pipeline.predict_proba(X_val)[:, 1]

# PR curve for validation set
blr_disp = PrecisionRecallDisplay.from_predictions(y_val, blr_val_pred_proba)
blr_disp.plot()
plt.title("Precision-Recall Curve - Logistic Regression")
plt.show()

## -----------------------------------------------------------------------------
## Elastic net - model training
## -----------------------------------------------------------------------------

# NB: two hyperparameters for elastic net (C=1/penalty and l1_ratio=mixture)

# Setup model with tuning parameters
# We'll use LogisticRegressionCV for automatic tuning
# Define parameter grid
penalty_values = 10 ** np.linspace(-6, -2, 101)
mixture_values = np.linspace(0, 1, 11)

# Create parameter grid
param_grid = [{'C': [1/p for p in penalty_values], 'l1_ratio': mixture_values}]

# Manual grid search
best_pr_auc = 0
best_params = None
best_model = None

for params in ParameterGrid(param_grid):
    el_mod = LogisticRegression(
        penalty='elasticnet',
        C=params['C'],
        l1_ratio=params['l1_ratio'],
        solver='saga',
        max_iter=1000,
        random_state=42
    )
    el_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', el_mod)
    ])
    el_pipeline.fit(X_train, y_train)
    val_pred_proba = el_pipeline.predict_proba(X_val)[:, 1]
    pr_auc = average_precision_score(y_val, val_pred_proba)
    
    if pr_auc > best_pr_auc:
        best_pr_auc = pr_auc
        best_params = params
        best_model = el_pipeline

print(f"Best parameters: C={best_params['C']}, l1_ratio={best_params['l1_ratio']}")
print(f"Best PR AUC: {best_pr_auc}")

# Train best elastic net model
el_best = best_model
el_best.fit(X_train, y_train)

## -----------------------------------------------------------------------------
## Further models
## -----------------------------------------------------------------------------

# Using scikit-learn you can easily fit several other models 
# (e.g., random forest and XGboost) by changing the classifier

# Example: Random Forest
# rf_mod = RandomForestClassifier(n_estimators=100, random_state=42)
# rf_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', rf_mod)])
# rf_pipeline.fit(X_train, y_train)

# Example: XGBoost
# xgb_mod = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
# xgb_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', xgb_mod)])
# xgb_pipeline.fit(X_train, y_train)

## -----------------------------------------------------------------------------
## Retrain models on combined training and validation set, using optimal 
## hyperparameters
## -----------------------------------------------------------------------------

# New splits
X_train_full = pd.concat([X_train, X_val])
y_train_full = pd.concat([y_train, y_val])

# Preprocess the full training data
preprocessor.fit(X_train_full)

## Logistic regression ---------------------------------------------------------

# Train and evaluate model
blr_final = LogisticRegression(
    penalty=None,
    solver='lbfgs',
    max_iter=1000,
    random_state=42
)
blr_final.fit(preprocessor.transform(X_train_full), y_train_full)

# Performance metrics
blr_pred_proba = blr_final.predict_proba(preprocessor.transform(X_test))[:, 1]
blr_metrics = {
    'precision': precision_score(y_test, blr_final.predict(preprocessor.transform(X_test))),
    'roc_auc': roc_auc_score(y_test, blr_pred_proba),
    'pr_auc': average_precision_score(y_test, blr_pred_proba),
    'brier': brier_score_loss(y_test, blr_pred_proba)
}

print("\nLogistic Regression Metrics:")
for metric, value in blr_metrics.items():
    print(f"  {metric}: {value:.4f}")

# Most important features (coefficients for logistic regression)
# Get feature names after one-hot encoding
cat_encoder = preprocessor.named_transformers_['cat']
if len(categorical_cols) > 0:
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_cols)
else:
    cat_feature_names = []

all_feature_names = numeric_cols + list(cat_feature_names)
blr_coef = pd.DataFrame({
    'feature': all_feature_names,
    'coefficient': blr_final.coef_[0]
}).sort_values('coefficient', key=abs, ascending=False).head(20)

print("\nTop 20 features - Logistic Regression:")
print(blr_coef)

## Elastic net -----------------------------------------------------------------

# Use hyperparameters determined earlier
el_final = LogisticRegression(
    penalty='elasticnet',
    C=best_params['C'],
    l1_ratio=best_params['l1_ratio'],
    solver='saga',
    max_iter=1000,
    random_state=42
)
el_final.fit(preprocessor.transform(X_train_full), y_train_full)

# Performance metrics
el_pred_proba = el_final.predict_proba(preprocessor.transform(X_test))[:, 1]
el_metrics = {
    'precision': precision_score(y_test, el_final.predict(preprocessor.transform(X_test))),
    'roc_auc': roc_auc_score(y_test, el_pred_proba),
    'pr_auc': average_precision_score(y_test, el_pred_proba),
    'brier': brier_score_loss(y_test, el_pred_proba)
}

print("\nElastic Net Metrics:")
for metric, value in el_metrics.items():
    print(f"  {metric}: {value:.4f}")

# Most important features (coefficients for elastic net)
el_coef = pd.DataFrame({
    'feature': all_feature_names,
    'coefficient': el_final.coef_[0]
}).sort_values('coefficient', key=abs, ascending=False).head(20)

print("\nTop 20 features - Elastic Net:")
print(el_coef)

## -----------------------------------------------------------------------------
## Summarise performance across models
## -----------------------------------------------------------------------------

# Create results DataFrame
results = pd.DataFrame({
    'model': ['Logistic'] * 4 + ['Elastic Net'] * 4,
    '.metric': ['precision', 'roc_auc', 'pr_auc', 'brier'] * 2,
    '.estimate': list(blr_metrics.values()) + list(el_metrics.values())
})

print("\nPerformance Comparison:")
print(results.pivot(index='.metric', columns='model', values='.estimate'))

# Plot performance metrics
plt.figure(figsize=(12, 8))
sns.barplot(data=results, x='model', y='.estimate', hue='.metric')
plt.title("Performance Metrics by Model")
plt.ylim(0, 1)
plt.xticks(rotation=45)
plt.show()

# PR curve
plt.figure(figsize=(10, 8))

# Logistic Regression PR curve
blr_disp = PrecisionRecallDisplay.from_predictions(y_test, blr_pred_proba)
blr_disp.plot(name="Logistic")

# Elastic Net PR curve
el_disp = PrecisionRecallDisplay.from_predictions(y_test, el_pred_proba)
el_disp.plot(name="Elastic Net", ax=plt.gca())

plt.title("Precision-Recall Curve")
plt.legend()
plt.show()

## -----------------------------------------------------------------------------
## Model calibration 
## -----------------------------------------------------------------------------

# Calibration is shown here for the elastic net model

# Predictions on test data
el_test_pred = pd.DataFrame({
    '.row': X_test.index,
    'el': el_pred_proba,
    'event_1y': y_test.values
})

# Predictions for the calibration data set
el_cal_pred_proba = el_final.predict_proba(preprocessor.transform(X_cal))[:, 1]
el_cal_pred = pd.DataFrame({
    'el': el_cal_pred_proba,
    'event_1y': y_cal.values
})

# Platt calibration (logistic regression)
from sklearn.linear_model import LogisticRegression as LR
platt_model = LR(solver='lbfgs', max_iter=1000)
platt_model.fit(el_cal_pred[['el']], (el_cal_pred['event_1y'] == 1).astype(int))

print("\nPlatt Calibration Model Summary:")
print(f"Coefficient: {platt_model.coef_[0][0]:.4f}, Intercept: {platt_model.intercept_[0]:.4f}")

# Apply calibrations for calibration data (sanity check)
el_cal_pred['el_calibrated'] = platt_model.predict_proba(el_cal_pred[['el']])[:, 1]

# Calibration plot for calibration data
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Uncalibrated
CalibrationDisplay.from_predictions(
    el_cal_pred['event_1y'], el_cal_pred['el'],
    n_bins=20, name='Uncalibrated', ax=ax1
)
ax1.set_title("Calibration Plot - Uncalibrated Elastic Net (Calibration Data)")

# Calibrated
CalibrationDisplay.from_predictions(
    el_cal_pred['event_1y'], el_cal_pred['el_calibrated'],
    n_bins=20, name='Calibrated', ax=ax2
)
ax2.set_title("Calibration Plot - Calibrated Elastic Net (Calibration Data)")

plt.tight_layout()
plt.show()

# Scatter plot: raw vs calibrated
plt.figure(figsize=(10, 6))
sns.scatterplot(data=el_cal_pred, x='el', y='el_calibrated', hue='event_1y')
plt.title("Raw vs Calibrated Probabilities (Calibration Data)")
plt.show()

# Apply calibrations for test data
el_test_pred['el_calibrated'] = platt_model.predict_proba(el_test_pred[['el']])[:, 1]

# Calibration plot using sklearn
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Uncalibrated
CalibrationDisplay.from_predictions(
    el_test_pred['event_1y'], el_test_pred['el'],
    n_bins=20, name='Uncalibrated', ax=ax1
)
ax1.set_title("Calibration Plot - Uncalibrated Elastic Net")

# Calibrated
CalibrationDisplay.from_predictions(
    el_test_pred['event_1y'], el_test_pred['el_calibrated'],
    n_bins=20, name='Calibrated', ax=ax2
)
ax2.set_title("Calibration Plot - Calibrated Elastic Net")

plt.tight_layout()
plt.show()

# Note: due to high class imbalance, too little data, and 
# the spread of predicted probabilities is quite small, the calibration plots 
# generated here are not that meaningful unfortunately. Do not put too much energy
# in trying to decipher the results from this.
