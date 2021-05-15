#!/usr/bin/env python

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, roc_auc_score

class train_funcs():
    def __init__(self):
        pass

    def train_and_measure(model, cv, model_name, x_train, y_train):
        """[summary]

        Args:
            model ([ML model object])
            cv ([cross validation object])
            model_name ([string])
            x_train ([numpy object])
            y_train ([numpy object])

        Returns:
            [dict]: [model training metrics]
            [dict]: [model validation metrics]
        """
        train_scores = dict()
        val_scores = dict()

        train_acc_scores = list()
        train_roc_scores = list()
        train_mcc_scores = list()
        train_f1_scores = list()

        acc_scores = list()
        roc_scores = list()
        mcc_scores = list()
        f1_scores = list()

        # cross validation
        for train, val in cv.split(x_train, y_train):
            model.fit(x_train[train], y_train[train])

            # predict on validation set
            train_preds = model.predict(x_train[train])
            preds = model.predict(x_train[val])

            # store metrics
            train_acc = accuracy_score(train_preds, y_train[train])
            train_acc_scores.append(train_acc)
            val_acc = accuracy_score(preds, y_train[val])
            acc_scores.append(val_acc)

            train_f1 = f1_score(train_preds, y_train[train])
            train_f1_scores.append(train_f1)
            val_f1 = f1_score(preds, y_train[val])
            f1_scores.append(val_f1)

            train_roc = roc_auc_score(train_preds, y_train[train])
            train_roc_scores.append(train_roc)
            val_roc = roc_auc_score(preds, y_train[val])
            roc_scores.append(val_roc)

            train_mcc = matthews_corrcoef(train_preds, y_train[train])
            train_mcc_scores.append(train_mcc)
            mcc = matthews_corrcoef(preds, y_train[val])
            mcc_scores.append(mcc)

        # metrics
        train_scores[model_name] = {
            'acc': np.mean(train_acc_scores),
            'roc': np.mean(train_roc_scores),
            'f1': np.mean(train_f1_scores),
            'mcc': np.mean(train_mcc_scores)
        }

        val_scores[model_name] = {
            'acc': np.mean(acc_scores),
            'roc': np.mean(roc_scores),
            'f1': np.mean(f1_scores),
            'mcc': np.mean(mcc_scores)
        }

        return train_scores, val_scores
