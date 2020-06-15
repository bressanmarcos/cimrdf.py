from setuptools import setup, find_packages
import sys, os

version = '0.2'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cimrdf.py",
    version=version,
    author="Marcos Bressan",
    author_email="bressanmarcos@alu.ufc.br",
    description="Generate Python data structures from CIM RDF profiles, parse and serialize CIM-compliant information objects, according to IEC 61970-501 standard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bressanmarcos/cimrdf.py",
    entry_points={
        'console_scripts': [
            'cimrdfpy = cimrdfpy.generator:main'
        ]
    },
    packages=['cimrdfpy'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=True,
)
