#!/usr/bin/env python3

from gloves.user_interface import UserInterface
from requests import get
from sklearn.metrics import cohen_kappa_score
from threading import Thread
from .subjects import merged_us
from .subjects import products_us


def annotate(query_id):
    response = get("http://127.0.0.1:8080/annotate", params={"query_id": str(query_id)})
    print(response.text)


def select(query, sort=None):
    if sort is None:
        response = get("http://127.0.0.1:8080/select", params={"query": query})
    else:
        response = get(
            "http://127.0.0.1:8080/select", params={"query": query, "sort": sort}
        )
    print(response.text)


class TestUserInterface(object):
    @classmethod
    def setup_class(cls):
        inverted_index = {}  # Cf. 2.0
        for product_id, product_title in zip(
            products_us["product_id"], products_us["product_title"]
        ):
            counter = {}
            for word in product_title.split():
                if word in counter:
                    counter[word] += 1
                else:
                    counter[word] = 1
            for word, count in counter.items():
                if word in inverted_index:
                    inverted_index[word].append((product_id, count))
                else:
                    inverted_index[word] = [(product_id, count)]

        cls.http_server = UserInterface.init("127.0.0.1", 8080)
        UserInterface.inverted_index = inverted_index
        UserInterface.indexed_products_us = products_us.set_index("product_id")
        UserInterface.merged_us = merged_us
        cls.thread = Thread(target=cls.http_server.serve_forever)
        cls.thread.start()

    def test_0(self):
        print("0.")
        select("Information")
        select("Science")

    def test_1(self):
        print("1.")
        select("Information Science")  # Cf. 1.5
        select("Amazon HDMI Cable")

    def test_3(self):
        print("3.")
        select("Information", sort="tf")
        select("Amazon HDMI Cable", sort="tf")

    def test_5(self):
        print("5.")
        annotate(2155)  # 15 ft hdmi cable
        annotate(18440)  # books on science for kids

        global my_annotations
        my_annotations = {
            2155: [
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "S",
                "E",
                "E",
                "E",
                "C",
            ],
            18440: [
                "I",
                "E",
                "I",
                "S",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "E",
                "I",
                "C",
                "C",
                "C",
                "I",
            ],
        }

    def test_6(self):
        print("6.")
        for query_id, my_annotation in my_annotations.items():
            their_annotation = merged_us[query_id == merged_us.query_id]["esci_label"]
            print(f"{query_id}: {cohen_kappa_score(my_annotation, their_annotation)}")

    def test_7(self):
        print("7.")
        select("Information OR Retrieval")  # Cf. 1.6

    @classmethod
    def teardown_class(cls):
        cls.http_server.shutdown()
        cls.http_server.socket.close()
        cls.thread.join()
