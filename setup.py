from setuptools import setup, find_packages

setup(
    name="eventdriven_template",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "celery>=5.3.5",
        "redis>=5.0.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'run-daemon=daemon.processor:main',
        ],
    },
)
