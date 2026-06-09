import os
import joblib
import yaml
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

class Predictor:
    def __init__(self, load_immediately=True, pipeline=None):
        self.model_path = self.load_config()['model']['store_path']
        # Prioritaskan pipeline yang diberikan, kalau tidak ada baru load dari file
        if pipeline is not None:
            self.pipeline = pipeline
        elif load_immediately:
            self.pipeline = self.load_model()
        else:
            self.pipeline = None

    def load_config(self):
        with open('config.yml', 'r') as config_file:
            return yaml.safe_load(config_file)
        
    def load_model(self):
        model_file_path = os.path.join(self.model_path, 'model.pkl')
        if os.path.exists(model_file_path):
            return joblib.load(model_file_path)
        return None

    def feature_target_separator(self, data):
        X = data.iloc[:, :-1]
        y = data.iloc[:, -1]
        return X, y
    
    def evaluate_model(self, X_test, y_test):
        if self.pipeline is None:
            raise RuntimeError("Model tidak dimuat. Load model terlebih dahulu.")
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        class_report = classification_report(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred)
        return accuracy, class_report, roc_auc