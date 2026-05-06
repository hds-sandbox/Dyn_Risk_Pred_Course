## -----------------------------------------------------------------------------
## Import packages
## -----------------------------------------------------------------------------
import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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
## Helper function to create PR curve with Plotly
## -----------------------------------------------------------------------------
def plot_pr_curve(y_true, y_scores, name, title):
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recall, y=precision, mode='lines', name=name,
        line=dict(color='blue' if 'Logistic' in name else 'red')
    ))
    fig.update_layout(
        title=title,
        xaxis_title='Recall',
        yaxis_title='Precision',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1.05])
    )
    fig.add_hline(y=1, line_dash="dot", line_color="gray")
    return fig

## -----------------------------------------------------------------------------
## Helper function to create ROC curve with Plotly
## -----------------------------------------------------------------------------
def plot_roc_curve(y_true, y_scores, name, title):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr, mode='lines', name=name,
        line=dict(color='blue' if 'Logistic' in name else 'red')
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Random', showlegend=False
    ))
    fig.update_layout(
        title=title,
        xaxis_title='False Positive Rate',
        yaxis_title='True Positive Rate',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1.05])
    )
    return fig

## -----------------------------------------------------------------------------
## Helper function to create calibration curve with Plotly
## -----------------------------------------------------------------------------
def plot_calibration_curve(y_true, y_prob, n_bins=20, name='', title=''):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prob_pred, y=prob_true, mode='markers+lines',
        name=name, marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Perfectly calibrated', showlegend=True
    ))
    fig.update_layout(
        title=title,
        xaxis_title='Mean predicted probability',
        yaxis_title='Fraction of positives',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1])
    )
    return fig

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
fig_pr_blr = plot_pr_curve(
    y_val, blr_val_pred_proba, 
    "Logistic Regression", 
    "Precision-Recall Curve - Logistic Regression"
)

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

# Performance metrics barplot with Plotly
fig_bar = go.Figure()
colors = {'precision': 'blue', 'roc_auc': 'green', 'pr_auc': 'orange', 'brier': 'red'}
metrics_order = ['precision', 'roc_auc', 'pr_auc', 'brier']

for metric in metrics_order:
    metric_data = results[results['.metric'] == metric]
    fig_bar.add_trace(go.Bar(
        x=metric_data['model'],
        y=metric_data['.estimate'],
        name=metric,
        marker_color=colors[metric]
    ))

fig_bar.update_layout(
    title="Performance Metrics by Model",
    xaxis_title="Model",
    yaxis_title="Score",
    yaxis=dict(range=[0, 1.1]),
    barmode='group'
)
# PR curve for both models
precision_blr, recall_blr, _ = precision_recall_curve(y_test, blr_pred_proba)
precision_el, recall_el, _ = precision_recall_curve(y_test, el_pred_proba)

fig_pr_both = go.Figure()
fig_pr_both.add_trace(go.Scatter(
    x=recall_blr, y=precision_blr, mode='lines', name='Logistic',
    line=dict(color='blue')
))
fig_pr_both.add_trace(go.Scatter(
    x=recall_el, y=precision_el, mode='lines', name='Elastic Net',
    line=dict(color='red')
))
fig_pr_both.update_layout(
    title="Precision-Recall Curve Comparison",
    xaxis_title='Recall',
    yaxis_title='Precision',
    xaxis=dict(range=[0, 1]),
    yaxis=dict(range=[0, 1.05])
)
fig_pr_both.add_hline(y=1, line_dash="dot", line_color="gray")

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

## -----------------------------------------------------------------------------

# Feature importance bar chart
# Combine feature importance data for both models
blr_coef['model'] = 'Logistic Regression'
el_coef['model'] = 'Elastic Net'

# Merge and get unique top features from both models
all_features = pd.concat([blr_coef[['feature', 'coefficient', 'model']], \
                          el_coef[['feature', 'coefficient', 'model']]])

# For cleaner visualization, get top N features that appear in either model
top_n = 15
# Get union of top features
all_top_features = list(blr_coef['feature'].head(top_n)) + list(el_coef['feature'].head(top_n))
unique_features = list(dict.fromkeys(all_top_features))[:top_n]  # Keep order, remove duplicates

# Create figure
fig_feat = go.Figure()

for model in ['Logistic Regression', 'Elastic Net']:
    model_data = all_features[all_features['model'] == model]
    # Get coefficients for the unique features
    model_coefs = []
    for feat in unique_features:
        coef = model_data[model_data['feature'] == feat]['coefficient'].values
        model_coefs.append(coef[0] if len(coef) > 0 else 0)
    
    fig_feat.add_trace(go.Bar(
        x=unique_features,
        y=model_coefs,
        name=model,
        marker_color='lightblue' if model == 'Logistic Regression' else 'lightcoral'
    ))

fig_feat.update_layout(
    title=f'Top {top_n} Feature Coefficients Comparison',
    xaxis_title="Feature",
    yaxis_title="Coefficient",
    barmode='group',
    xaxis={'tickangle': -45},
    height=600
)
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

# Use CalibratedClassifierCV for calibration

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
fig_cal_calib = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        "Calibration - Uncalibrated Elastic Net (Calibration Data)",
        "Calibration - Calibrated Elastic Net (Calibration Data)"
    )
)

# Uncalibrated - calibration data
prob_true_uncal, prob_pred_uncal = calibration_curve(el_cal_pred['event_1y'], el_cal_pred['el'], n_bins=20)
fig_cal_calib.add_trace(
    go.Scatter(x=prob_pred_uncal, y=prob_true_uncal, mode='markers+lines',
               name='Uncalibrated', marker=dict(size=8)),
    row=1, col=1
)
fig_cal_calib.add_trace(
    go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
               line=dict(dash='dash', color='gray'),
               name='Perfect', showlegend=False),
    row=1, col=1
)

# Calibrated - calibration data
prob_true_cal, prob_pred_cal = calibration_curve(el_cal_pred['event_1y'], el_cal_pred['el_calibrated'], n_bins=20)
fig_cal_calib.add_trace(
    go.Scatter(x=prob_pred_cal, y=prob_true_cal, mode='markers+lines',
               name='Calibrated', marker=dict(size=8)),
    row=1, col=2
)
fig_cal_calib.add_trace(
    go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
               line=dict(dash='dash', color='gray'),
               name='Perfect', showlegend=False),
    row=1, col=2
)

fig_cal_calib.update_xaxes(range=[0, 1], title_text="Mean predicted probability", row=1, col=1)
fig_cal_calib.update_xaxes(range=[0, 1], title_text="Mean predicted probability", row=1, col=2)
fig_cal_calib.update_yaxes(range=[0, 1], title_text="Fraction of positives", row=1, col=1)
fig_cal_calib.update_yaxes(range=[0, 1], title_text="Fraction of positives", row=1, col=2)

# Scatter plot: raw vs calibrated
fig_scatter = px.scatter(
    el_cal_pred, x='el', y='el_calibrated', color='event_1y',
    title="Raw vs Calibrated Probabilities (Calibration Data)",
    labels={'el': 'Raw Probability', 'el_calibrated': 'Calibrated Probability', 'event_1y': 'Event'}
)
fig_scatter.add_trace(go.Scatter(
    x=[0, 1], y=[0, 1], mode='lines',
    line=dict(dash='dash', color='gray'),
    name='y=x', showlegend=True
))

# Final calibration plots for test data (side by side)
fig_test_calib = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        "Calibration Plot - Uncalibrated Elastic Net",
        "Calibration Plot - Calibrated Elastic Net"
    )
)

# Uncalibrated - test data
prob_true_t_uncal, prob_pred_t_uncal = calibration_curve(el_test_pred['event_1y'], el_test_pred['el'], n_bins=20)
fig_test_calib.add_trace(
    go.Scatter(x=prob_pred_t_uncal, y=prob_true_t_uncal, mode='markers+lines',
               name='Uncalibrated', marker=dict(size=8)),
    row=1, col=1
)
fig_test_calib.add_trace(
    go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
               line=dict(dash='dash', color='gray'),
               name='Perfect', showlegend=False),
    row=1, col=1
)

# Calibrated - test data
prob_true_t_cal, prob_pred_t_cal = calibration_curve(el_test_pred['event_1y'], el_test_pred['el_calibrated'], n_bins=20)
fig_test_calib.add_trace(
    go.Scatter(x=prob_pred_t_cal, y=prob_true_t_cal, mode='markers+lines',
               name='Calibrated', marker=dict(size=8)),
    row=1, col=2
)
fig_test_calib.add_trace(
    go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
               line=dict(dash='dash', color='gray'),
               name='Perfect', showlegend=False),
    row=1, col=2
)

fig_test_calib.update_xaxes(range=[0, 1], title_text="Mean predicted probability", row=1, col=1)
fig_test_calib.update_xaxes(range=[0, 1], title_text="Mean predicted probability", row=1, col=2)
fig_test_calib.update_yaxes(range=[0, 1], title_text="Fraction of positives", row=1, col=1)
fig_test_calib.update_yaxes(range=[0, 1], title_text="Fraction of positives", row=1, col=2)

## -----------------------------------------------------------------------------
## Display all figures
## -----------------------------------------------------------------------------
print()
print("...Displaying all plots...")
print()

# Show all figures
fig_pr_blr.show()
fig_feat.show()
fig_bar.show()
fig_pr_both.show()
fig_cal_calib.show()
fig_scatter.show()
fig_test_calib.show()