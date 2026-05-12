## -----------------------------------------------------------------------------
## Import packages
## -----------------------------------------------------------------------------
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, ParameterGrid
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, roc_auc_score, average_precision_score,
    brier_score_loss, precision_recall_curve, roc_curve
)
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility (match R's behavior)
np.random.seed(42)

## -----------------------------------------------------------------------------
## Load and prepare data
## -----------------------------------------------------------------------------
df = pd.read_csv("../Data_ready_for_workshop2.csv")
df = pd.DataFrame(df)

# Split data
df_test = df[df['split'] == 'test']
df_cal = df[df['split'] == 'calibration']
df_train = df[df['split'] == 'train']
df_val = df[df['split'] == 'validation']

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

# Preprocessing
numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ]
)

## -----------------------------------------------------------------------------
## Logistic Regression
## -----------------------------------------------------------------------------
blr_mod = LogisticRegression(
    penalty=None,
    solver='lbfgs',
    max_iter=1000,
    random_state=42
)

blr_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', blr_mod)
])

blr_pipeline.fit(X_train, y_train)
blr_val_pred_proba = blr_pipeline.predict_proba(X_val)[:, 1]

# PR curve for Logistic Regression
precision, recall, _ = precision_recall_curve(y_val, blr_val_pred_proba)
plt.figure()
plt.plot(recall, precision, label='Logistic Regression')
plt.title("Precision-Recall Curve - Logistic Regression")
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.xlim([0, 1])
plt.ylim([0, 1.05])
plt.axhline(y=1, color='gray', linestyle=':')
plt.legend()
plt.show()

## -----------------------------------------------------------------------------
## Elastic Net (with manual grid search)
## -----------------------------------------------------------------------------
penalty_values = 10 ** np.linspace(-6, -2, 101)
mixture_values = np.linspace(0, 1, 11)
param_grid = [{'C': [1/p for p in penalty_values], 'l1_ratio': mixture_values}]

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

# Retrain best model on full training + validation data
X_train_full = pd.concat([X_train, X_val])
y_train_full = pd.concat([y_train, y_val])
preprocessor.fit(X_train_full)  # Re-fit preprocessor on full data

el_final = LogisticRegression(
    penalty='elasticnet',
    C=best_params['C'],
    l1_ratio=best_params['l1_ratio'],
    solver='saga',
    max_iter=1000,
    random_state=42
)
el_final.fit(preprocessor.transform(X_train_full), y_train_full)

## -----------------------------------------------------------------------------
## Evaluate Models on Test Set
## -----------------------------------------------------------------------------
# Logistic Regression
blr_final = LogisticRegression(penalty=None, solver='lbfgs', max_iter=1000, random_state=42)
blr_final.fit(preprocessor.transform(X_train_full), y_train_full)
blr_pred_proba = blr_final.predict_proba(preprocessor.transform(X_test))[:, 1]

blr_metrics = {
    'precision': precision_score(y_test, blr_final.predict(preprocessor.transform(X_test))),
    'roc_auc': roc_auc_score(y_test, blr_pred_proba),
    'pr_auc': average_precision_score(y_test, blr_pred_proba),
    'brier': brier_score_loss(y_test, blr_pred_proba)
}

# Elastic Net
el_pred_proba = el_final.predict_proba(preprocessor.transform(X_test))[:, 1]
el_metrics = {
    'precision': precision_score(y_test, el_final.predict(preprocessor.transform(X_test))),
    'roc_auc': roc_auc_score(y_test, el_pred_proba),
    'pr_auc': average_precision_score(y_test, el_pred_proba),
    'brier': brier_score_loss(y_test, el_pred_proba)
}

# Print metrics
print("\nLogistic Regression Metrics:")
for metric, value in blr_metrics.items():
    print(f"  {metric}: {value:.4f}")

print("\nElastic Net Metrics:")
for metric, value in el_metrics.items():
    print(f"  {metric}: {value:.4f}")

# Performance comparison table
results = pd.DataFrame({
    'model': ['Logistic'] * 4 + ['Elastic Net'] * 4,
    '.metric': ['precision', 'roc_auc', 'pr_auc', 'brier'] * 2,
    '.estimate': list(blr_metrics.values()) + list(el_metrics.values())
})
print("\nPerformance Comparison:")
print(results.pivot(index='.metric', columns='model', values='.estimate'))

# Performance metrics barplot
plt.figure()
metrics_order = ['precision', 'roc_auc', 'pr_auc', 'brier']
x = np.arange(len(metrics_order))
width = 0.35
for i, model in enumerate(['Logistic', 'Elastic Net']):
    model_data = results[results['model'] == model]
    values = [model_data[model_data['.metric'] == m]['.estimate'].values[0] for m in metrics_order]
    plt.bar(x + i * width, values, width, label=model)
plt.title("Performance Metrics by Model")
plt.xlabel("Metric")
plt.ylabel("Score")
plt.ylim([0, 1.1])
plt.xticks(x + width / 2, metrics_order)
plt.legend()
plt.show()

# PR curve for both models
precision_blr, recall_blr, _ = precision_recall_curve(y_test, blr_pred_proba)
precision_el, recall_el, _ = precision_recall_curve(y_test, el_pred_proba)

plt.figure()
plt.plot(recall_blr, precision_blr, label='Logistic')
plt.plot(recall_el, precision_el, label='Elastic Net')
plt.title("Precision-Recall Curve Comparison")
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.xlim([0, 1])
plt.ylim([0, 1.05])
plt.axhline(y=1, color='gray', linestyle=':')
plt.legend()
plt.show()

## -----------------------------------------------------------------------------
## Feature Importance
## -----------------------------------------------------------------------------
# Get feature names after one-hot encoding
cat_encoder = preprocessor.named_transformers_['cat']
cat_feature_names = cat_encoder.get_feature_names_out(categorical_cols) if categorical_cols else []
all_feature_names = numeric_cols + list(cat_feature_names)

# Logistic Regression
blr_coef = pd.DataFrame({
    'feature': all_feature_names,
    'coefficient': blr_final.coef_[0],
    'importance_type': 'coefficient'
}).sort_values('coefficient', key=abs, ascending=False).head(20)

print("\nTop 20 features - Logistic Regression:")
print(blr_coef)

# Elastic Net
el_coef = pd.DataFrame({
    'feature': all_feature_names,
    'coefficient': el_final.coef_[0],
    'importance_type': 'coefficient'
}).sort_values('coefficient', key=abs, ascending=False).head(20)

print("\nTop 20 features - Elastic Net:")
print(el_coef)

# Feature importance bar chart
blr_coef['model'] = 'Logistic Regression'
el_coef['model'] = 'Elastic Net'

all_features = pd.concat([blr_coef[['feature', 'coefficient', 'model']], 
                          el_coef[['feature', 'coefficient', 'model']]])

top_n = 15
all_top_features = list(blr_coef['feature'].head(top_n)) + list(el_coef['feature'].head(top_n))
unique_features = list(dict.fromkeys(all_top_features))[:top_n]

plt.figure(figsize=(12, 6))
for model in ['Logistic Regression', 'Elastic Net']:
    model_data = all_features[all_features['model'] == model]
    model_coefs = []
    for feat in unique_features:
        coef = model_data[model_data['feature'] == feat]['coefficient'].values
        model_coefs.append(coef[0] if len(coef) > 0 else 0)
    plt.bar(unique_features, model_coefs, label=model, alpha=0.7)
plt.title(f'Top {top_n} Feature Coefficients Comparison')
plt.xlabel("Feature")
plt.ylabel("Coefficient")
plt.xticks(rotation=45, ha='right')
plt.legend()
plt.show()

## Calibration
## -----------------------------------------------------------------------------
# Predictions on test and calibration data
el_test_pred = pd.DataFrame({
    '.row': X_test.index,
    'el': el_pred_proba,
    'event_1y': y_test.values
})

el_cal_pred_proba = el_final.predict_proba(preprocessor.transform(X_cal))[:, 1]
el_cal_pred = pd.DataFrame({
    'el': el_cal_pred_proba,
    'event_1y': y_cal.values
})

calibrated_el = CalibratedClassifierCV(
    Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(
            penalty='elasticnet',
            C=best_params['C'],
            l1_ratio=best_params['l1_ratio'],
            solver='saga',
            max_iter=1000,
            random_state=42
        ))
    ]),
    method='sigmoid',
    cv=2
)
calibrated_el.fit(X_cal, y_cal)

el_cal_pred['el_calibrated'] = calibrated_el.predict_proba(X_cal)[:, 1]
el_test_pred['el_calibrated'] = calibrated_el.predict_proba(X_test)[:, 1]

# Calibration plots for calibration data (side by side)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Uncalibrated - calibration data
prob_true_uncal, prob_pred_uncal = calibration_curve(el_cal_pred['event_1y'], el_cal_pred['el'], n_bins=20)
ax1.plot(prob_pred_uncal, prob_true_uncal, 'o-', label='Uncalibrated')
ax1.plot([0, 1], [0, 1], 'k--', label='Perfect')
ax1.set_xlabel('Mean predicted probability')
ax1.set_ylabel('Fraction of positives')
ax1.set_xlim([0, 1])
ax1.set_ylim([0, 1])
ax1.set_title("Calibration - Uncalibrated Elastic Net (Calibration Data)")
ax1.legend()

# Calibrated - calibration data
prob_true_cal, prob_pred_cal = calibration_curve(el_cal_pred['event_1y'], el_cal_pred['el_calibrated'], n_bins=20)
ax2.plot(prob_pred_cal, prob_true_cal, 'o-', label='Calibrated')
ax2.plot([0, 1], [0, 1], 'k--', label='Perfect')
ax2.set_xlabel('Mean predicted probability')
ax2.set_ylabel('Fraction of positives')
ax2.set_xlim([0, 1])
ax2.set_ylim([0, 1])
ax2.set_title("Calibration - Calibrated Elastic Net (Calibration Data)")
ax2.legend()

plt.tight_layout()
plt.show()

# Scatter plot: raw vs calibrated
plt.figure()
colors = {'0': 'blue', '1': 'red'}
for event in [0, 1]:
    mask = el_cal_pred['event_1y'] == event
    plt.scatter(el_cal_pred.loc[mask, 'el'], el_cal_pred.loc[mask, 'el_calibrated'], 
                color=colors[str(event)], label=f'Event={event}', alpha=0.5)
plt.plot([0, 1], [0, 1], 'k--', label='y=x')
plt.title("Raw vs Calibrated Probabilities (Calibration Data)")
plt.xlabel('Raw Probability')
plt.ylabel('Calibrated Probability')
plt.legend()
plt.show()

# Final calibration plots for test data (side by side)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Uncalibrated - test data
prob_true_t_uncal, prob_pred_t_uncal = calibration_curve(el_test_pred['event_1y'], el_test_pred['el'], n_bins=20)
ax1.plot(prob_pred_t_uncal, prob_true_t_uncal, 'o-', label='Uncalibrated')
ax1.plot([0, 1], [0, 1], 'k--', label='Perfect')
ax1.set_xlabel('Mean predicted probability')
ax1.set_ylabel('Fraction of positives')
ax1.set_xlim([0, 1])
ax1.set_ylim([0, 1])
ax1.set_title("Calibration Plot - Uncalibrated Elastic Net")
ax1.legend()

# Calibrated - test data
prob_true_t_cal, prob_pred_t_cal = calibration_curve(el_test_pred['event_1y'], el_test_pred['el_calibrated'], n_bins=20)
ax2.plot(prob_pred_t_cal, prob_true_t_cal, 'o-', label='Calibrated')
ax2.plot([0, 1], [0, 1], 'k--', label='Perfect')
ax2.set_xlabel('Mean predicted probability')
ax2.set_ylabel('Fraction of positives')
ax2.set_xlim([0, 1])
ax2.set_ylim([0, 1])
ax2.set_title("Calibration Plot - Calibrated Elastic Net")
ax2.legend()

plt.tight_layout()
plt.show()
