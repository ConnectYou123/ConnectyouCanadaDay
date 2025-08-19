"""
Setup script for the Value Investing Stock Finder application.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="value-investing-stock-finder",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A sophisticated Python application for finding value investing opportunities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stock-finder",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stock-finder=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="value investing, stock analysis, financial analysis, warren buffett, benjamin graham",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/stock-finder/issues",
        "Source": "https://github.com/yourusername/stock-finder",
        "Documentation": "https://github.com/yourusername/stock-finder/blob/main/README.md",
    },
)
