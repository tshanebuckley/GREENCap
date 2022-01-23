# GREENCap
Asynchronous Python SDK for working with REDCap data.

Currently, this repo includes a Python SDK that wraps PyCap, but runs asynchronous REDCap requests, a FastAPI server that utilizes the asyncronous SDK, and an RShiny frontend.

This is currently being built-out to function as a Python SDK with a self-container desktop application provided by the API and Shiny App.

After this initial goal is reached, the project will be scaled-up to operate as a middleware beteen a REDCap instance and a client.

## Current Goals of this Repo

1. Recreate some of the functionality of REDCapR, but in native Python.
2. Successfully wrap PyCap to create api payloads, but run these asynchronously.
3. Create a REST-like API for working with data that abstracts the api token and url.
4. Test this REST-like API with a demo FastAPI service and RShiny FrontEnd.

## Current State and Deliverables

Currently, this repo is at the stage where it has met the base-criteria of operating as a middleware between a REDCap server and
client machine for extracting record data from REDCap to the client. The Package can also operate as a standalone SDK for 
asynchronously pulling REDCap data. 

Future Deliverables:
1. Refactor API to stream responses as they complete from the main REDCap server instead of waiting for all requests to complete.
This behavior is fine for the SDK, but will act as a bottleneck at scale.
2. Have the client recieve middleware requests asynchronously (this should be simple given the use of the ijson package).
3. Refactor previous synchronous definitions to ustilize asncyio.run() to run their asynchronous versions.
4. Implement the pipeline runner utilizing Dagster

    A. First, running pipelines on the local machine.
    
    B. Second, running pipelines via Slurm on an HPC.
    
    C. Third, utilize MQ to go to scale.
    
    This is deliverable is inspired by following two project:
    
        DAX: https://github.com/VUIIS/dax
        
        Balsam: https://github.com/argonne-lcf/balsam
        
    Hoping that Balsam could be utilized to meet these goals.
    
5. Implement basic user authentification on middleware requests.
6. Finish an RShiny app front-end utilizing reticulate to utilize the Python SDK.
7. Implememt a file-server protocol, allowing the middleware to handle file storage for the client via REDCap.
8. Provide Dockerfile and Docker-compose implementations.
9. Create a CLI for starting up the middleware and for client functions.
10. Allow json configurations to be implemented with a MongoDB server.

## To Install

```bash
pip install --user git+https://github.com/tshanebuckley/GREENCap.git
```

## Basic usage

The goal is to keep the usage as close to PyCap as possible while extending the usage.

```python
# import the module
import greencap
# import asyncio
import asyncio
# create a "GREENCap Project"
gc = greencap.Project()
# add a project (saved under ~/.greencap/projects/my_project.json where "my_project" is the name of your REDCap Project)
# my_project.json is a simple json file that holds your url and api token
gc.add_project('my_project')
# fecth your data asynchronously
r = asyncio.run(gc.exec_request(method='POST', selection_criteria={'fields': {'field_name'}}, rc_name='my_project', func_name='export_records'))
```

## Example project json

Project JSON files must be stored under the following path:
```bash
~/.greencap/projects
```

And should be defined as follows:
```json
{
  "url": "your url",
  "token": "your api token",
  "def_field": "project's id defining field"
}
```

## Starting the API

Navigate to your home directory, the FastAPI file. Then start the api.
```bash
# go to the directory
cd ~/.greencap/api
# start the api
uvicorn api:app
```

## TODO: Complete the client SDK and CLI
