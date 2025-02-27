from setuptools import setup, find_packages

setup(
    name="ebay-auction-tracker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9.6",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
) 