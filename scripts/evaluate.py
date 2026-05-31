import json
import sys
import pandas as pd
sys.path.insert(0, '.')
from steps.predict import Predictor
from steps.clean import Cleaner

cleaner = Cleaner()
test_data = cleaner.clean_data(pd.read_csv('data/test.csv'))
predictor = Predictor()
X_test, y_test = predictor.feature_target_separator(test_data)
accuracy, class_report, roc_auc = predictor.evaluate_model(X_test, y_test)
metrics = {'accuracy': accuracy, 'roc_auc': roc_auc}
with open('metrics.json', 'w') as f:
    json.dump(metrics, f)
print(f'Accuracy: {accuracy:.4f}, ROC AUC: {roc_auc:.4f}')