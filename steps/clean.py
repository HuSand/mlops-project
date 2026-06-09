import re
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer


class Cleaner:
    def __init__(self):
        pass

    def clean_data(self, data):
        # Drop kolom yang tidak diperlukan
        cols_to_drop = ['id', 'SalesChannelID', 'VehicleAge', 'DaysSinceCreated']
        data = data.drop(columns=[c for c in cols_to_drop if c in data.columns])

        # Fix AnnualPremium — hapus karakter non-numerik
        if 'AnnualPremium' in data.columns:
            data['AnnualPremium'] = data['AnnualPremium'].astype(str).apply(
                lambda x: re.sub(r'[^\d.]', '', x)
            )
            data['AnnualPremium'] = pd.to_numeric(data['AnnualPremium'], errors='coerce').astype(float)

            # Remove outliers menggunakan IQR
            Q1 = data['AnnualPremium'].quantile(0.25)
            Q3 = data['AnnualPremium'].quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            data = data[data['AnnualPremium'] <= upper_bound]

        # Impute Gender dan PastAccident dengan most_frequent / 'Unknown'
        if 'Gender' in data.columns:
            data['Gender'] = data['Gender'].fillna(
                data['Gender'].mode()[0] if not data['Gender'].mode().empty else 'Male'
            )

        if 'PastAccident' in data.columns:
            data['PastAccident'] = data['PastAccident'].fillna('Unknown')

        # Impute Age dengan median
        if 'Age' in data.columns:
            data['Age'] = pd.to_numeric(data['Age'], errors='coerce')
            data['Age'] = data['Age'].fillna(data['Age'].median())

        # Impute HasDrivingLicense dengan 1
        if 'HasDrivingLicense' in data.columns:
            data['HasDrivingLicense'] = pd.to_numeric(data['HasDrivingLicense'], errors='coerce')
            data['HasDrivingLicense'] = data['HasDrivingLicense'].fillna(1)

        # Impute Switch dengan -1
        if 'Switch' in data.columns:
            data['Switch'] = pd.to_numeric(data['Switch'], errors='coerce')
            data['Switch'] = data['Switch'].fillna(-1)

        # Impute RegionID dengan median
        if 'RegionID' in data.columns:
            data['RegionID'] = pd.to_numeric(data['RegionID'], errors='coerce')
            data['RegionID'] = data['RegionID'].fillna(data['RegionID'].median())

        # Drop target NaN kalau ada
        if 'target' in data.columns:
            data['target'] = pd.to_numeric(data['target'], errors='coerce')
            data = data.dropna(subset=['target'])
            data['target'] = data['target'].astype(int)

        data = data.drop_duplicates().reset_index(drop=True)
        return data