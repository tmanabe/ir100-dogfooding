import setuptools

setuptools.setup(
    name="gloves",
    version="0.4.3",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow", "requests"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
