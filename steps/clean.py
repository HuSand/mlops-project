import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

class Cleaner:
    def __init__(self):
        self.num_imputer = SimpleImputer(strategy='mean')
        self.cat_imputer = SimpleImputer(strategy='most_frequent')

    def clean_data(self, data):
        columns_to_drop = ['id', 'SalesChannelID', 'VehicleAge', 'DaysSinceCreated']
        data = data.drop(columns=columns_to_drop, errors='ignore')
        feature_cols = [col for col in data.columns if col != 'target']
        
        # Pisahkan kolom numerik dan kategorik
        num_cols = data[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = data[feature_cols].select_dtypes(exclude=[np.number]).columns.tolist()

        # Impute numerik dengan mean
        if num_cols:
            data[num_cols] = self.num_imputer.fit_transform(data[num_cols])

        # Impute kategorik dengan most_frequent
        if cat_cols:
            data[cat_cols] = self.cat_imputer.fit_transform(data[cat_cols])

        # Clean target
        if 'target' in data.columns:
            data['target'] = pd.to_numeric(data['target'], errors='coerce')
            data = data.dropna(subset=['target'])
            data['target'] = data['target'].astype(int)

        data = data.drop_duplicates().reset_index(drop=True)
        return data