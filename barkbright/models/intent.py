import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from barkbright.models import Model, random_state
from barkbright import colors, modes
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score
from dataset import bb_data_path, bb_data, BB_INTENTS
from xgboost import XGBClassifier
from typing import Tuple

asset_path = Path(__file__).parent / Path('assets')

class IntentMatchingModel(Model):

    def __init__(self, tf_params=None, clf_params=None, svd_params=None) -> None:
        super().__init__()
        token_pattern = r'(?u)\b\w\w+\b|<\w+>'

        self._tf_params = tf_params if tf_params else {
            'token_pattern':token_pattern,
        #     'max_df': 1,
        #     'min_df': 1,
            'ngram_range': (1,1),
        }

        self._clf_params = clf_params if clf_params else {
            'n_estimators': 5000,
            'max_depth': 6,
            'eval_metric': 'mlogloss',
            'early_stopping_rounds': 10,
            'random_state': random_state
        }

        self._svd_params = svd_params if svd_params else {
            'n_components': 25,
            'random_state': random_state
        }
        self._pre_pipe = Pipeline([
            ('tf', CountVectorizer(**self._tf_params)),
            ('svd', TruncatedSVD(**self._svd_params)),
            ('norm', StandardScaler())
        ])
        self._clf = XGBClassifier(**self._clf_params)
        self._pipe = Pipeline([
            ('pre', self._pre_pipe),
            ('clf', self._clf)
        ])
        self._le = LabelEncoder()
    
    def train(self, data_path=None, logging=True):
        df = None
        if data_path:
            df = pd.read_json(data_path)
        else:
            df = pd.DataFrame(bb_data)
        self._preprocess(df)
        X, y = (df['phrase'].values, df['intent'].values)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=random_state)
        X_train, y_train = self._random_upsample(X_train, y_train)
        if logging:
            print('Training Preprocessing Pipe...')
        self._pre_pipe.fit(X_train, y_train)
        if logging:
            print('Done')
            evr = self._pre_pipe.named_steps['svd'].explained_variance_ratio_ * 100
            num_feats = self._pre_pipe.named_steps['svd'].n_features_in_
            print(f'EVR: {evr.sum():.1f}\tNumber of Features: {num_feats}')
        X_train = self._pre_pipe.transform(X_train)
        X_test = self._pre_pipe.transform(X_test)
        y_train = self._le.fit_transform(y_train)
        y_test = self._le.transform(y_test)
        if logging:
            print('Training Model...')
        self._clf.fit(X_train, y_train, eval_set=[(X_test, y_test)])
        if logging:
            print('Done')
            y_pred = self._clf.predict(X_test)
            f1_test = f1_score(y_test, y_pred, average='micro')
            y_pred = self._clf.predict(X_train)
            f1_train = f1_score(y_train, y_pred, average='micro')
            print(f"F1 (Test): {f1_test}\tF1 (Train): {f1_train}")
    
    def save(self, model_name='intent_model'):
        self._clf.save_model(asset_path / f"{model_name}.xgb")
        with open(asset_path / f"{model_name}.prepipe", 'wb') as f:
            pickle.dump(self._pre_pipe, f)
        with open(asset_path / f"{model_name}.le", 'wb') as f:
            pickle.dump(self._le, f)
    
    def load(self, model_name='intent_model'):
        with open(asset_path / f"{model_name}.prepipe", 'rb') as f:
            self._pre_pipe = pickle.load(f)
        with open(asset_path / f"{model_name}.le", 'rb') as f:
            self._le = pickle.load(f)
        self._clf.load_model(asset_path / f"{model_name}.xgb")
        self._pipe = Pipeline([
            ('pre', self._pre_pipe),
            ('clf', self._clf)
        ])

    def update(self, df, model_name='intent_model'):
        with open(asset_path / f"{model_name}.prepipe", 'rb') as f:
            self._pre_pipe = pickle.load(f)
        with open(asset_path / f"{model_name}.le", 'rb') as f:
            self._le = pickle.load(f)
        self._preprocess(df)
        X, y = (df['phrase'].values, df['intent'].values)
        y = self._le.transform(y)
        X = self._pre_pipe.transform(X)
        self._clf_params['early_stopping_rounds'] = None
        self._clf_params['n_estimators'] = 20
        new_clf = XGBClassifier(**self._clf_params)
        new_clf.fit(X, y, xgb_model=asset_path / f"{model_name}.xgb")
        self._clf = new_clf
        self._pipe = Pipeline([
            ('pre', self._pre_pipe),
            ('clf', self._clf)
        ])

        

    def predict(self, phrases:list, threshold=0.2) -> np.ndarray:
        df = pd.DataFrame(phrases, columns=['phrase'])
        self._preprocess(df)
        y_pred = self._pipe.predict_proba(df['phrase'])
        pred = y_pred.argmax(axis=1, keepdims=True)
        avg = np.delete(y_pred, pred, axis=1).mean(axis=1, keepdims=True)
        labels = self._le.inverse_transform(pred.flatten())
        labels = np.expand_dims(labels, axis=1)
        pred_prob = np.take_along_axis(y_pred, pred, axis=1)
        labels = np.hstack([labels, pred_prob])
        unknown = np.argwhere(pred_prob - avg < threshold)
        labels[unknown] = ['unknown', -1]
        return labels


        

    def _preprocess(self, df:pd.DataFrame):
        df['phrase'] = df['phrase'].str.lower()
        df['phrase'] = df['phrase'].str.replace(r'\d+', '<number>', regex=True)
        for color in colors.KNOWN_COLORS:
            df['phrase'] = df['phrase'].str.replace(color, '<color>')
        for mode in modes.KNOWN_MODES:
            df['phrase'] = df['phrase'].str.replace(mode, '<mode>')

    def _random_upsample(self, X, y):
        classes, counts = np.unique(y, return_counts=True)
        maj_count = np.max(counts)
        X_list = list()
        y_list = list()
        for cls, count in zip(classes, counts):
            num_samps = maj_count - count
            if num_samps > 0:
                cls_indicies = np.argwhere(y == cls).flatten()
                cls_indicies = np.random.choice(cls_indicies, num_samps)
                X_list.append(X[cls_indicies])
                y_list.append(y[cls_indicies])
        X_resamp = np.concatenate([X] + X_list)
        y_resamp = np.concatenate([y] + y_list)
        return X_resamp, y_resamp
