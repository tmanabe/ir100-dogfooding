from gloves.nlp import whitespace_tokenizer
from .subjects import products_us


def test_1_1():
    global dictionary
    dictionary = {}
    for product_title in products_us["product_title"]:
        for word in whitespace_tokenizer(product_title):
            if word in dictionary:
                dictionary[word] += 1
            else:
                dictionary[word] = 1
    assert 912923 == len(dictionary)


def test_1_2():
    global posting_list
    posting_list = []
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        if "Information" in whitespace_tokenizer(product_title):
            posting_list.append(product_id)
    print(posting_list)
    assert 110 == len(posting_list)


def test_1_3():
    global inverted_index_title
    inverted_index_title = {}
    for product_id, product_title in zip(
        products_us["product_id"], products_us["product_title"]
    ):
        for word in set(whitespace_tokenizer(product_title)):
            if word in inverted_index_title:
                inverted_index_title[word].append(product_id)
            else:
                inverted_index_title[word] = [product_id]
    assert len(dictionary) == len(inverted_index_title)
    assert posting_list == inverted_index_title["Information"]


def test_1_4():
    from pickle import dump
    from pickle import load
    from tempfile import NamedTemporaryFile

    global inverted_index_title
    with NamedTemporaryFile() as ntf:
        with open(ntf.name, "wb") as f:
            dump(inverted_index_title, f)
        with open(ntf.name, "rb") as f:
            inverted_index_title = load(f)


def test_1_5():
    from gloves.iterator import boolean_and

    global inverted_index_title
    result5 = list(
        boolean_and(
            iter(inverted_index_title["Information"]),
            iter(inverted_index_title["Science"]),
        )
    )
    print(result5)
    assert 3 == len(result5)


def test_1_6():
    from gloves.iterator import boolean_or

    global inverted_index_title
    result6 = list(
        boolean_or(
            iter(inverted_index_title["Information"]),
            iter(inverted_index_title["Retrieval"]),
        )
    )
    print(result6)
    assert 129 == len(result6)


def test_1_7():
    from gloves.iterator import boolean_and
    from gloves.iterator import boolean_and_not
    from gloves.iterator import boolean_or

    global inverted_index_title
    result7 = list(
        boolean_and_not(
            boolean_or(
                iter(inverted_index_title["Information"]),
                iter(inverted_index_title["Retrieval"]),
            ),
            boolean_and(
                iter(inverted_index_title["Information"]),
                iter(inverted_index_title["Science"]),
            ),
        )
    )
    print(result7)
    assert 126 == len(result7)


def test_1_8():
    global inverted_index_brand
    inverted_index_brand = {}
    for product_id, product_brand in zip(
        products_us["product_id"], products_us["product_brand"]
    ):
        if product_brand in inverted_index_brand:
            inverted_index_brand[product_brand].append(product_id)
        else:
            inverted_index_brand[product_brand] = [product_id]


def test_1_9():
    from gloves.iterator import boolean_and_not

    global inverted_index_brand
    global inverted_index_title
    result9 = list(
        boolean_and_not(
            iter(inverted_index_title["Amazon"]),
            iter(inverted_index_brand["Amazon Basics"]),
        )
    )
    assert 8681 == len(result9)
