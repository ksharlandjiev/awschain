import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Conditionally load requirements.txt if it exists
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r", encoding="utf-8") as f:
        requirements = f.read().splitlines()
else:
    requirements = []

setup(
    name="awschain",
    version="0.1.1",
    author="Kamen Sharlandjiev",
    author_email="ksharlandjiev@gmail.com",
    description="A framework for chaining AWS services using the chain of responsibility pattern",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ksharlandjiev/awschain",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={"awschain": ["**/*.py"]},
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=requirements,  # Optional if requirements.txt doesn't exist
    test_suite='tests',
)
