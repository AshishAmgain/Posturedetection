import joblib
import numpy as np

# Model path
model_path = "./models/exercise_classifier.pkl"

# Load the trained model
try:
    model = joblib.load(model_path)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {model_path}. Please train the model first.")
    exit()
except Exception as e:
    print(f"An error occurred while loading the model: {e}")
    exit()

# Test the model with dummy data
# Replace this with actual features for testing
dummy_features = np.random.rand(1, 99)  # Assuming 33 landmarks (x, y, z) = 99 features
try:
    prediction = model.predict(dummy_features)
    print("Prediction:", prediction)
except Exception as e:
    print(f"Error during prediction: {e}")
