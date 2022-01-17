# import dependencies
from setuptools import setup, find_packages
import os
import requests

# get the user's home directory
HOME = os.path.expanduser('~')
# url of this repo
URL = 'https://github.com/tshanebuckley/GREENCap'

# run setup
setup(name='greencap',
    version='0.1',
    description='GREENCap: Asynchronous requests and middleware API for REDCap.',
    url=URL,
    author='Maintainer: Shane Buckley',
    author_email='tshanebuckley@gmail.com',
    #license='MIT',
    python_requires='>=3.6',
    #package_dir={'': 'GREENCap/greencap'},
    packages=['greencap', 'greencap/utils'],
    include_package_data=True,
    #packages=find_packages(),
    install_requires=[
          "pycap",
          "fastapi",
          "uvicorn[standard]",
          "pydantic",
          "pyyaml",
          "aiohttp",
          "aiofiles",
          "aiopath",
          "tqdm",
          "mergedeep",
          "configparser",
          "numpy",
          "pandas",
          "asgiref",
          "multipart",
          "dtale"
    ],
    zip_safe=False
)
    
# function to download a file from GitHub and save it on the install machine
def github_copy_file(url, github_path, system_path):
    # get the content of the file
    file_content = requests.get(url + '/' + github_path).content
    # get the file text
    file_text = file_content.decode('utf-8')
    # get the file name
    file_name = os.path.basename(github_path)
    # make the path to where the file should be saved
    os.makedirs(system_path, exist_ok=True)
    # save the file
    with open(system_path + '/' + file_name, 'w') as file:
        # write the file
        file.write(file_text)

# Downloading base config, shiny app, fastapi, and setup .greencap and other folders under the home directory
github_copy_file(URL, 'greencap_config.yaml', HOME + '/.greencap')
github_copy_file(URL, 'redcap_webapp.R', HOME + '/.greencap/shiny')
github_copy_file(URL, 'open_dtale.py', HOME + '/.greencap/shiny')
github_copy_file(URL, 'api.py', HOME + '/.greencap/api')

# Make directories for the user, groups, and projects
os.makedirs(HOME + '/.greencap/projects', exist_ok=True)
os.makedirs(HOME + '/.greencap/users', exist_ok=True)
os.makedirs(HOME + '/.greencap/groups', exist_ok=True)
