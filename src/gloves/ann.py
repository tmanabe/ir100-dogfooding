from annoy import AnnoyIndex
from gloves.inverted_index import SimpleInvertedIndex
from gloves.priority_queue import BatchPriorityQueue

from tensorflow import matmul
from tensorflow_hub import load


# 6.0
USE_TF_MODULE = load("https://tfhub.dev/google/universal-sentence-encoder/4")
VECTOR_SIZE = 512


# 6.2
def tf_module_batch_tokenizer_factory(tf_module):
    def tf_module_batch_tokenizer(strings):
        return tf_module(strings).numpy()

    return tf_module_batch_tokenizer


use_batch_tokenizer = tf_module_batch_tokenizer_factory(USE_TF_MODULE)


def dot_product_batch_prioritizer(product_vectors, query_vectors):
    return matmul(product_vectors, query_vectors, transpose_b=True).numpy()


class BatchProcessor(object):
    BATCH_SIZE = 512

    def __init__(self):
        self.id_buffer = []
        self.field_value_buffer = []

    def clear(self):
        self.id_buffer = []
        self.field_value_buffer = []

    def batch_add(self):
        self.clear()

    def add(self, id, field_value):
        self.id_buffer.append(id)
        self.field_value_buffer.append(field_value)
        if BatchProcessor.BATCH_SIZE <= len(self.id_buffer):
            self.batch_add()

    def batch_build(self):
        return None

    def build(self):
        self.batch_add()
        return self.batch_build()


class BatchRankingBuilder(BatchProcessor):
    def __init__(
        self,
        queries,
        sizes,
        batch_tokenizer=use_batch_tokenizer,
        batch_prioritizer=dot_product_batch_prioritizer,
    ):
        assert len(queries) == len(sizes)
        self.query_vectors = batch_tokenizer(queries)
        self.batch_priority_queue = BatchPriorityQueue(sizes)
        self.batch_tokenizer = batch_tokenizer
        self.batch_prioritizer = batch_prioritizer
        super().__init__()

    def batch_add(self):
        field_vectors = self.batch_tokenizer(self.field_value_buffer)
        priority_matrix = self.batch_prioritizer(field_vectors, self.query_vectors)
        self.batch_priority_queue.batch_push(priority_matrix, self.id_buffer)
        self.clear()

    def batch_build(self):
        return self.batch_priority_queue.batch_pop()


# 6.3
class BatchAnnoyIndexBuilder(BatchProcessor):
    def __init__(
        self,
        metric,
        n_trees,
        vector_size=VECTOR_SIZE,
        batch_tokenizer=use_batch_tokenizer,
    ):
        self.annoy_index = AnnoyIndex(vector_size, metric)
        self.batch_tokenizer = batch_tokenizer
        self.ids = []
        self.n_trees = n_trees
        super().__init__()

    def batch_add(self):
        field_vectors = self.batch_tokenizer(self.field_value_buffer)
        assert len(self.id_buffer) == len(field_vectors)
        for id, field_vector in zip(self.id_buffer, field_vectors):
            index = len(self.ids)
            self.annoy_index.add_item(index, field_vector)
            self.ids.append(id)
        self.clear()

    def batch_build(self):
        self.annoy_index.build(self.n_trees)
        return self.annoy_index, self.ids


# 6.5
def annoy_filter_factory(annoy_index, n_closest):
    def annoy_filter(vector):
        return iter(annoy_index.get_nns_by_vector(vector, n_closest))

    return annoy_filter


class ANNInvertedIndexBuilder(BatchProcessor):
    def __init__(self, filter, batch_tokenizer=use_batch_tokenizer):
        if not hasattr(self, "results"):
            self.inverted_index = SimpleInvertedIndex()
        self.filter = filter
        self.batch_tokenizer = batch_tokenizer
        self.body = self.inverted_index.body
        super().__init__()

    def batch_add(self):
        field_vectors = self.batch_tokenizer(self.field_value_buffer)
        assert len(self.id_buffer) == len(field_vectors)
        for id, field_vector in zip(self.id_buffer, field_vectors):
            for index in self.filter(field_vector):
                if index in self.body:
                    self.body[index].append(id)
                else:
                    self.body[index] = [id]
        self.clear()

    def batch_build(self):
        return self.inverted_index


# 6.9
def as_is_batch_tokenizer(jag):
    return jag
