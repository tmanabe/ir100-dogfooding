import setuptools

setuptools.setup(
    name="gloves",
    version="1.0.0",
    extras_require={
        "test": [
            "pytest",
            "fastparquet",
            "pandas",
            "pyarrow",
            "scipy",
            "scikit-learn",
            "xgboost",
            "datasets",
            "transformers[torch]",
            "sentence_transformers",
        ]
    },
    install_requires=[
        "annoy",
        "tensorflow-hub",
        "tensorflow-macos",
        "pystemmer",
        "regex",
        "mecab-python3",
        "unidic-lite",
        "requests",
    ],
    packages=setuptools.find_packages(exclude=["tests"]),
)
