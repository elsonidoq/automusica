
try:
    from setuptools import setup, find_packages
    extra_kw = dict(
        packages=find_packages(),
        install_requires=[],
        tests_require=[])
except ImportError:
    from distutils.core import setup
    extra_kw = dict(packages=['tesis', 'tesis.distcmds'])

setup(
    name="tesis",
    description="",
    long_description="",
    url="",
    author="",
    author_email="",
    **extra_kw
)