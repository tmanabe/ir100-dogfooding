#!/usr/bin/env python3

from gloves.nlp import whitespace_tokenizer
from gloves.scoring import idf
from gloves.scoring import bm25_weight
from statistics import mean
from statistics import pvariance
from .subjects import merged_us


def test_0():
    global merged_us_train
    global merged_us_test
    merged_us_train = merged_us["train" == merged_us.split]
    merged_us_test = merged_us["test" == merged_us.split]


FEATURES = [
    "title_tf_sum",
    "title_tf_avg",
    "title_tf_var",
    "title_tfidf_sum",
    "title_tfidf_avg",
    "title_tfidf_var",
    "title_bm25_sum",
    "title_bm25_avg",
    "title_bm25_var",
    "desc_tf_sum",
    "desc_tf_avg",
    "desc_tf_var",
    "desc_tfidf_sum",
    "desc_tfidf_avg",
    "desc_tfidf_var",
    "desc_bm25_sum",
    "desc_bm25_avg",
    "desc_bm25_var",
    "title_len",
    "desc_len",
]


def _test_1():
    FIELD_NAMES = {  # Short name -> DataFrame column name
        "title": "product_title",
        "desc": "product_description",
    }
    POOLING = {  # Short name -> Function
        "sum": sum,
        "avg": mean,
        "var": pvariance,
    }

    def extract_dfs(field_name, dataframe):
        sum_len, dfs = 0, {}
        for field_value in dataframe[FIELD_NAMES[field_name]]:
            if field_value is None:
                continue
            words = set()
            for word in whitespace_tokenizer(field_value):
                sum_len += 1
                words.add(word)
            for word in words:
                if word in dfs:
                    dfs[word] += 1
                else:
                    dfs[word] = 1
        return len(dataframe), sum_len / len(dataframe), dfs

    def name(field_name, feature, pooling=None):
        if pooling is None:
            return "_".join([field_name, feature])
        else:
            return "_".join([field_name, feature, pooling])

    def extract_features(field_name, dataframe, N, avg_len, dfs):
        features = {}
        for feature in ("tf", "tfidf", "bm25"):
            for pooling in POOLING.keys():
                features[name(field_name, feature, pooling)] = []
        features[name(field_name, "len")] = []

        for query, field_value in zip(dataframe["query"], dataframe[FIELD_NAMES[field_name]]):
            length, tfs = 0, {}
            if field_value is not None:
                for word in whitespace_tokenizer(field_value):
                    length += 1
                    if word in tfs:
                        tfs[word] += 1
                    else:
                        tfs[word] = 1
            tfs = [tfs.get(keyword, 0) for keyword in whitespace_tokenizer(query)]
            idfs = [idf(N, dfs.get(keyword, 0)) for keyword in whitespace_tokenizer(query)]
            tfidfs = [tf * idf_ for tf, idf_ in zip(tfs, idfs)]
            bm25_weights = [bm25_weight(tf, 1.2, 0.75, length, avg_len) for tf in tfs]
            for feature, data in {"tf": tfs, "tfidf": tfidfs, "bm25": bm25_weights}.items():
                for pooling, func in POOLING.items():
                    features[name(field_name, feature, pooling)].append(func(data))
            features[name(field_name, "len")].append(length)
        return features

    for field_name in FIELD_NAMES.keys():
        N, avg_len, dfs = extract_dfs(field_name, merged_us_train)  # Share IDFs and avg_len from training data
        for dataframe in (merged_us_train, merged_us_test):
            for column_name, data in extract_features(field_name, dataframe, N, avg_len, dfs).items():
                dataframe[column_name] = data


def test_2():
    # Share min. and max. values from training data
    min_values = {feature: merged_us_train[feature].min() for feature in FEATURES}
    max_values = {feature: merged_us_train[feature].max() for feature in FEATURES}
    for dataframe in (merged_us_train, merged_us_test):
        for feature in FEATURES:
            dataframe[feature] -= min_values[feature]
            dataframe[feature] /= max_values[feature] - min_values[feature]
