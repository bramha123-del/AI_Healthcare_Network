import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score

df = pd.read_csv("heart.csv")
X = df.drop("target", axis=1)
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

models = {
    "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
}

best_name, best_model, best_f1 = None, None, 0
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    f1 = f1_score(y_test, pred)
    print("\n====", name, "====")
    print(classification_report(y_test, pred))
    if f1 > best_f1:
        best_name, best_model, best_f1 = name, model, f1

print("Best model:", best_name, "F1:", round(best_f1, 3))
joblib.dump({"model": best_model, "columns": list(X.columns)}, "../2_backend/model.pkl")
print("Saved model.pkl")