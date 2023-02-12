import setuptools

setuptools.setup(
    name="gloves",
    version="0.3.5",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
