import os
import pickle
from threading import Thread

import numpy as np
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, precision_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from commons.aws.dynamodb_helper import get_all_elements_from_table
from commons.aws.s3_helper import get_file, put_file, put_json
from commons.logger import logged, logger
from commons.settings import settings

AI_BUCKET = os.environ['AI_BUCKET_NAME']
FINGERPRINT_TABLE = os.environ['DYNAMODB_FINGERPRINTS']

MACS_5GHZ = settings['MACS_5GHZ'].split(',')
MACS_2_4GHZ = settings['MACS_2_4GHZ'].split(',')
FINGERPRINT_NULL_VALUE = int(settings['FINGERPRINT_NULL_VALUE'])

class AIEngine():

    def __init__(self, is_5ghz=True):
        # Try to restore context from S3
        self.is_5ghz = is_5ghz
        
        self.ai_s3_path = f'ai/{"5ghz" if is_5ghz else "2_4ghz"}'

        downloaded_data = get_file(AI_BUCKET, f'{self.ai_s3_path}/context.ai')
        if not downloaded_data:
            self.algorithms = {
                'Nearest Neighbors': None,
                'Decision Tree': None,
                'Lineal SVM': None,
                'Random Forest': None,
                'Neural Net': None,
                'AdaBoost': None
            }
            self.headers = {}
            self.youden_indexes = {
                'Nearest Neighbors': 1,
                'Decision Tree': 1,
                'Lineal SVM': 1,
                'Random Forest': 1,
                'Neural Net': 1,
                'AdaBoost': 1
            },
            self.label_mapping = {}
        else:
            saved_data = pickle.loads(downloaded_data)
            self.headers = saved_data['headers']
            self.algorithms = saved_data['algorithms']
            self.youden_indexes = saved_data['youden_indexes']
            self.label_mapping = saved_data['label_mapping']

    def save_context(self):
        save_data = {
            'headers': self.headers,
            'algorithms': self.algorithms,
            'youden_indexes': self.youden_indexes,
            'label_mapping': self.label_mapping
        }
        save_data = pickle.dumps(save_data)
        put_file(AI_BUCKET, f'{self.ai_s3_path}/context.ai', save_data)

    @logged
    def get_datasets(self):
        dynamo_data = get_all_elements_from_table(FINGERPRINT_TABLE)
        filtered_macs = MACS_5GHZ + MACS_2_4GHZ if self.is_5ghz else MACS_2_4GHZ

        X = dynamo_data[filtered_macs].fillna(FINGERPRINT_NULL_VALUE)

        self.headers = self.create_headers(list(X))

        raw_y = np.array(dynamo_data['result'])

        self.label_mapping = {'from': {}, 'to': {}}
        numerical_label = 0

        y = np.zeros(raw_y.shape)
        for index, label in enumerate(raw_y):
            if label not in self.label_mapping['from']:
                self.label_mapping['from'][label] = numerical_label
                self.label_mapping['to'][numerical_label] = label
                numerical_label += 1
            y[index] = self.label_mapping['from'][label]

        X = np.array(X)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2)
        
        return X_train, X_test, X_val, y_train, y_test, y_val

    @logged
    def create_headers(self, headers_list):
        headers_dict = {}

        for index, header in enumerate(headers_list):
            headers_dict[header] = index
        
        return headers_dict

    @logged
    def youden_statistic(self, y_test, y_hat):
        return balanced_accuracy_score(y_test, y_hat, adjusted=True)

        # TP = 0
        # FP = 0
        # TN = 0
        # FN = 0
        # for i in range(len(y_hat)): 
        #     if y_test[i]==y_hat[i]==1:
        #         TP += 1
        #     if y_hat[i]==1 and y_test[i]!=y_hat[i]:
        #         FP += 1
        #     if y_test[i]==y_hat[i]==0:
        #         TN += 1
        #     if y_hat[i]==0 and y_test[i]!=y_hat[i]:
        #         FN += 1

        # sensitivity = 0
        # if TP + FN != 0:
        #     sensitivity = TP / (TP + FN)

        # specificity = 0
        # if TN + FP != 0:
        #     specificity = TN / (TN + FP)

        # return specificity + sensitivity - 1 

    @logged
    def train(self):
        X_train, X_test, X_val, y_train, y_test, y_val = self.get_datasets()

        models = {
            'Nearest Neighbors': KNeighborsClassifier(3),
            'Decision Tree': DecisionTreeClassifier(max_depth=5),
            'Lineal SVM': SVC(kernel="linear", C=0.025, probability=True),
            'Random Forest': RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
            'Neural Net': MLPClassifier(alpha=1, max_iter=1000),
            'AdaBoost': AdaBoostClassifier()
        }

        for name, model in models.items():
            try:
                self.algorithms[name] = model.fit(X_train,y_train)
            except Exception as e:
                logger.error(str(e))

        results = {}

        for model_name in self.algorithms.keys():
            results[model_name] = self.algorithms[model_name].predict(X_test)

        self.youden_indexes = {}

        for model_name in self.algorithms.keys():
            self.youden_indexes[model_name] = self.youden_statistic(y_test, results[model_name])

        self.save_train_stats(X_val, y_val)

        self.save_context()

    def save_train_stats(self, X_val, y_val):
        y_final, _ = self.classify(X_val)

        labels = list(self.label_mapping['from'].keys())

        precision = precision_score(y_val, y_final, average='macro')
        classification_report_json = classification_report(
            y_val, y_final, target_names=labels, output_dict=True
        )

        stats = {
            'precision': precision,
            'classification_report': classification_report_json
        }

        put_json(AI_BUCKET, f'{self.ai_s3_path}/stats.json', stats)   

    def classify_single_model(self, X_val, model_name, model, model_results):
        model_results[model_name] = model.predict_proba(X_val)

    def classify(self, X_val):
        model_results = {}

        threads = [None]*len(self.algorithms)

        for i, model_name in enumerate(self.algorithms.keys()):
            threads[i] = Thread(
                target=self.classify_single_model, 
                args=(X_val, model_name, self.algorithms[model_name], model_results)
            )
            threads[i].start()

        for thread in threads:
            thread.join()

        shape = np.shape(model_results[model_name])

        probabilities = np.zeros(shape)

        for model_name, model_result in model_results.items():
            probabilities = probabilities + model_result * self.youden_indexes[model_name]

        probabilities = probabilities / len(model_results)

        y_final = np.argmax(probabilities, axis=1)
        
        return y_final, probabilities

    def prepare_fingerprint(self, raw_fingerprint):
        fingerprint = np.zeros(len(self.headers)) + FINGERPRINT_NULL_VALUE

        filtered_macs = MACS_5GHZ + MACS_2_4GHZ if self.is_5ghz else MACS_2_4GHZ

        wifi_fingerprint = {
            mac:rss 
            for mac,rss in raw_fingerprint.get('wifi', {}).items() 
            if mac in filtered_macs
        }

        for mac, rss in wifi_fingerprint.items():
            fingerprint[self.headers[mac]] = rss

        bt_fingerprint = {
            mac:rss 
            for mac,rss in raw_fingerprint.get('bt', {}).items() 
            if mac in filtered_macs
        }

        for mac, rss in bt_fingerprint.items():
            fingerprint[self.headers[mac]] = rss

        return [fingerprint]
        
    @logged
    def localize_fingerprint(self, fingerprint):
        classification, raw_probabilities = self.classify(fingerprint)

        classification = classification[0]
        raw_probabilities = raw_probabilities[0]


        probabilities = {
            self.label_mapping['to'][index]: probability
            for index, probability in enumerate(raw_probabilities)
        }

        return self.label_mapping['to'][classification], probabilities
