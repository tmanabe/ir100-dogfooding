from gloves.ann import ANNInvertedIndexBuilder
from gloves.ann import BatchAnnoyIndexBuilder
from gloves.ann import BatchRankingBuilder
from gloves.ann import annoy_filter_factory
from gloves.ann import as_is_batch_tokenizer
from gloves.ann import use_batch_tokenizer
from gloves.iterator import boolean_or
from sklearn.cluster import KMeans
from time import time

from .subjects import sampled_products_us as products_us


def test_0():
    print("0.")
    print(
        use_batch_tokenizer(
            [
                "The quick brown fox jumps over the lazy dog.",
                "I am a sentence for which I would like to get its embedding",
            ]
        )
    )


# 1.
QUERIES = ["Information Science", "HDMI Cable"]
QUERY_VECTORS = use_batch_tokenizer(QUERIES)
assert len(QUERIES) == len(QUERY_VECTORS)


def test_1():
    print("1.")
    print(QUERIES)
    print(QUERY_VECTORS)


# 2.
K = 10


products_us = products_us.set_index("product_id", drop=False)
products_us.sort_index(inplace=True)


def print_rankings(rankings):
    assert len(QUERIES) == len(rankings)
    for query, ranking in zip(QUERIES, rankings):
        print(query)
        for priority, product_id in ranking:
            print(priority, product_id, products_us.at[product_id, "product_title"])


def test_2():
    print("2.")
    batch_ranking_builder = BatchRankingBuilder(QUERIES, len(QUERIES) * [K])
    for product_id, product_title in zip(products_us["product_id"], products_us["product_title"]):
        batch_ranking_builder.add(product_id, product_title)

    global exact_rankings  # For 7.
    exact_rankings = batch_ranking_builder.build()
    print_rankings(exact_rankings)


# 3.
METRIC = "euclidean"
N_TREES = 10


def test_3():
    print("3.")
    batch_annoy_index_builder = BatchAnnoyIndexBuilder(METRIC, N_TREES)
    for product_id, product_title in zip(products_us["product_id"], products_us["product_title"]):
        batch_annoy_index_builder.add(product_id, product_title)
    annoy_index, product_ids = batch_annoy_index_builder.build()

    approx_rankings = []
    for query, query_vector in zip(QUERIES, QUERY_VECTORS):
        approx_ranking = []
        indices, distances = annoy_index.get_nns_by_vector(query_vector, K, include_distances=True)
        assert len(indices) == len(distances)
        for index, distance in zip(indices, distances):
            product_id = product_ids[index]
            approx_ranking.append((distance, product_id))
        approx_rankings.append(approx_ranking)
    print_rankings(approx_rankings)


# 4.
N_CENTROIDS = int(len(products_us) ** 0.5)


def test_4():
    centroids = products_us.sample(N_CENTROIDS, random_state=0)
    batch_annoy_index_builder = BatchAnnoyIndexBuilder(METRIC, N_TREES)
    for product_id, product_title in zip(centroids["product_id"], centroids["product_title"]):
        batch_annoy_index_builder.add(product_id, product_title)

    global annoy_index
    annoy_index, _ = batch_annoy_index_builder.build()


def answer_5(annoy_index, n_closest):
    annoy_filter = annoy_filter_factory(annoy_index, n_closest)
    ann_inverted_index_builder = ANNInvertedIndexBuilder(annoy_filter)
    for product_id, product_title in zip(products_us["product_id"], products_us["product_title"]):
        ann_inverted_index_builder.add(product_id, product_title)
    return ann_inverted_index_builder.build()


def test_5():
    global inverted_index_title
    inverted_index_title = answer_5(annoy_index, 1)


def answer_6(inverted_index, n_closest):
    start, approx_rankings = time(), []
    for query, query_vector in zip(QUERIES, QUERY_VECTORS):
        iterator = None
        for index in annoy_index.get_nns_by_vector(query_vector, n_closest):
            if iterator is None:
                iterator = inverted_index.iter(index)
            else:
                iterator = boolean_or(iterator, inverted_index.iter(index))
        assert iterator is not None

        ranking_builder = BatchRankingBuilder([query], [K])
        for product_id in iterator:
            product_title = products_us.at[product_id, "product_title"]
            ranking_builder.add(product_id, product_title)
        approx_ranking = ranking_builder.build()[0]
        approx_rankings.append(approx_ranking)
    print("Elapsed Time: {0} (s)".format(time() - start))
    return approx_rankings


def test_6():
    print("6.")
    global approx_rankings
    approx_rankings = answer_6(inverted_index_title, 1)
    print_rankings(approx_rankings)


def answer_7(rankings_i, rankings_j):
    assert len(QUERIES) == len(rankings_i) == len(rankings_j)
    for query, ranking_i, ranking_j in zip(QUERIES, rankings_i, rankings_j):
        print(query)
        print(len(set(ranking_i) & set(ranking_j)) / len(ranking_j))


def test_7():
    print("7.")
    answer_7(exact_rankings, approx_rankings)


def test_8():
    print("8.")
    for n_closest in (5, 25):
        inverted_index_title = answer_5(annoy_index, n_closest)
        approx_rankings = answer_6(inverted_index_title, n_closest)
        answer_7(exact_rankings, approx_rankings)


def test_9():
    field_vectors = use_batch_tokenizer(products_us["product_title"])
    kmeans = KMeans(n_clusters=N_CENTROIDS, random_state=0).fit(field_vectors)
    centroids = kmeans.cluster_centers_

    batch_annoy_index_builder = BatchAnnoyIndexBuilder(METRIC, N_TREES, batch_tokenizer=as_is_batch_tokenizer)
    for index, centroid in enumerate(centroids):
        batch_annoy_index_builder.add(index, centroid)
    annoy_index, _ = batch_annoy_index_builder.build()

    inverted_index_title = answer_5(annoy_index, 5)
    approx_rankings = answer_6(inverted_index_title, 5)
    answer_7(exact_rankings, approx_rankings)
