from setuptools import setup, find_packages
import os

USER_PATH = os.path.expanduser('~')

setup(name='greencap',
      version='0.1',
      description='GREENCap: Asynchronous requests and middleware API for REDCap.',
      url='https://github.com/tshanebuckley/GREENCap',
      author='Maintainer: Shane Buckley',
      author_email='tshanebuckley@gmail.com',
      #license='MIT',
      python_requires='>=3.6',
      #package_dir={'': 'GREENCap/greencap'},
      packages=['greencap'],
      include_package_data=True,
      #packages=find_packages(),
      install_requires=[
            "pycap",
            "fastapi",
            "pydantic",
            "pyyaml",
            "aiohttp",
            "tqdm",
            "mergedeep",
            "configparser",
            "numpy",
            "pandas",
            "asgiref",
            "multipart",
            "dtale"
      ],
      data_files=[
            ('{HOME}/.greencap'.format(HOME=USER_PATH), ['greencap_config.yaml']),
            ('{HOME}/.greencap/projects'.format(HOME=USER_PATH), []),
            ('{HOME}/.greencap/users'.format(HOME=USER_PATH), []),
            ('{HOME}/.greencap/groups'.format(HOME=USER_PATH), []),
            ('{HOME}/.greencap/shiny'.format(HOME=USER_PATH), ['open_dtale.py', 'redcap_webapp.R'])
      ],
      zip_safe=False
      )
