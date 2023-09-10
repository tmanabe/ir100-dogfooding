#!/usr/bin/env python3

from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from gloves.priority_queue import PriorityQueue
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from urllib.parse import urlparse

import json


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class UserInterface(BaseHTTPRequestHandler):
    @classmethod
    def init(cls, host, port):
        cls.query_parser = None
        cls.inverted_index = {}
        cls.indexed_products_us = None
        cls.merged_us = None
        return ThreadedHTTPServer((host, port), cls)

    def do_GET(self):
        response, result, parameters = 200, {}, parse_qs(urlparse(self.path).query)

        if self.path.startswith("/annotate"):  # 4.4
            assert 1 == len(parameters["query_id"])
            query_id = int(parameters["query_id"][0])
            products = []
            filtered_merged_us = self.merged_us[query_id == self.merged_us.query_id]
            for query, product_id, product_title in zip(
                filtered_merged_us["query"],
                filtered_merged_us["product_id"],
                filtered_merged_us["product_title"],
            ):
                products.append(
                    {
                        "query": query,
                        "product_id": product_id,
                        "product_title": product_title,
                    }
                )
            result["success"] = {
                "product_count": len(products),
                "products": products,
            }

        elif self.path.startswith("/select"):
            assert 1 == len(parameters["query"])
            query = self.query_parser.parse(parameters["query"][0])
            product_count, ranking = 0, []
            if "sort" in parameters:  # 4.2
                assert 1 == len(parameters["sort"])
                assert "tf" == parameters["sort"][0]
                priority_queue = PriorityQueue(10)  # Cf. 2.3
                for product_id, expansions in query.iterator(self.inverted_index):
                    product_count += 1
                    priority = 0
                    for expansion in expansions:
                        if expansion is not None:
                            priority += len(expansion.positions)  # == TF
                    priority_queue.push((priority, product_id))
                while 0 < len(priority_queue.body):
                    _, product_id = priority_queue.pop()
                    ranking.append(product_id)
                ranking.reverse()
            else:
                for product_id, _ in query.iterator(self.inverted_index):
                    product_count += 1
                    if len(ranking) < 10:
                        ranking.append(product_id)
            products = []
            for product_id in ranking:
                products.append(
                    {
                        "product_id": product_id,
                        "product_title": self.indexed_products_us.at[product_id, "product_title"],
                    }
                )
            result["success"] = {
                "product_count": product_count,
                "products": products,
            }

        else:
            response, result["error"] = 404, "unknown GET endpoint"

        self.send(response, result)

    def send(self, response, result):
        self.send_response(response)
        self.send_header("Content-Type", "text/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=4).encode("utf-8"))


if __name__ == "__main__":
    argument_parser = ArgumentParser(description="runs a web UI")
    argument_parser.add_argument("--host", default="127.0.0.1", help="host name", metavar="str", type=str)
    argument_parser.add_argument("--port", default=8080, help="port number", metavar="int", type=int)
    arg_dict = argument_parser.parse_args()
    UserInterface.init(arg_dict.host, arg_dict.port).serve_forever()
