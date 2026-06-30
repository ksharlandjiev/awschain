from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Library dependencies with minimum version bounds.
# For reproducible dev/CI builds, use requirements.txt (which has exact pins).
requirements = [
    "requests>=2.32.3",
    "boto3>=1.38.27",
    "python-dotenv>=1.1.0",
    "backoff>=2.2.1",
    "jsonpath-ng>=1.7.0",
    "PyYAML>=6.0.2",
]

setup(
    name="awschain",
    version="0.1.1.4",
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
    entry_points={
        'console_scripts': [
            'awschain-cli = awschain.cli:main',
        ],
    },    
    test_suite='tests',
)
