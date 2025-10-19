from setuptools import setup, find_packages

setup(
    name="eventdriven_template",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    description="Event-Driven Architecture Template with Django, React, Celery and Redis",
    author="Juan Del Monte",
    author_email="delmontejuan92@gmail.com",
    url="https://github.com/juandelmonte/eventdriven_template",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        # Core requirements will be installed from requirements.txt files
    ],
)
