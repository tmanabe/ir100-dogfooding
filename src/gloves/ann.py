import tensorflow as tf
import tensorflow_hub as hub


def dot_product(product_vectors, query_vectors):
    return tf.matmul(product_vectors, tf.transpose(query_vectors))


embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
