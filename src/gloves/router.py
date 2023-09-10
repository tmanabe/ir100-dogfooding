#!/usr/bin/env python3

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from hashlib import md5
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from gloves.priority_queue import PriorityQueue
from requests import get
from requests import post
from socketserver import ThreadingMixIn
from threading import current_thread
from urllib.parse import parse_qs
from urllib.parse import urlparse

import json


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class Router(BaseHTTPRequestHandler):
    @classmethod
    def reset_port_matrix(cls):
        port, cls.port_matrix = cls.port, []
        for _ in range(cls.shards):
            ports = []
            for _ in range(cls.replicas):
                port += 1
                ports.append(port)
            cls.port_matrix.append(ports)

    @classmethod
    def init(cls, host, port, replicas, shards):
        cls.host = host
        cls.port = port
        cls.replicas = replicas
        cls.shards = shards
        cls.reset_port_matrix()
        cls.tpe_for_select = ThreadPoolExecutor(replicas)
        return ThreadedHTTPServer((host, port), cls)

    def do_POST(self):
        response, result, body = (
            200,
            {},
            self.rfile.read(int(self.headers["content-length"])).decode("utf-8"),
        )

        # 9.1, 9.6
        if self.path.startswith("/update"):
            sharded_contents_list = []
            for _ in range(Router.shards):
                sharded_contents_list.append([])
            for product in json.loads(body):
                product_hash = int(
                    md5(product["product_id"].encode("utf-8")).hexdigest(), 16
                )
                sharded_contents_list[product_hash % Router.shards].append(product)

            with ThreadPoolExecutor(
                max_workers=Router.shards * Router.replicas
            ) as tpe_for_update:

                def fn(url, contents):
                    return {url: json.loads(post(url, data=json.dumps(contents)).text)}

                fs = []
                assert len(Router.port_matrix) == len(sharded_contents_list)
                for ports, sharded_contents in zip(
                    Router.port_matrix, sharded_contents_list
                ):
                    for port in ports:
                        url = "http://{0}:{1}/update".format(Router.host, port)
                        fs.append(tpe_for_update.submit(fn, url, sharded_contents))
                result["success"] = {}
                for f in as_completed(fs):
                    result["success"].update(f.result())

        else:
            response, result["error"] = 404, "unknown POST endpoint"

        self.send(response, result)

    def do_GET(self):
        response, result, parameters = 200, {}, parse_qs(urlparse(self.path).query)

        if self.path.startswith("/commit"):
            with ThreadPoolExecutor(
                max_workers=Router.shards * Router.replicas
            ) as tpe_for_update:

                def fn(url):
                    return {url: json.loads(get(url).text)}

                fs = []
                for ports in Router.port_matrix:
                    for port in ports:
                        url = "http://{0}:{1}/commit".format(Router.host, port)
                        fs.append(tpe_for_update.submit(fn, url))
                result["success"] = {}
                for f in as_completed(fs):
                    result["success"].update(f.result())

        elif self.path.startswith("/queries"):
            queries = set()
            for ports in Router.port_matrix:
                url = "http://{0}:{1}/queries".format(Router.host, ports[0])
                queries |= set(json.loads(get(url).text)["success"])
            result["success"] = sorted(queries)

        # 9.8
        elif self.path.startswith("/replicate"):
            port_to = Router.port + Router.shards * Router.replicas
            result["success"] = []
            for ports in Router.port_matrix:
                port_from, port_to = ports[0], port_to + 1
                url_from = "http://{0}:{1}/".format(Router.host, port_from)
                url_to = "http://{0}:{1}/".format(Router.host, port_to)
                text = get(url_from + "replicate", params={"to": url_to}).text
                result["success"].append(json.loads(text)["success"])
                ports.append(port_to)
            Router.replicas += 1

        # 9.3, 9.7
        elif self.path.startswith("/select"):

            def fn(query):
                partial_results, replica_index = [], int(
                    current_thread().name.rsplit("_", 1)[-1]
                )
                with ThreadPoolExecutor(max_workers=Router.shards) as tpe_for_shards:

                    def fn(query, shard_index, replica_index):
                        port = Router.port_matrix[shard_index][replica_index]
                        url = "http://{0}:{1}/select".format(Router.host, port)
                        return json.loads(get(url, params={"query": query}).text)[
                            "success"
                        ]

                    fs = []
                    for shard_index in range(Router.shards):
                        fs.append(
                            tpe_for_shards.submit(fn, query, shard_index, replica_index)
                        )
                    for f in as_completed(fs):
                        partial_results.append(f.result())
                return partial_results

            assert 1 == len(parameters["query"])
            priority_queue, query = PriorityQueue(10), parameters["query"][0]
            for partial_result in Router.tpe_for_select.submit(fn, query).result():
                for product in partial_result:
                    priority_queue.push(
                        (product["_priority"], product["product_id"], product)
                    )
            result["success"] = []
            while 0 < len(priority_queue.body):
                _, _, product = priority_queue.pop()
                result["success"].append(product)

        # 9.8
        elif self.path.startswith("/split"):
            # md5 % 2 in {0, 1} -> md5 % 4 in {0, 1, 2, 3}
            denominator_from, denominator_to = Router.shards, 2 * Router.shards
            port_to = Router.port + Router.shards * Router.replicas
            result["success"] = []
            for surplus_from, ports_from in enumerate(Router.port_matrix.copy()):
                surplus_to = denominator_from + surplus_from
                results, ports_to = [], []
                for port_from in ports_from:
                    port_to += 1
                    url_from = "http://{0}:{1}/".format(Router.host, port_from)
                    url_to = "http://{0}:{1}/".format(Router.host, port_to)
                    text = get(
                        url_from + "split",
                        params={
                            "to": url_to,
                            "denominator": str(denominator_to),
                            "surplus": str(surplus_to),
                        },
                    ).text
                    results.append(json.loads(text)["success"])
                    ports_to.append(port_to)
                Router.port_matrix.append(ports_to)
            Router.shards *= 2

        elif self.path.startswith("/truncate"):
            port, result["success"] = Router.port, {}
            for ports in Router.port_matrix:
                for port in ports:
                    url = "http://{0}:{1}/truncate".format(Router.host, port)
                    result["success"][url] = json.loads(get(url).text)
            if "new_replicas" in parameters:
                assert 1 == len(parameters["new_replicas"])
                new_replicas = int(parameters["new_replicas"][0])
                assert 0 < new_replicas
                Router.replicas = new_replicas
                Router.tpe_for_select = ThreadPoolExecutor(new_replicas)
            if "new_shards" in parameters:
                assert 1 == len(parameters["new_shards"])
                new_shards = int(parameters["new_shards"][0])
                assert 0 < new_shards
                Router.shards = new_shards
            Router.reset_port_matrix()

        # 9.5
        elif self.path.startswith("/two_stage_select"):

            def fn_select(query):
                partial_results, replica_index = {}, int(
                    current_thread().name.rsplit("_", 1)[-1]
                )
                with ThreadPoolExecutor(max_workers=Router.shards) as tpe_for_shards:

                    def fn(query, shard_index, replica_index):
                        port = Router.port_matrix[shard_index][replica_index]
                        url = "http://{0}:{1}/select".format(Router.host, port)
                        params = {"omit_detail": "y", "query": query}
                        return {
                            shard_index: json.loads(get(url, params).text)["success"]
                        }

                    fs = []
                    for shard_index in range(Router.shards):
                        fs.append(
                            tpe_for_shards.submit(fn, query, shard_index, replica_index)
                        )
                    for f in as_completed(fs):
                        partial_results.update(f.result())
                return partial_results

            def fn_fetch(shard_index_to_product_ids):
                result, replica_index = {}, int(
                    current_thread().name.rsplit("_", 1)[-1]
                )
                with ThreadPoolExecutor(max_workers=Router.shards) as tpe_for_shards:

                    def fn(shard_index, product_ids):
                        port = Router.port_matrix[shard_index][replica_index]
                        url = "http://{0}:{1}/fetch".format(Router.host, port)
                        product_titles = json.loads(
                            get(url, params={"product_id": product_ids}).text
                        )["success"]
                        return dict(zip(product_ids, product_titles))

                    fs = []
                    for shard_index, product_ids in shard_index_to_product_ids.items():
                        fs.append(tpe_for_shards.submit(fn, shard_index, product_ids))
                    for f in as_completed(fs):
                        result.update(f.result())
                return result

            assert 1 == len(parameters["query"])
            priority_queue, query = PriorityQueue(10), parameters["query"][0]
            for surplus_from, partial_result in (
                Router.tpe_for_select.submit(fn_select, query).result().items()
            ):
                for product in partial_result:
                    assert "product_title" not in product
                    priority_queue.push(
                        (
                            product["_priority"],
                            product["product_id"],
                            product,
                            surplus_from,
                        )
                    )
            ranking, shard_index_to_product_ids = [], {}
            while 0 < len(priority_queue.body):
                _, product_id, product, surplus_from = priority_queue.pop()
                ranking.append(product)
                if surplus_from in shard_index_to_product_ids:
                    shard_index_to_product_ids[surplus_from].append(product_id)
                else:
                    shard_index_to_product_ids[surplus_from] = [product_id]
            product_id_to_title = Router.tpe_for_select.submit(
                fn_fetch, shard_index_to_product_ids
            ).result()
            for product in ranking:
                product["product_title"] = product_id_to_title[product["product_id"]]
            result["success"] = ranking

        else:
            response, result["error"] = 404, "unknown GET endpoint"

        self.send(response, result)

    def send(self, response, result):
        self.send_response(response)
        self.send_header("Content-Type", "text/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=4).encode("utf-8"))


if __name__ == "__main__":
    argument_parser = ArgumentParser(description="runs a router")
    argument_parser.add_argument(
        "--host", default="127.0.0.1", help="host name", metavar="str", type=str
    )
    argument_parser.add_argument(
        "--port", default=8080, help="port number", metavar="int", type=int
    )
    argument_parser.add_argument(
        "--replicas", default=1, help="number of replicas", metavar="int", type=int
    )
    argument_parser.add_argument(
        "--shards", default=2, help="number of shards", metavar="int", type=int
    )
    arg_dict = argument_parser.parse_args()
    Router.init(
        arg_dict.host, arg_dict.port, arg_dict.replicas, arg_dict.shards
    ).serve_forever()
