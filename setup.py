import setuptools

setuptools.setup(
    name="gloves",
    version="0.2.7",
    extras_require={"test": ["pytest"]},
    install_requires=["fastparquet", "pandas", "pyarrow"],
    packages=setuptools.find_packages(exclude=["tests"]),
)
