from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in victory_farms_custom_app/__init__.py
from victory_farms_custom_app import __version__ as version

setup(
	name="victory_farms_custom_app",
	version=version,
	description="Custom Inventory Report",
	author="Solufy",
	author_email="contact@solufy.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
