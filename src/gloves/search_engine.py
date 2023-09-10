#!/usr/bin/env python3

from argparse import ArgumentParser
from hashlib import md5
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from gloves.iterator import boolean_or
from gloves.nlp import whitespace_tokenizer
from gloves.priority_queue import PriorityQueue
from requests import get
from requests import post
from socketserver import ThreadingMixIn
from tempfile import TemporaryFile
from urllib.parse import parse_qs
from urllib.parse import urlparse

import fcntl
import json


class Segment(object):
    # 8.4
    @classmethod
    def merge(cls, segments):
        segments.sort(key=lambda segment: -len(segment.live_ids))
        new_segment, old_segment_i, old_segment_j = (
            Segment([]),
            segments.pop(),
            segments.pop(),
        )

        for word in old_segment_i.inverted_index_title.keys():
            if word in old_segment_j.inverted_index_title:
                posting_list = list(
                    boolean_or(
                        old_segment_i.iter(word),
                        old_segment_j.iter(word),
                    )
                )
            else:
                posting_list = list(old_segment_i.iter(word))
            if 0 < len(posting_list):
                new_segment.inverted_index_title[word] = posting_list
        for word in old_segment_j.inverted_index_title.keys() - old_segment_i.inverted_index_title.keys():
            posting_list = list(old_segment_j.iter(word))
            if 0 < len(posting_list):
                new_segment.inverted_index_title[word] = posting_list

        for old_segment in (old_segment_i, old_segment_j):
            for product_id, info in old_segment.info_title.items():
                if product_id in old_segment.live_ids:
                    new_segment.info_title[product_id] = info

        new_segment.live_ids = old_segment_i.live_ids | old_segment_j.live_ids

        segments.append(new_segment)

    def __init__(self, products):
        self.inverted_index_title, self.info_title, self.live_ids = {}, {}, set()
        for product in sorted(products, key=lambda product: product["product_id"]):
            product_id, product_title = product["product_id"], product["product_title"]
            # Cf. 2.0
            counter = {}
            for word in whitespace_tokenizer(product_title):
                if word in counter:
                    counter[word] += 1
                else:
                    counter[word] = 1
            for word, count in counter.items():
                if word in self.inverted_index_title:
                    self.inverted_index_title[word].append((product_id, count))
                else:
                    self.inverted_index_title[word] = [(product_id, count)]
            self.info_title[product_id] = product_title
            self.live_ids.add(product_id)

    def iter(self, word):
        for entry in self.inverted_index_title.get(word, []):
            if entry[0] in self.live_ids:
                yield entry


class SegmentBuilder(object):
    def __init__(self):
        self.products = {}

    def add(self, products):
        for product in products:
            assert "product_id" in product
            self.products[product["product_id"]] = product

    def build(self):
        result = Segment(self.products.values())
        self.products.clear()
        return result


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class SearchEngine(BaseHTTPRequestHandler):
    # 8.8
    class Lock(object):
        def __exit__(self, *_):
            fcntl.flock(SearchEngine.lockfile, fcntl.LOCK_UN)

    class ReadLock(Lock):
        def __enter__(self):
            fcntl.flock(SearchEngine.lockfile, fcntl.LOCK_SH)

    class WriteLock(Lock):
        def __enter__(self):
            fcntl.flock(SearchEngine.lockfile, fcntl.LOCK_EX)

    @classmethod
    def truncate(cls):
        cls.segment_builder = SegmentBuilder()
        cls.segments = []
        cls.live_ids_cache = []

    @classmethod
    def init(cls, host, port):
        cls.lockfile = TemporaryFile()
        with cls.WriteLock():
            cls.truncate()
        return ThreadedHTTPServer((host, port), cls)

    def do_POST(self):
        response, result, contents = (
            200,
            {},
            self.rfile.read(int(self.headers["content-length"])).decode("utf-8"),
        )

        if self.path.startswith("/update"):
            products = json.loads(contents)
            with SearchEngine.WriteLock():
                self.segment_builder.add(products)
            result["success"] = "updated {0} products".format(len(products))

        else:
            response, result["error"] = 404, "unknown POST endpoint"

        self.send(response, result)

    def do_GET(self):
        response, result, parameters = 200, {}, parse_qs(urlparse(self.path).query)

        # 8.9
        if self.path.startswith("/commit"):
            with SearchEngine.WriteLock():
                segments, live_ids_cache = (
                    SearchEngine.segments,
                    SearchEngine.live_ids_cache,
                )
                new_segment = self.segment_builder.build()
                assert len(segments) == len(live_ids_cache)
                for old_segment, live_ids in zip(segments, live_ids_cache):
                    live_ids -= new_segment.live_ids
                    old_segment.live_ids = live_ids.copy()
                segments.append(new_segment)
                live_ids_cache.append(new_segment.live_ids.copy())
                if 10 < len(segments):
                    Segment.merge(segments)
                    SearchEngine.live_ids_cache = [segment.live_ids.copy() for segment in segments]
            result["success"] = "committed {0} products".format(len(new_segment.live_ids))

        elif self.path.startswith("/delete"):
            product_ids = set(parameters["product_id"])
            with SearchEngine.WriteLock():
                for live_ids in SearchEngine.live_ids_cache:
                    live_ids -= product_ids
            result["success"] = "deleted {0} products if exist".format(len(product_ids))

        # Cf. 9.5
        elif self.path.startswith("/fetch"):
            result["success"] = []
            with SearchEngine.ReadLock():
                for product_id in parameters["product_id"]:
                    for segment in SearchEngine.segments:
                        if product_id in segment.live_ids:
                            result["success"].append(segment.info_title[product_id])
                            break

        elif self.path.startswith("/optimize"):
            with SearchEngine.WriteLock():
                segments = SearchEngine.segments
                while 1 < len(segments):
                    Segment.merge(segments)
                SearchEngine.live_ids_cache = [segment.live_ids.copy() for segment in segments]
            result["success"] = "optimized"

        elif self.path.startswith("/queries"):
            queries = set()
            with SearchEngine.ReadLock():
                for segment in SearchEngine.segments:
                    queries |= segment.inverted_index_title.keys()
            result["success"] = []
            for query in sorted(queries):
                query_hash = int(md5(query.encode("utf-8")).hexdigest(), 16)
                if 0 == query_hash % 100:
                    result["success"].append(query)

        # Cf. 9.8
        elif self.path.startswith("/replicate"):
            assert 1 == len(parameters["to"])
            to = parameters["to"][0]
            with SearchEngine.ReadLock():
                result["success"] = []
                for segment in SearchEngine.segments:
                    contents = []
                    for product_id in segment.live_ids:
                        contents.append(
                            {
                                "product_id": product_id,
                                "product_title": segment.info_title[product_id],
                            }
                        )
                    result["success"].append(post(to + "update", data=json.dumps(contents)).text)
                    result["success"].append(get(to + "commit").text)

        elif self.path.startswith("/select"):
            with SearchEngine.ReadLock():
                segments, priority_queue, ranking = (
                    SearchEngine.segments,
                    PriorityQueue(10),
                    [],
                )
                assert 1 == len(parameters["query"])
                for segment_index, segment in enumerate(segments):
                    for product_id, tf in segment.iter(parameters["query"][0]):
                        priority_queue.push((tf, product_id, segment_index))
                while 0 < len(priority_queue.body):
                    priority, product_id, segment_index = priority_queue.pop()
                    ranking.append(
                        {
                            "_priority": priority,
                            "product_id": product_id,
                        }
                    )
                    # Cf. 9.5
                    if "omit_detail" not in parameters:
                        ranking[-1]["product_title"] = segments[segment_index].info_title[product_id]
                result["success"] = ranking

        # Cf. 9.9
        elif self.path.startswith("/split"):
            assert (
                1 == len(parameters["to"]) and 1 == len(parameters["denominator"]) and 1 == len(parameters["surplus"])
            )
            to, denominator, surplus = (
                parameters["to"][0],
                int(parameters["denominator"][0]),
                int(parameters["surplus"][0]),
            )
            with SearchEngine.WriteLock():
                result["success"] = []
                assert len(SearchEngine.segments) == len(SearchEngine.live_ids_cache)
                for segment, live_ids in zip(SearchEngine.segments, SearchEngine.live_ids_cache):
                    contents, to_delete = [], set()
                    for product_id in segment.live_ids:
                        product_hash = int(md5(product_id.encode("utf-8")).hexdigest(), 16)
                        if product_hash % denominator == surplus:
                            contents.append(
                                {
                                    "product_id": product_id,
                                    "product_title": segment.info_title[product_id],
                                }
                            )
                            to_delete.add(product_id)
                    result["success"].append(post(to + "update", data=json.dumps(contents)).text)
                    result["success"].append(get(to + "commit").text)
                    live_ids -= to_delete

        elif self.path.startswith("/truncate"):
            with SearchEngine.WriteLock():
                SearchEngine.truncate()
            result["success"] = "truncated"

        else:
            response, result["error"] = 404, "unknown GET endpoint"

        self.send(response, result)

    def send(self, response, result):
        self.send_response(response)
        self.send_header("Content-Type", "text/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=4).encode("utf-8"))


if __name__ == "__main__":
    argument_parser = ArgumentParser(description="runs a search engine")
    argument_parser.add_argument("--host", default="127.0.0.1", help="host name", metavar="str", type=str)
    argument_parser.add_argument("--port", default=8080, help="port number", metavar="int", type=int)
    arg_dict = argument_parser.parse_args()
    SearchEngine.init(arg_dict.host, arg_dict.port).serve_forever()
