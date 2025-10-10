#!/usr/bin/env python3
"""
Setup script for Biometric Trackpad Authentication System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="biometric-trackpad-auth",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A pure motion dynamics biometric authentication system using trackpad gestures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/biometric-trackpad-auth",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "pygame>=2.0.0",
        "evdev>=1.4.0",
    ],
    entry_points={
        "console_scripts": [
            "trackpad-train=realtime_verifier_advanced:main",
            "trackpad-verify=realtime_verify_with_display:main",
            "trackpad-visualize=trackpad_visualizer:main",
        ],
    },
)
