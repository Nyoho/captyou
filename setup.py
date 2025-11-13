from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="captyou",
    version="0.1.0",
    author="CaptyOU Team",
    description="リアルタイムポーズ・表情キャプチャシステム for macOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/captyou",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video :: Capture",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.9",
    install_requires=[
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "mediapipe>=0.10.0",
        "pyobjc-framework-AVFoundation>=9.0",
        "pyobjc-framework-CoreML>=9.0",
        "coremltools>=7.0",
        "python-osc>=1.8.0",
        "websockets>=11.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "black>=23.0.0", "flake8>=6.0.0"],
        "streaming": ["pyvirtualcam>=0.10.0"],
    },
)
