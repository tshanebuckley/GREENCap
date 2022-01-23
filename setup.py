# import dependencies
from setuptools import setup, find_packages
import os
import requests

# get the user's home directory
HOME = os.path.expanduser('~')
# GitHub path
GH_PATH = 'github.com/tshanebuckley/GREENCap'
# raw version url 
RAW = 'https://raw.' + GH_PATH
# GitHub url
URL = 'https://' + GH_PATH

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
          "ijson",
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
    file_content = requests.get(url + '/master/' + github_path).content
    # get the file text
    file_text = file_content.decode('utf-8')
    # get the file name
    file_name = os.path.basename(github_path)
    # make the path to where the file should be saved
    os.makedirs(system_path, exist_ok=True)
    # get the system file path
    system_file_path = system_path + '/' + file_name
     # if the file does not already exist
    if os.path.exists(system_file_path) == False:
        # save the file
        with open(system_file_path, 'w') as file:
            # write the file
            file.write(file_text)

# Downloading base config, shiny app, fastapi, and setup .greencap and other folders under the home directory
github_copy_file(RAW, 'greencap_config.yaml', HOME + '/.greencap')
github_copy_file(RAW, 'redcap_webapp.R', HOME + '/.greencap/shiny')
github_copy_file(RAW, 'open_dtale.py', HOME + '/.greencap/shiny')
github_copy_file(RAW, 'api.py', HOME + '/.greencap/api')

# Make directories for the user, groups, and projects
os.makedirs(HOME + '/.greencap/projects', exist_ok=True)
os.makedirs(HOME + '/.greencap/users', exist_ok=True)
os.makedirs(HOME + '/.greencap/groups', exist_ok=True)
