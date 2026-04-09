
""" Student Performance Prediction

Run locally or in Colab to train a quick baseline model on the Student Performance Datasets

Example: Python studentperform.py --csv data/student-mat.csv --target G3 --problem auto 
"""

import argparse
from pathlib import Path

import matplotlib

# Use a non-interactive backend so plots save correctly in headless runs. 

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Log
from sklearn.metrics import(
    ConfusionMatrixDisplay
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

def infer_problem_type(y: pd.Series) -> str:
    """ Infer whether the task is classfication or regression based on the target."""

    if pd.api.types.is_numeric_dtype(y):

        # If numeric but only a few uniques values, treat as classification

        unique_count = y.nunique(dropna = True)
        return 'classification' if unique_count <= 10 else 'regression'
    return 'classification'
    
   