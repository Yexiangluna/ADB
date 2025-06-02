"""
ADB 项目安装配置文件
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("Readme.md", "r", encoding="utf-8") as f:
        return f.read()

# 读取requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="adb-database",
    version="1.0.0",
    author="ADB Development Team",
    author_email="dev@adb.com",
    description="轻量级基于API的数据库管理系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/adb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "api": [
            "flask>=2.0.0",
        ],
        "utils": [
            "python-dotenv>=0.19.0",
            "coloredlogs>=15.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "adb=adb.cli:main",
            "adb-server=adb.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "adb": [
            "templates/*.json",
            "static/*",
        ],
    },
)
