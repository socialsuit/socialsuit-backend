from setuptools import setup, find_packages

setup(
    name="shared",
    version="0.1.0",
    description="Shared library for Social Suit and Sparkr",
    author="Social Suit Team",
    author_email="team@socialsuit.example.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "sqlalchemy>=1.4.0",
        "pydantic>=1.8.0",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "redis>=4.0.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)