import setuptools

setuptools.setup(
    name="gloves",
    version="0.9.0",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow", "scipy", "scikit-learn", "xgboost"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos", "pystemmer", "regex", "uniseg", "mecab-python3", "unidic-lite", "requests"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
