from gloves.iterator import sum_count_boolean_and
from gloves.iterator import sum_count_boolean_or


class WordQuery(object):
    def __init__(self, word):
        self.word = word

    def debug_print(self):
        return f"WordQuery({self.word})"

    def iterator(self, inverted_index):
        return iter(inverted_index.get(self.word, []))


# 4.1
class BooleanAndQuery(object):
    def __init__(self, query_i, query_j):
        self.query_i = query_i
        self.query_j = query_j

    def debug_print(self):
        return f"BooleanAndQuery({self.query_i.debug_print()}, {self.query_j.debug_print()})"

    def iterator(self, inverted_index):
        iterator_i = self.query_i.iterator(inverted_index)
        iterator_j = self.query_j.iterator(inverted_index)
        return sum_count_boolean_and(iterator_i, iterator_j)


# 4.7
class BooleanOrQuery(object):
    def __init__(self, query_i, query_j):
        self.query_i = query_i
        self.query_j = query_j

    def debug_print(self):
        return f"BooleanOrQuery({self.query_i.debug_print()}, {self.query_j.debug_print()})"

    def iterator(self, inverted_index):
        iterator_i = self.query_i.iterator(inverted_index)
        iterator_j = self.query_j.iterator(inverted_index)
        return sum_count_boolean_or(iterator_i, iterator_j)


def parse_and(and_term):
    result = None
    for word in and_term.split():
        if result is None:
            result = WordQuery(word)
        else:
            result = BooleanAndQuery(result, WordQuery(word))
    return result


def parse_or(or_term):
    result = None
    for and_term in or_term.split(" OR "):
        if result is None:
            result = parse_and(and_term)
        else:
            result = BooleanOrQuery(result, parse_and(and_term))
    return result


def parse(query):
    return parse_or(query)
