#!/usr/bin/env python3

from gloves.search_engine import SearchEngine
from requests import get
from requests import post
from threading import Thread
from time import time
from .subjects import products_us

import json


def delete(product_id):
    response = get("http://127.0.0.1:8080/delete", params={"product_id": product_id})
    print(response.text)


def optimize():
    response = get("http://127.0.0.1:8080/optimize")
    print(response.text)


def queries():
    response = get("http://127.0.0.1:8080/queries")
    return json.loads(response.text)["success"]


def select(query, verbose=True):
    response = get("http://127.0.0.1:8080/select", params={"query": query})
    if verbose:
        print(response.text)


def update(json_object, verbose=True):
    response = post("http://127.0.0.1:8080/update", data=json.dumps(json_object))
    if verbose:
        print(response.text)


class TestSearchEngine(object):
    @classmethod
    def setup_class(cls):
        cls.search_engine = SearchEngine.init("127.0.0.1", 8080)
        cls.thread = Thread(target=cls.search_engine.serve_forever)
        cls.thread.start()

    def test_0(self):
        print("0.")
        update(
            [
                {"product_id": "x", "product_title": "a b c"},
                {"product_id": "y", "product_title": "a b"},
                {"product_id": "z", "product_title": "a"},
            ]
        )
        select("b")

    def test_1(self):
        print("1.")
        update(
            [
                {"product_id": "v", "product_title": "c c"},
                {"product_id": "w", "product_title": "c c c"},
            ]
        )
        select("c")

    def test_2(self):
        print("2.")
        delete("v")
        select("c")

    def test_3(self):
        print("3.")
        update(
            [
                {"product_id": "x", "product_title": "a b a b"},
                {"product_id": "y", "product_title": "c c c c"},
            ]
        )
        select("c")

    def test_5(self):
        global products_us
        products_us = products_us.sample(frac=0.1, random_state=0)  # For quick testing
        post_size = len(products_us) // 100

        print("5.")
        for _ in range(2):
            buffer, start = [], time()
            for product_id, product_title in zip(
                products_us["product_id"], products_us["product_title"]
            ):
                buffer.append(
                    {"product_id": product_id, "product_title": product_title}
                )
                if post_size <= len(buffer):
                    update(buffer, verbose=False)
                    buffer = []
            if 0 < len(buffer):
                update(buffer, verbose=False)
            print("Elapsed Time: {0} (s)".format(time() - start))

    def test_6_7(self):
        for attempt in ("6.", "7."):
            print(attempt)
            if "7." == attempt:
                optimize()
            start = time()
            for query in queries():
                select(query, verbose=False)
            print("Elapsed Time: {0} (s)".format(time() - start))

    @classmethod
    def teardown_class(cls):
        cls.search_engine.shutdown()
        cls.search_engine.socket.close()
        cls.thread.join()
