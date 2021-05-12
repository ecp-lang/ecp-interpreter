import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-ecp",
    version="1.2.0-b2",
    author="Conqu3red",
    description="ECP programming language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Conqu3red/pseudocode-interpreter",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    package_data = {
        "ecp": ["stdlib/*.*"]
    },
    install_requires=[
        "tabulate"
    ]
)