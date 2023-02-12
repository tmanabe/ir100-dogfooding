import setuptools

setuptools.setup(
    name="gloves",
    version="0.5.1",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow"]},
    install_requires=["annoy", "requests", "tensorflow-hub", "tensorflow-macos"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
