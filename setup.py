import setuptools

setuptools.setup(
    name="gloves",
    version="0.7.6",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow", "scipy", "scikit-learn"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos", "pystemmer", "regex", "uniseg", "requests"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
