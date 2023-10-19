import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("src/ecp/__init__.py") as f:
    lines = f.readlines()

version = None
for l in lines:
    if l.startswith("__version__"):
        version = l.split("=")[1].strip()[1:-1]

if version is None:
    raise Exception("Version not found!")

setuptools.setup(
    name="py-ecp",
    version=version,
    author="Conqu3red",
    description="ECP programming language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ecp-lang/ecp-interpreter",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "tabulate",
        "astor",
        "parsergen==2.0.0b9"
    ],
    entry_points = {
        'console_scripts': [
            'ecp = ecp.__main__:main'
        ]
    },
)