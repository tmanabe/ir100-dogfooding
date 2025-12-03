#!/usr/bin/env python3

from MeCab import Tagger
from gloves.nlp import english_lowercase_filter
from gloves.nlp import english_possessive_filter
from gloves.nlp import katakana_stem_filter
from gloves.nlp import mecab_analyzer
from gloves.nlp import mecab_tokenizer
from gloves.nlp import porter_stem_filter
from gloves.nlp import pos_filter
from gloves.nlp import unicode_punctuation_tokenizer
from gloves.nlp import whitespace_tokenizer
from time import time
from transformers import AutoTokenizer
from .subjects import products_jp
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
    bert_tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    start = time()
    for product_description in products_us["product_description"]:
        if product_description is None:
            continue
        for _ in bert_tokenizer.tokenize(product_description):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))  # Possibly slow (~3 minutes)


def test_6():
    print("6.")
    start = time()
    for product_description in products_jp["product_description"]:
        if product_description is None:
            continue
        for _ in mecab_tokenizer(product_description):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))

    tagger = Tagger()
    print(tagger.parse("情報検索100本ノック"))


def test_7():
    print("7.")
    start = time()
    for product_description in products_jp["product_description"]:
        if product_description is None:
            continue
        for _ in pos_filter(mecab_analyzer(product_description)):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))


def test_8():
    print("8.")
    start = time()
    for product_description in products_jp["product_description"]:
        if product_description is None:
            continue
        for _ in katakana_stem_filter(mecab_tokenizer(product_description)):
            pass
    print("Elapsed Time: {0} (s)".format(time() - start))
