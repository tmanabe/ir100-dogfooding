from array import array


# 1.3
class SimpleInvertedIndex(object):
    def __init__(self):
        self.body = {}

    def __getitem__(self, word):
        return self.body.get(word, [])

    def __len__(self):
        return len(self.body)

    def iter(self, word):
        return iter(self[word])


class SimpleInvertedIndexBuilder(object):
    def __init__(self, tokenizer):
        if not hasattr(self, "results"):
            self.results = SimpleInvertedIndex()
        self.body = self.results.body
        self.tokenizer = tokenizer

    def add(self, id, field_value):
        for word in set(self.tokenizer(field_value)):
            if word in self.body:
                self.body[word].append(id)
            else:
                self.body[word] = [id]

    def build(self):
        results = self.results
        self.results = None
        return results


# 1.10
class PrefixIterator(object):
    def __init__(self, posting_list):
        self.posting_list = posting_list
        self.index = 0
        self.context = posting_list[0]

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.posting_list) <= self.index:
            raise StopIteration()
        suffix = self.posting_list[self.index]
        self.context = self.context[: len(self.context) - len(suffix)] + suffix
        self.index += 1
        return self.context


class PrefixInvertedIndex(SimpleInvertedIndex):
    def iter(self, word):
        return PrefixIterator(self[word])


class PrefixInvertedIndexBuilder(SimpleInvertedIndexBuilder):
    def __init__(self, tokenizer):
        if not hasattr(self, "results"):
            self.results = PrefixInvertedIndex()
        super().__init__(tokenizer)

    def build(self):
        for posting_list in self.body.values():
            context = posting_list[0]
            for index in range(1, len(posting_list)):
                target = posting_list[index]
                assert len(context) == len(target)
                prefix_length = 0
                while context[prefix_length] == target[prefix_length]:
                    prefix_length += 1
                posting_list[index] = target[prefix_length:]
                context = target
        return super().build()


# 1.11
class EncodeIterator(object):
    def __init__(self, posting_list, id_list):
        self.posting_list = posting_list
        self.index = 0
        self.id_list = id_list

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.posting_list) <= self.index:
            raise StopIteration()
        result = self.id_list[self.posting_list[self.index]]
        self.index += 1
        return result


class EncodeInvertedIndex(SimpleInvertedIndex):
    def __init__(self):
        self.id_list = []
        super().__init__()

    def iter(self, word):
        return EncodeIterator(self[word], self.id_list)


class EncodeInvertedIndexBuilder(SimpleInvertedIndexBuilder):
    def __init__(self, tokenizer):
        if not hasattr(self, "results"):
            self.results = EncodeInvertedIndex()
        self.id_list = self.results.id_list
        super().__init__(tokenizer)

    def add(self, id, field_value):
        index = len(self.id_list)
        self.id_list.append(id)
        for word in set(self.tokenizer(field_value)):
            if word in self.body:
                self.body[word].append(index)
            else:
                self.body[word] = [index]


# 1.12  Ref: https://nlp.stanford.edu/IR-book/html/htmledition/variable-byte-codes-1.html
def variable_byte_decode(byte_stream):
    numbers, n = [], 0
    for byte in byte_stream:
        if byte < 128:
            n = 128 * n + byte
        else:
            n = 128 * n + byte - 128
            numbers.append(n)
            n = 0
    return numbers


class VariableByteIterator(object):
    def __init__(self, byte_stream, id_list):
        self.deltas = variable_byte_decode(byte_stream)
        self.index = 0
        self.context = 0
        self.id_list = id_list

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.deltas) <= self.index:
            raise StopIteration()
        self.context += self.deltas[self.index]
        result = self.id_list[self.context]
        self.index += 1
        return result


class VariableByteInvertedIndex(EncodeInvertedIndex):
    def iter(self, word):
        return VariableByteIterator(self[word], self.id_list)


def variable_byte_encode_number(n):
    bytes = array("B")
    while True:
        bytes.insert(0, n % 128)
        if n < 128:
            break
        n //= 128
    bytes[-1] += 128
    return bytes


def variable_byte_encode(numbers):
    byte_stream = array("B")
    for n in numbers:
        byte_stream += variable_byte_encode_number(n)
    return byte_stream


class VariableByteInvertedIndexBuilder(EncodeInvertedIndexBuilder):
    def __init__(self, tokenizer):
        if not hasattr(self, "results"):
            self.results = VariableByteInvertedIndex()
        super().__init__(tokenizer)

    def build(self):
        # Delta compression
        for posting_list in self.body.values():
            context = 0
            for index in range(len(posting_list)):
                target = posting_list[index]
                posting_list[index] = target - context
                context = target
        # Variable byte encoding
        for word in self.body:
            self.body[word] = variable_byte_encode(self.body[word])
        return super().build()
