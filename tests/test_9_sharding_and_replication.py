#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from gloves.search_engine import SearchEngine
from gloves.router import Router
from requests import get
from requests import post
from threading import Thread
from time import time
from .subjects import products_us

import json


def queries():
    response = get("http://127.0.0.1:8080/queries")
    return json.loads(response.text)["success"]


def truncate(params={}):
    get("http://127.0.0.1:8080/truncate", params)


def update(json_object):
    post("http://127.0.0.1:8080/update", json.dumps(json_object))


class TestRouter(object):
    def setup_class(cls):
        cls.search_engines = [
            SearchEngine.init("127.0.0.1", port) for port in range(8081, 8085)
        ]
        cls.threads = [
            Thread(target=search_engine.serve_forever)
            for search_engine in cls.search_engines
        ]
        for thread in cls.threads:
            thread.start()
        cls.router = Router.init("127.0.0.1", 8080, 1, 2)
        cls.thread = Thread(target=cls.router.serve_forever)
        cls.thread.start()

    def answer8_5(self):
        for _ in range(2):
            buffer, start = [], time()
            for i, (product_id, product_title) in enumerate(
                zip(products_us["product_id"], products_us["product_title"])
            ):
                buffer.append(
                    {"product_id": product_id, "product_title": product_title}
                )
                if post_size <= len(buffer):
                    update(buffer)
                    buffer = []
            if 0 < len(buffer):
                update(buffer)
            print("Elapsed Time: {0} (s)".format(time() - start))

    def test_2(self):
        global products_us
        global post_size
        products_us = products_us.sample(frac=0.1, random_state=0)  # For quick testing
        post_size = len(products_us) // 100

        print("2.")
        truncate({"new_replicas": "1", "new_shards": "2"})
        self.answer8_5()

    def answer8_6(self, max_workers):
        def fn(query):
            get("http://127.0.0.1:8080/select", params={"query": query})

        start = time()
        with ThreadPoolExecutor(max_workers) as tpe:
            for query in queries():
                tpe.submit(fn, query)
        print("Elapsed Time: {0} (s)".format(time() - start))

    def test_4(self):
        print("4.")
        self.answer8_6(1)

    def test_5(self):
        print("5.")
        start = time()
        for query in queries():
            get("http://127.0.0.1:8080/two_stage_select", params={"query": query})
        print("Elapsed Time: {0} (s)".format(time() - start))

    def test_6(self):
        print("6.")
        truncate({"new_replicas": "2", "new_shards": "2"})
        self.answer8_5()

    def test_7(self):
        print("7")
        self.answer8_6(2)

    @classmethod
    def teardown_class(cls):
        cls.router.shutdown()
        cls.router.socket.close()
        cls.thread.join()
        for search_engine in cls.search_engines:
            search_engine.shutdown()
            search_engine.socket.close()
        for thread in cls.threads:
            thread.join()
