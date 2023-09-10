from gloves.iterator import extended_boolean_or
from gloves.nlp import whitespace_tokenizer
from gloves.priority_queue import PriorityQueue
from gloves.scoring import bm25_weight
from gloves.scoring import bm25f_weight
from gloves.scoring import idf
from .subjects import products_us


def test_0():
    global inverted_index_title
    inverted_index_title = {}
    for product_id, product_title in zip(products_us["product_id"], products_us["product_title"]):
        counter = {}
        for word in whitespace_tokenizer(product_title):
            if word in counter:
                counter[word] += 1
            else:
                counter[word] = 1
        for word, count in counter.items():
            if word in inverted_index_title:
                inverted_index_title[word].append((product_id, count))
            else:
                inverted_index_title[word] = [(product_id, count)]


def test_1():
    global priority_queue
    priority_queue = PriorityQueue(10)


def test_3():
    global posting_list_hdmi, posting_list_cable
    global indexed_products_us
    posting_list_hdmi, posting_list_cable = (
        inverted_index_title["HDMI"],
        inverted_index_title["Cable"],
    )
    for product_id, tf_hdmi, tf_cable in extended_boolean_or(iter(posting_list_hdmi), iter(posting_list_cable)):
        priority_queue.push((tf_hdmi + tf_cable, product_id))
    indexed_products_us = products_us.set_index("product_id")
    print("3.")
    while 0 < len(priority_queue.body):
        priority, product_id = priority_queue.pop()
        print(priority, product_id, indexed_products_us.at[product_id, "product_title"])


def test_4():
    global N, df_hdmi, df_cable
    N, df_hdmi, df_cable = (
        len(products_us),
        len(posting_list_hdmi),
        len(posting_list_cable),
    )
    for product_id, tf_hdmi, tf_cable in extended_boolean_or(iter(posting_list_hdmi), iter(posting_list_cable)):
        priority_queue.push((tf_hdmi * idf(N, df_hdmi) + tf_cable * idf(N, df_cable), product_id))
    print("4.")
    while 0 < len(priority_queue.body):
        priority, product_id = priority_queue.pop()
        print(priority, product_id, indexed_products_us.at[product_id, "product_title"])


def test_5():
    global info_title, avg_length_title
    info_title, sum_length_title = {}, 0
    for product_id, product_title in zip(products_us["product_id"], products_us["product_title"]):
        length_title = len(list(whitespace_tokenizer(product_title)))
        info_title[product_id] = {"length": length_title}
        sum_length_title += length_title
    avg_length_title = sum_length_title / N


def test_6():
    global K1, B
    K1, B = 1.2, 0.75
    for product_id, tf_hdmi, tf_cable in extended_boolean_or(iter(posting_list_hdmi), iter(posting_list_cable)):
        length_title = info_title[product_id]["length"]
        bm25 = 0
        bm25 += bm25_weight(tf_hdmi, K1, B, length_title, avg_length_title) * idf(N, df_hdmi)
        bm25 += bm25_weight(tf_cable, K1, B, length_title, avg_length_title) * idf(N, df_cable)
        priority_queue.push((bm25, product_id))
    print("6.")
    while 0 < len(priority_queue.body):
        priority, product_id = priority_queue.pop()
        print(priority, product_id, indexed_products_us.at[product_id, "product_title"])


def answer7():
    for product_id, tf_hdmi, tf_cable in extended_boolean_or(iter(posting_list_hdmi), iter(posting_list_cable)):
        boost_title, length_title = 2.0, info_title[product_id]["length"]
        weight_hdmi = bm25f_weight(tf_hdmi, boost_title, B, length_title, avg_length_title)
        weight_cable = bm25f_weight(tf_cable, boost_title, B, length_title, avg_length_title)
        tf_basics = "Amazon Basics" == indexed_products_us.at[product_id, "product_brand"]
        boost_brand, length_brand, avg_length_brand = 1.0, 1, 1
        weight_basics = bm25f_weight(tf_basics, boost_brand, B, length_brand, avg_length_brand)
        bm25f = 0
        bm25f += weight_hdmi / (K1 + weight_hdmi) * idf(N, df_hdmi)
        bm25f += weight_cable / (K1 + weight_cable) * idf(N, df_cable)
        bm25f += weight_basics / (K1 + weight_basics) * idf(N, df_basics)
        priority_queue.push((bm25f, product_id))
    while 0 < len(priority_queue.body):
        priority, product_id = priority_queue.pop()
        print(priority, product_id, indexed_products_us.at[product_id, "product_title"])


def test_7():
    global df_basics
    df_basics = len(products_us["Amazon Basics" == products_us.product_brand])
    print("7.")
    answer7()


def test_8():
    global K1
    K1 = 3.5
    print("8.")
    answer7()
