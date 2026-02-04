import math

def calculate_metrics(tp: int, fp: int, tn: int, fn: int):

    if (tp + fp + tn + fn) == 0:
        return {"error": "Total predictions cannot be zero."}

    # Total number of observations
    total = tp + fp + tn + fn

    # 1. Accuracy: Overall correctness of the model.
    # Formula: (TP + TN) / Total
    accuracy = (tp + tn) / total if total > 0 else 0

    # 2. Sensitivity (Recall): Ability of the model to find all positive samples.
    # Formula: TP / (TP + FN) - True Positive Rate (TPR)
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

    # 3. Specificity: Ability of the model to correctly identify negative samples.
    # Formula: TN / (TN + FP) - True Negative Rate (TNR)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

    # 4. Precision: Ability of the model not to label as positive a sample that is negative.
    # Formula: TP / (TP + FP)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0

    # 5. F1 Score: The harmonic mean of Precision and Sensitivity (Recall).
    # Formula: 2 * (Precision * Recall) / (Precision + Recall)
    if (precision + sensitivity) > 0:
        f1_score = 2 * (precision * sensitivity) / (precision + sensitivity)
    else:
        f1_score = 0

    return {
        "Accuracy": accuracy,
        "Sensitivity (Recall)": sensitivity,
        "Specificity": specificity,
        "Precision": precision,
        "F1 Score": f1_score,
    }

def print_results(title, metrics, tp, fp, tn, fn):
    """Formats and prints the calculated metrics."""
    print(f"\n--- {title} ---")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print("-" * (len(title) + 8))
    for metric, value in metrics.items():
        # Displaying values with 4 decimal places for clarity
        print(f"{metric:<25}: {value:.4f}")
    print("-" * (len(title) + 8))


# Example 1: The distribution shown in the provided image (TP=10, FP=20, TN=75, FN=0)
tp_1, fp_1, tn_1, fn_1 = 10, 20, 75, 4
metrics_1 = calculate_metrics(tp_1, fp_1, tn_1, fn_1)
print_results("User's Original Distribution", metrics_1, tp_1, fp_1, tn_1, fn_1)


