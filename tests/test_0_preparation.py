from .subjects import products
from .subjects import queries


def test_0_4():
    for _ in range(3):
        print(products.sample())


def test_0_6():
    for _ in range(3):
        print(queries.sample())
