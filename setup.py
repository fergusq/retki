from setuptools import setup

setup(
	name='retki',
	version='0.12.1',
	description='Finnish programming language inspired by Inform 7',
	url='http://github.com/fergusq/retki',
	author='Iikka Hauhio',
	author_email='iikka.hauhio@gmail.com',
	license='GPL',
	classifiers=[
		'Programming Language :: Python :: 3'
	],
	packages=['retki'],
	python_requires='>=3',
	install_requires=['voikko', 'suomilog'],
	package_data={
		'retki': ['std.txt', 'tekstiseikkailukirjasto.txt'],
	},
	entry_points={
		'console_scripts': [
			'retki=retki.compiler:main',
		],
	},
)
