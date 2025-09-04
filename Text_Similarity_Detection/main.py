import pickle
import distance
from helper import query_point_creator

# Load your trained model (you must have trained & saved it from the notebook)
model = pickle.load(open("model.pkl", "wb"))
cv = pickle.load(open("cv.pkl", "wb"))
STOP_WORDS = pickle.load(open("stopwords.pkl", "wb"))

def check_duplicate(q1, q2):
    # Extract features using helper.py
    features = query_point_creator(q1, q2)
    # Predict using trained model
    pred = model.predict(features)[0]
    return "Duplicate" if pred == 1 else "Not Duplicate"

if __name__ == "__main__":
    print("=== Duplicate Question Checker ===")
    q1 = input("Enter first question: ")
    q2 = input("Enter second question: ")

    result = check_duplicate(q1, q2)
    print(f"\nResult: {result}")
