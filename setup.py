"""Setup script for Telegram Game Engine."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="tg-bot-engine",
    version="0.5.6",
    description="Production-ready game engine for Telegram bots with command-based architecture, ACID transactions, and event-driven modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TG Bot Engine Team",
    author_email="",
    url="https://github.com/yourusername/tg_bot_engine",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "demo_rpg", "demo_rpg.*", "docs", "docs.*", "scripts", "scripts.*"]),
    python_requires=">=3.9",
    install_requires=[
        "typing-extensions>=4.8.0",
        "jsonschema>=4.20.0",
    ],
    extras_require={
        "telegram": [
            "aiogram>=3.3.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.7.0",
            "ruff>=0.1.0",
        ],
        "all": [
            "aiogram>=3.3.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords="telegram bot game engine command-based async rpg transactions events",
    project_urls={
        "Documentation": "https://github.com/yourusername/tg_bot_engine/blob/main/docs/USAGE.md",
        "Source": "https://github.com/yourusername/tg_bot_engine",
        "Tracker": "https://github.com/yourusername/tg_bot_engine/issues",
    },
)

