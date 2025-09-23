"""Setup para o projeto GeoSense"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="geosense",
    version="1.0.0",
    author="GeoSense Team",
    author_email="contato@geosense.com",
    description="Sistema de Detecção e Rastreamento de Motos para Mottu x FIAP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geosense/iot-sprint2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "geosense=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
)
