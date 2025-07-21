import joblib
import os

BASE_DIR = os.path.dirname(__file__)

vectorizer = joblib.load(os.path.join(BASE_DIR, "vector.joblib"))
model = joblib.load(os.path.join(BASE_DIR, "model.joblib"))

label_map = {
    0: "negative",
    1: "neutral",
    2: "positive"
}

def predict_sentiment(text):
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    return label_map.get(pred, "neutral")
