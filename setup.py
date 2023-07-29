import setuptools

setuptools.setup(
    name="gloves",
    version="0.5.9",
    extras_require={"test": ["pytest", "fastparquet", "pandas", "pyarrow", "scipy"]},
    install_requires=["annoy", "tensorflow-hub", "tensorflow-macos", "requests"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
