from gloves.scoring import idf
from scipy.stats import binomtest
from scipy.stats import kstest
from scipy.stats import norm
from scipy.stats import ttest_rel
from .ndcg import ESCI_LABEL_TO_GAIN
from .ndcg import calc_dcgs_at
from .ndcg import calc_ndcgs
from .subjects import merged_us
from .subjects import products_us


def test_0():
    global baseline_rankings
    baseline_rankings = merged_us.sort_values(["query_id", "product_id"])


def test_1():
    def calc_tf(query, product_title):
        tf = 0
        keywords = set(query.split())
        for word in product_title.split():
            if word in keywords:
                tf += 1
        return tf

    def batch_tf(queries, product_titles):
        return [calc_tf(*pair) for pair in zip(queries, product_titles)]

    global improved_rankings
    improved_rankings = merged_us.assign(tf=batch_tf(merged_us["query"], merged_us["product_title"]))
    improved_rankings.sort_values(["query_id", "tf", "product_id"], ascending=[True, False, True], inplace=True)


def test_2():
    def calc_mean_precision_at(k, rankings):
        total_precision, query_count = 0.0, 0
        last_query_id, rank, relevant_count, count = None, 0, 0, 0
        for query_id, esci_label in zip(rankings["query_id"], rankings["esci_label"]):
            if last_query_id != query_id:
                if last_query_id is not None:
                    query_count += 1
                    total_precision += relevant_count / count
                last_query_id, rank, relevant_count, count = query_id, 0, 0, 0
            rank += 1
            if rank <= k:
                count += 1
                if "I" != esci_label:
                    relevant_count += 1
        if last_query_id is not None:
            query_count += 1
            total_precision += relevant_count / count
        if 0 < query_count:
            return total_precision / query_count
        else:
            return None

    print("2.")
    print(f"Baseline: {calc_mean_precision_at(10, baseline_rankings)}")
    print(f"Improved: {calc_mean_precision_at(10, improved_rankings)}")


def test_3():
    def calc_mean_average_precision(rankings):
        total_average_precision, query_count = 0.0, 0
        last_query_id, total_precision, relevant_count, count = None, 0.0, 0, 0
        for query_id, esci_label in zip(rankings["query_id"], rankings["esci_label"]):
            if last_query_id != query_id:
                if last_query_id is not None and 0 < relevant_count:
                    query_count += 1
                    total_average_precision += total_precision / relevant_count
                last_query_id, total_precision, relevant_count, count = (
                    query_id,
                    0.0,
                    0,
                    0,
                )
            count += 1
            if "I" != esci_label:
                relevant_count += 1
                total_precision += relevant_count / count
        if last_query_id is not None and 0 < relevant_count:
            query_count += 1
            total_average_precision += total_precision / relevant_count
        if 0 < query_count:
            return total_average_precision / query_count
        else:
            return None

    print("3.")
    print(f"Baseline: {calc_mean_average_precision(baseline_rankings)}")
    print(f"Improved: {calc_mean_average_precision(improved_rankings)}")


def test_4():
    print("4.")
    global baseline_dcgs
    baseline_dcgs = calc_dcgs_at(10, baseline_rankings)
    print(f"Baseline: {sum(baseline_dcgs) / len(baseline_dcgs)}")
    global improved_dcgs
    improved_dcgs = calc_dcgs_at(10, improved_rankings)
    print(f"Improved: {sum(improved_dcgs) / len(improved_dcgs)}")


def test_5():
    ideal_rankings = merged_us.assign(gain=[ESCI_LABEL_TO_GAIN[esci_label] for esci_label in merged_us["esci_label"]])
    ideal_rankings.sort_values(["query_id", "gain", "product_id"], ascending=[True, False, True], inplace=True)
    global ideal_dcgs
    ideal_dcgs = calc_dcgs_at(10, ideal_rankings)

    print("5.")
    global baseline_ndcgs
    baseline_ndcgs = calc_ndcgs(baseline_dcgs, ideal_dcgs)
    print(f"Baseline: {sum(baseline_ndcgs) / len(baseline_ndcgs)}")
    global improved_ndcgs
    improved_ndcgs = calc_ndcgs(improved_dcgs, ideal_dcgs)
    print(f"Improved: {sum(improved_ndcgs) / len(improved_ndcgs)}")


def test_6():
    assert len(baseline_ndcgs) == len(improved_ndcgs)
    baseline_count, improved_count = 0, 0
    for baseline_ndcg, improved_ndcg in zip(baseline_ndcgs, improved_ndcgs):
        if improved_ndcg < baseline_ndcg:
            baseline_count += 1
        if baseline_ndcg < improved_ndcg:
            improved_count += 1
    print("6.")
    print(f"Baseline: {baseline_count}")
    print(f"Improved: {improved_count}")
    print(binomtest(k=improved_count, n=baseline_count + improved_count))


def test_7():
    print("7.")
    print(ttest_rel(improved_ndcgs, baseline_ndcgs))


def test_8():
    def calc_df(product_title, results):
        for word in set(product_title.split()):
            if word in results:
                results[word] += 1
            else:
                results[word] = 1

    def batch_idf(product_titles):
        results = {}
        for product_title in product_titles:
            calc_df(product_title, results)
        N = len(product_titles)
        results = {word: idf(N, n) for word, n in results.items()}
        return results, idf(N, 0)

    def calc_tfidf(query, product_title, idfs, default_idf):
        tfs = {}
        for word in product_title.split():
            if word in tfs:
                tfs[word] += 1
            else:
                tfs[word] = 1
        tfidf = 0.0
        for keyword in set(query.split()):
            if keyword in tfs:
                tfidf += tfs[keyword] * idfs.get(keyword, default_idf)
        return tfidf

    def batch_tfidf(queries, product_titles, idfs, default_idf):
        return [
            calc_tfidf(query, product_title, idfs, default_idf) for query, product_title in zip(queries, product_titles)
        ]

    def bonferroni_correct(p, m):
        return p * m * (m - 1) / 2

    idfs, default_idf = batch_idf(products_us["product_title"])
    global re_improved_rankings
    re_improved_rankings = merged_us.assign(
        tfidf=batch_tfidf(merged_us["query"], merged_us["product_title"], idfs, default_idf)
    )
    re_improved_rankings.sort_values(["query_id", "tfidf", "product_id"], ascending=[True, False, True], inplace=True)

    print("8.")
    re_improved_dcgs = calc_dcgs_at(10, re_improved_rankings)
    re_improved_ndcgs = calc_ndcgs(re_improved_dcgs, ideal_dcgs)
    print(f"Re-improved: {sum(re_improved_ndcgs) / len(re_improved_ndcgs)}")

    result = ttest_rel(improved_ndcgs, baseline_ndcgs)
    print(f"Improved    vs. Baseline: {result} -> {bonferroni_correct(result.pvalue, 3)}")
    result = ttest_rel(re_improved_ndcgs, baseline_ndcgs)
    print(f"Re-improved vs. Baseline: {result} -> {bonferroni_correct(result.pvalue, 3)}")
    result = ttest_rel(re_improved_ndcgs, improved_ndcgs)
    print(f"Re-improved vs. Improved: {result} -> {bonferroni_correct(result.pvalue, 3)}")


def test_9():
    print("9.")
    print(kstest(baseline_ndcgs, norm.cdf))
    print(kstest(improved_ndcgs, norm.cdf))
