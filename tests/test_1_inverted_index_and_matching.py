from gloves.inverted_index import SimpleInvertedIndexBuilder
from gloves.iterator import boolean_and
from gloves.iterator import boolean_and_not
from gloves.iterator import boolean_or
from gloves.nlp import as_is_tokenizer
from gloves.nlp import whitespace_tokenizer
from .subjects import products_us


def test_01():
    global dictionary
    dictionary = {}
    for product_title in products_us["product_title"]:
        for word in whitespace_tokenizer(product_title):
            if word in dictionary:
                dictionary[word] += 1
            else:
                dictionary[word] = 1
    assert 912923 == len(dictionary)


def test_02():
    global posting_list
    posting_list = []
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        if "Information" in whitespace_tokenizer(product_title):
            posting_list.append(product_id)
    print(posting_list)
    assert 110 == len(posting_list)


def test_03():
    global inverted_index_title
    builder = SimpleInvertedIndexBuilder(whitespace_tokenizer)
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        builder.add(product_id, product_title)
    inverted_index_title = builder.build()
    assert len(dictionary) == len(inverted_index_title)
    assert posting_list == inverted_index_title["Information"]


def test_04():
    from pickle import dump
    from pickle import load
    from tempfile import NamedTemporaryFile

    global inverted_index_title
    with NamedTemporaryFile() as ntf:
        with open(ntf.name, "wb") as f:
            dump(inverted_index_title, f)
        with open(ntf.name, "rb") as f:
            inverted_index_title = load(f)


def answer_05(inverted_index, verbose=False):
    result5 = list(
        boolean_and(
            inverted_index.iter("Information"),
            inverted_index.iter("Science"),
        )
    )
    if verbose:
        print(result5)
    assert 3 == len(result5)


def test_05():
    answer_05(inverted_index_title, True)


def answer_06(inverted_index, verbose=False):
    result6 = list(
        boolean_or(
            inverted_index.iter("Information"),
            inverted_index.iter("Retrieval"),
        )
    )
    if verbose:
        print(result6)
    assert 129 == len(result6)


def test_06():
    answer_06(inverted_index_title, True)


def answer_07(inverted_index, verbose=False):
    result7 = list(
        boolean_and_not(
            boolean_or(
                inverted_index.iter("Information"),
                inverted_index.iter("Retrieval"),
            ),
            boolean_and(
                inverted_index.iter("Information"),
                inverted_index.iter("Science"),
            ),
        )
    )
    if verbose:
        print(result7)
    assert 126 == len(result7)


def test_07():
    answer_07(inverted_index_title, True)


def test_08():
    global inverted_index_brand
    builder = SimpleInvertedIndexBuilder(as_is_tokenizer)
    for product_id, product_brand in zip(
        products_us["product_id"], products_us["product_brand"]
    ):
        if product_brand is not None:
            builder.add(product_id, product_brand)
    inverted_index_brand = builder.build()


def test_09():
    result9 = list(
        boolean_and_not(
            inverted_index_title.iter("Amazon"),
            inverted_index_brand.iter("Amazon Basics"),
        )
    )
    assert 8681 == len(result9)


def test_10():
    from gloves.inverted_index import PrefixInvertedIndexBuilder

    builder = PrefixInvertedIndexBuilder(whitespace_tokenizer)
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        builder.add(product_id, product_title)
    inverted_index_title = builder.build()
    answer_05(inverted_index_title)
    answer_06(inverted_index_title)
    answer_07(inverted_index_title)


def test_11():
    from gloves.inverted_index import EncodeInvertedIndexBuilder

    builder = EncodeInvertedIndexBuilder(whitespace_tokenizer)
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        builder.add(product_id, product_title)
    inverted_index_title = builder.build()
    answer_05(inverted_index_title)
    answer_06(inverted_index_title)
    answer_07(inverted_index_title)


def test_12():
    from gloves.inverted_index import VariableByteInvertedIndexBuilder

    builder = VariableByteInvertedIndexBuilder(whitespace_tokenizer)
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        builder.add(product_id, product_title)
    inverted_index_title = builder.build()
    answer_05(inverted_index_title)
    answer_06(inverted_index_title)
    answer_07(inverted_index_title)
