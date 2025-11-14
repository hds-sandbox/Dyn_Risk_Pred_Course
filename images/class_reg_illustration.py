import matplotlib.pyplot as plt
import numpy as np

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))


# Generate synthetic data for two classes
np.random.seed(0)
# Class 1
X1 = np.random.randn(50, 2) + np.array([2, 2])
# Class 2
X2 = np.random.randn(50, 2) + np.array([-2, -2])

# Plot the data
ax1.scatter(X1[:, 0], X1[:, 1], color='salmon', label='Class 1')
ax1.scatter(X2[:, 0], X2[:, 1], color='lightgreen', label='Class 0')

# --- Start of Classification Boundary Addition ---

# Define the range for the line using the current x-limits
x_min, x_max = ax1.get_xlim()
x_line = np.array([x_min, x_max])

# Define a simple diagonal line (e.g., x2 = -x1) for visualization
# The corresponding y values are -x_line
y_line = -x_line

# Plot the decision boundary line
ax1.plot(x_line, y_line, color='midnightblue', linestyle='--', label='Decision Boundary', linewidth=3)

# --- End of Classification Boundary Addition ---

ax1.set_title('Classification Problem')
ax1.set_xlabel('$x_1$')
ax1.set_ylabel('$x_2$')
ax1.legend()


# Generate synthetic data for regression
np.random.seed(42)
X_reg = np.linspace(0, 10, 100)
y_reg = 2 * X_reg + 1 + np.random.randn(100) * 2

# Plot the data points
ax2.scatter(X_reg, y_reg, color='blue', label='Data points')

# Fit a line to the data
m, c = np.polyfit(X_reg, y_reg, 1)
ax2.plot(X_reg, m * X_reg + c, color='midnightblue', linestyle='--', label='Fitted line', linewidth=3)

ax2.set_title('Regression Problem')
ax2.set_xlabel('$x$')
ax2.set_ylabel('y')
ax2.legend()

plt.savefig('class_vs_reg_own.png')

# Adjust layout and show the plot
plt.tight_layout()
plt.show()