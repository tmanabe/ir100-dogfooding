#!/usr/bin/env python3

from gloves.nlp import whitespace_tokenizer
from gloves.priority_queue import PriorityQueue
from gloves.scoring import idf
from gloves.scoring import bm25_weight
from sklearn.linear_model import LogisticRegression
from statistics import mean
from statistics import pvariance
from xgboost import XGBRanker
from .ndcg import ESCI_LABEL_TO_GAIN
from .ndcg import calc_dcgs_at
from .ndcg import calc_ndcgs
from .subjects import merged_us


def test_0():
    global merged_us_train
    global merged_us_test
    merged_us_train = merged_us["train" == merged_us.split].copy()
    merged_us_test = merged_us["test" == merged_us.split].copy()

    # For later test cases.
    merged_us_train.sort_values(["query_id", "product_id"], inplace=True)
    merged_us_test.sort_values(["query_id", "product_id"], inplace=True)
    global ideal_rankings
    ideal_rankings = merged_us_test.assign(
        gain=[
            ESCI_LABEL_TO_GAIN[esci_label]
            for esci_label in merged_us_test["esci_label"]
        ]
    ).sort_values(["query_id", "gain", "product_id"], ascending=[True, False, True])


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


def test_1():
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

        for query, field_value in zip(
            dataframe["query"], dataframe[FIELD_NAMES[field_name]]
        ):
            length, tfs = 0, {}
            if field_value is not None:
                for word in whitespace_tokenizer(field_value):
                    length += 1
                    if word in tfs:
                        tfs[word] += 1
                    else:
                        tfs[word] = 1
            tfs = [tfs.get(keyword, 0) for keyword in whitespace_tokenizer(query)]
            idfs = [
                idf(N, dfs.get(keyword, 0)) for keyword in whitespace_tokenizer(query)
            ]
            tfidfs = [tf * idf_ for tf, idf_ in zip(tfs, idfs)]
            bm25_weights = [
                bm25_weight(tf, 1.2, 0.75, length, avg_len) * idf_
                for tf, idf_ in zip(tfs, idfs)
            ]
            for feature, data in {
                "tf": tfs,
                "tfidf": tfidfs,
                "bm25": bm25_weights,
            }.items():
                for pooling, func in POOLING.items():
                    features[name(field_name, feature, pooling)].append(func(data))
            features[name(field_name, "len")].append(length)
        return features

    for field_name in FIELD_NAMES.keys():
        N, avg_len, dfs = extract_dfs(
            field_name, merged_us_train
        )  # Share IDFs and avg_len from training data
        for dataframe in (merged_us_train, merged_us_test):
            for column_name, data in extract_features(
                field_name, dataframe, N, avg_len, dfs
            ).items():
                dataframe[column_name] = data


def test_2():
    # Share min. and max. values from training data
    min_values = {feature: merged_us_train[feature].min() for feature in FEATURES}
    max_values = {feature: merged_us_train[feature].max() for feature in FEATURES}
    for dataframe in (merged_us_train, merged_us_test):
        for feature in FEATURES:
            dataframe[feature] -= min_values[feature]
            dataframe[feature] /= max_values[feature] - min_values[feature]


def test_3():
    global logistic_regression
    logistic_regression = LogisticRegression(max_iter=10000)
    logistic_regression.fit(
        merged_us_train[FEATURES],
        merged_us_train["esci_label"].map({"E": 1, "S": 1, "C": 1, "I": 0}),
    )


def test_4():
    relevant_class_index, relevant_logits = 0, []
    for class_ in logistic_regression.classes_:
        if 1 == class_:
            break
        relevant_class_index += 1
    for logits in logistic_regression.predict_log_proba(merged_us_test[FEATURES]):
        relevant_logits.append(logits[relevant_class_index])
    merged_us_test["logit"] = relevant_logits
    logit_rankings = merged_us_test.sort_values(
        ["query_id", "logit", "product_id"], ascending=[True, False, True]
    )
    logit_ndcgs = calc_ndcgs(
        calc_dcgs_at(10, logit_rankings),
        calc_dcgs_at(10, ideal_rankings),
    )
    print("4.")
    print(f"Logit: {sum(logit_ndcgs) / len(logit_ndcgs)}")


def eval_xgb_ranker(xgb_ranker, features):
    merged_us_test["xgb"] = xgb_ranker.predict(merged_us_test[features])
    xgb_rankings = merged_us_test.sort_values(
        ["query_id", "xgb", "product_id"], ascending=[True, False, True]
    )
    xgb_ndcgs = calc_ndcgs(
        calc_dcgs_at(10, xgb_rankings),
        calc_dcgs_at(10, ideal_rankings),
    )
    print(f"XGBoost: {sum(xgb_ndcgs) / len(xgb_ndcgs)}")


def test_5():
    print("5.")
    xgb_ranker = XGBRanker(objective="rank:ndcg")
    xgb_ranker.fit(
        merged_us_train[FEATURES],
        merged_us_train["esci_label"].map(ESCI_LABEL_TO_GAIN),
        qid=merged_us_train["query_id"],
        verbose=True,
    )
    eval_xgb_ranker(xgb_ranker, FEATURES)


def answer6(xgb_ranker, features):
    xgb_ranker.fit(
        merged_us_train_train[features],
        merged_us_train_train["esci_label"].map(ESCI_LABEL_TO_GAIN),
        qid=merged_us_train_train["query_id"],
        eval_set=[
            (
                merged_us_train_valid[features],
                merged_us_train_valid["esci_label"].map(ESCI_LABEL_TO_GAIN),
            ),
        ],
        eval_qid=[
            merged_us_train_valid["query_id"],
        ],
        verbose=True,
    )
    return xgb_ranker


def test_6():
    print("6.")
    global merged_us_train_train
    global merged_us_train_valid
    merged_us_train_train = merged_us_train[0 != merged_us_train["query_id"] % 5]
    merged_us_train_valid = merged_us_train[0 == merged_us_train["query_id"] % 5]

    xgb_ranker = XGBRanker(
        objective="rank:ndcg",
        learning_rate=0.03,
    )
    answer6(xgb_ranker, FEATURES)
    eval_xgb_ranker(xgb_ranker, FEATURES)

    # For 7.
    priority_queue = PriorityQueue(10)
    assert len(xgb_ranker.feature_importances_) == len(FEATURES)
    for pair in zip(xgb_ranker.feature_importances_, FEATURES):
        priority_queue.push(pair)

    global IMPORTANT_FEATURES
    IMPORTANT_FEATURES = []
    while 0 < len(priority_queue.body):
        _, feature = priority_queue.pop()
        IMPORTANT_FEATURES.append(feature)


def test_7():
    print("7.")
    print(IMPORTANT_FEATURES)
    xgb_ranker = XGBRanker(
        objective="rank:ndcg",
        learning_rate=0.03,
    )
    answer6(xgb_ranker, IMPORTANT_FEATURES)
    eval_xgb_ranker(xgb_ranker, IMPORTANT_FEATURES)
