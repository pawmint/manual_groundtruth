# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


readme = open('README.md').read()

setup(
    name='Manual-Groundtruth',
    version='0.1.0',
    description=("Writing down observations about our dataset"),
    long_description=readme,
    author='Romain Endelin',
    author_email='romain.endelin@mines-telecom.fr',
    url='https://github.com/pawmint/manual_groundtruth.git',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'arrow>=0.5.4',
        'prompt-toolkit>=0.32'
    ],
    entry_points = {
        'console_scripts': ['manual-gt=manual_groundtruth.main:main'],
    },
    license='Copyright',
    zip_safe=True,  # To be verified
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
        'License :: Other/Proprietary License',
        'Topic :: Scientific/Engineering'
    ],
)
