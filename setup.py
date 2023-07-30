import setuptools

setuptools.setup(
    name="gloves",
    version="0.6.7",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow", "scipy", "scikit-learn"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos", "requests"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
