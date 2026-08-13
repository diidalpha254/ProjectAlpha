"""
Setup configuration for Project Alpha
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="project-alpha",
    version="1.0.0",
    author="Project Alpha Team",
    description="Advanced Deriv Match/Differ Market Intelligence Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/project-alpha",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.14.0",
        "scikit-learn>=1.3.0",
        "websockets>=11.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "openpyxl>=3.1.0",
        "selenium>=4.15.0",
        "pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "project-alpha=app.main:main",
        ],
    },
)