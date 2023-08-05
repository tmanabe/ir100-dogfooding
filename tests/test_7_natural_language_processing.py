#!/usr/bin/env python3

from gloves.nlp import english_lowercase_filter
from gloves.nlp import english_possessive_filter
from gloves.nlp import porter_stem_filter
from gloves.nlp import unicode_punctuation_tokenizer
from gloves.nlp import unicode_text_segmentation_tokenizer
from gloves.nlp import whitespace_tokenizer
from time import time
from .subjects import products_us


def test_1():
    print("1.")
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in english_possessive_filter(whitespace_tokenizer(product_description)):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))


def test_2():
    print("2.")
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in english_lowercase_filter(whitespace_tokenizer(product_description)):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))


def test_3():
    print("3.")
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in porter_stem_filter(whitespace_tokenizer(product_description)):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))


def test_4():
    print("4.")
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in unicode_punctuation_tokenizer(product_description):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))


def test_5():
    print("5.")
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in unicode_text_segmentation_tokenizer(product_description):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))  # Possibly slow (~10 minutes)
