#!/usr/bin/env python3

from gloves.inverted_index import ExpandedVariableByteInvertedIndexBuilder
from gloves.nlp import whitespace_tokenizer
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
        builder = ExpandedVariableByteInvertedIndexBuilder(whitespace_tokenizer)
        for product_id, product_title in zip(
            products_us["product_id"], products_us["product_title"]
        ):
            builder.add(product_id, product_title)
        inverted_index = builder.build()

        cls.http_server = UserInterface.init("127.0.0.1", 8080)
        UserInterface.inverted_index = inverted_index
        UserInterface.indexed_products_us = products_us.set_index("product_id")
        UserInterface.merged_us = merged_us
        cls.thread = Thread(target=cls.http_server.serve_forever)
        cls.thread.start()

    def test_00(self):
        print("0.")
        select("Information")
        select("Science")

    def test_01(self):
        print("1.")
        select("Information Science")  # Cf. 1.5
        select("Amazon HDMI Cable")

    def test_03(self):
        print("3.")
        select("Information", sort="tf")
        select("Amazon HDMI Cable", sort="tf")

    def test_05(self):
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

    def test_06(self):
        print("6.")
        for query_id, my_annotation in my_annotations.items():
            their_annotation = merged_us[query_id == merged_us.query_id]["esci_label"]
            print(f"{query_id}: {cohen_kappa_score(my_annotation, their_annotation)}")

    def test_07(self):
        print("7.")
        select("Information OR Retrieval", sort="tf")  # Cf. 1.6

    def test_09(self):  # Cf. 4.1
        print("9.")
        select('" Information Science "')
        select('Amazon " HDMI Cable "')

    @classmethod
    def teardown_class(cls):
        cls.http_server.shutdown()
        cls.http_server.socket.close()
        cls.thread.join()
