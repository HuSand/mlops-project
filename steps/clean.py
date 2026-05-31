import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

class Cleaner:
    def __init__(self):
        self.imputer = SimpleImputer(strategy='mean', missing_values=np.nan)

    def clean_data(self, data):
        feature_cols = [col for col in data.columns if col != 'target']

        # Konversi ke numeric
        data[feature_cols] = data[feature_cols].apply(pd.to_numeric, errors='coerce')
        data['target'] = pd.to_numeric(data['target'], errors='coerce')

        # Drop baris yang target-nya NaN (tidak bisa di-impute)
        data = data.dropna(subset=['target'])
        data['target'] = data['target'].astype(int)

        data = data.drop_duplicates().reset_index(drop=True)
        data[feature_cols] = self.imputer.fit_transform(data[feature_cols])

        return data