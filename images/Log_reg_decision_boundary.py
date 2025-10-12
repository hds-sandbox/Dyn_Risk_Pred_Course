import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
np.seterr(divide='ignore')

games = pd.read_csv("games").dropna()
games.head()

X = games[["GOAL_DIFF"]]
Y = games["WON"]

import sklearn.linear_model as lm


# Initialize a LogisticRegression object
model = lm.LogisticRegression()

# Fit the model to the data
model.fit(X, Y)

# Predict probabilities. We display only the first 5 rows for clarity
model.predict_proba(X)[:5, :]

p = model.predict_proba(X)[:, 1]

(p >= 0.5).astype(int)

classes = model.predict(X)
games["Predicted Class"] = classes

# Visualize our results
def sigmoid(z):
    return 1/(1+np.exp(-z))

plt.axvline(x=0.0, color='grey', linestyle=':', linewidth=1.5)

x = np.linspace(-0.3, 0.3)
custom_palette = {0: "salmon", 1: "lightgreen"}
sns.stripplot(data=games, x="GOAL_DIFF", y="WON", hue="Predicted Class", orient="h", palette=custom_palette)
plt.plot(x, sigmoid(model.intercept_ + model.coef_[0]*x), "k")
plt.gca().invert_yaxis();
plt.xlabel("$x_1$")
plt.ylabel("$x_2$")

plt.savefig('Log_reg_decision_boundary.png')

plt.show()