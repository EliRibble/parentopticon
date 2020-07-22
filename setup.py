import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="parentopticon",
	version="0.0.1",
	author="Eli Ribble",
	author_email="junk@theribbles.org",
	description="A system for controlling kids access to computers.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/eliribble/parentopticon",
	packages=setuptools.find_packages(),
	install_requires = [
		"arrow==0.15.5",
		"flask==1.1.2",
		"Jinja2==2.11.1",
		"psutil==5.6.6",
		"requests==2.23.0",
		"toml==0.10.0",
	],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
)
