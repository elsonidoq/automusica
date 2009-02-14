
try:
    from setuptools import setup, find_packages
    extra_kw = dict(
        packages=find_packages(),
        install_requires=[],
        tests_require=[])
except ImportError:
    from distutils.core import setup
    extra_kw = dict(packages=['electrozart', 'electrozart.distcmds'])

setup(
    name="electrozart",
    description="",
    long_description="",
    url="",
    author="",
    author_email="",
    **extra_kw
)
