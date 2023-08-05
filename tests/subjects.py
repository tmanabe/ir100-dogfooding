import os
import pandas as pd


# 0.3
products = pd.read_parquet(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "esci-data",
        "shopping_queries_dataset",
        "shopping_queries_dataset_products.parquet",
    )
)

# 0.5
queries = pd.read_parquet(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "esci-data",
        "shopping_queries_dataset",
        "shopping_queries_dataset_examples.parquet",
    )
)

# 0.7
products_us = products["us" == products.product_locale].sort_values("product_id")
queries_us = queries["us" == queries.product_locale]

# 0.8
merged_us = pd.merge(products_us, queries_us, on="product_id")

# 7.0
products_jp = products["jp" == products.product_locale].sort_values("product_id")

# For quick testing
sampled_products_us = products_us.sample(frac=0.01, random_state=0)
