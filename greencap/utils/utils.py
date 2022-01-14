from typing import Optional
from asgiref.sync import async_to_sync, sync_to_async
from mergedeep import merge, Strategy
from functools import reduce
import configparser
import fnmatch
import json
import yaml
import numpy as np
import pandas as pd
import os
import sys
import threading
import asyncio
import aiohttp
import aiofiles
import redcap
import contextlib
import itertools
import requests
import pathlib
from greencap.utils import creds as gc_creds

# covenience function for prunning a parsed selection
def run_selection(project = None, records: Optional[str] = "", arms: Optional[str] = "", events: Optional[str] = "", forms: Optional[str] = "", fields: Optional[str] = "", syncronous=False, num_chunks=50):
    chosen_fields = [] # project.def_field
    chosen_forms = []
    chosen_records = []
    if records != "":
        chosen_records = records.split(';')
    if forms != "":
        chosen_forms = forms.split(';')
    # if fields are given for the selection
    if fields != "":
        # add the optional selections
        selected_fields = fields.split(";")
        # for each field
        for selection in selected_fields:
            # determine if the selection is a single field, a selection of fields, or an entire form
            is_type = field_or_selection(project=project, item=selection)
            # if it is whole form
            #if is_type == "form":
            #    # add the form selection
            #    chosen_forms.append(selection)
            # if it is a single field
            if is_type == "field":
                # add the single field selection
                chosen_fields.append(selection)
            # if it is a selection of fields
            elif is_type == "field_selection":
                # split the selection
                split_str = split_form_and_str(full_str = selection)
                # parse the selection of multiple fields
                parsed_fields = parse_field_single_selection(selection_item = split_str["form_name"], selection_str = split_str["select_str"])
                # add the fields
                chosen_fields.extend(parsed_fields)
    # initialize the df as an empty list
    df = []
    # if running an asynchronous call
    if syncronous == False:
        # if records, fields, or forms were not selected, "opt-in" for all of that criteria
        # NOTE: PyCap opts-in by default, but we must set these criteria manually to setup asynchronous calls
        if chosen_records == []:
            # get the records
            chosen_records = run_selection(project=project, fields=project.def_field, syncronous=True)
        if chosen_fields == [] and chosen_forms == []:
            # get all of the fields
            chosen_fields = project.field_names
        print("CHOSEN RECORDS:")
        print(chosen_records)
        # get the kwargs
        selection_criteria = {"records": chosen_records, "fields": chosen_fields, "forms": chosen_forms}
        # get all of the possible single item api calls
        api_calls = extend_api_calls(project, selection_criteria=selection_criteria, num_chunks=num_chunks)
        #print(api_calls)
        # run the api calls asynchronously
        results = asyncio.run(run_pycap_requests(project=project, function_name='export_records', api_calls=api_calls))
        #print(results)
        #print(len(results))
        #print(type(results))
        #print(results[0])
        # rename to match downstream logic
        df = results
    # if a syncronous api call is desired single call
    elif syncronous == True:
        # pull data using PyCap, convert to a pandas dataframe: will eventually be deprecated by async records call
        df = project.export_records(records=chosen_records, fields=chosen_fields, forms=chosen_forms)
        # wrap into a list of length 1 to follow iterative logic that follow
        df = [df]
    #df = clean_content()
    #-----------------------
    # at this point, return the df if it is empty
    if df == [[]]:
        df = dict()
        json.dumps(df)
        df = json.loads(df)
        return df
    # TODO: reformat the below to handle the single return dict (as given), or run each return dict and then merge
    print("Finished getting requests, trimming and elongating if longitudinal...")
    # if the project is longitudinal
    if is_longitudinal(project):
        # trin the longitudinal study of unwanted data
        df = trim_longitudial_project(df=df, arms=arms, events=events)
    # if the df is a list with a single dictionary
    if isinstance(df, dict):
        # convert the dictionary to a dataframe
        df = pd.DataFrame.from_dict(df)
    # if the df is a list of dictionaries
    elif isinstance(df, list):
        # convert the list of dictionaries to a list of dataframes
        df = [pd.DataFrame.from_dict(x) for x in df]
        # if there are multiple dataframe in the list
        if len(df) > 1:
            # merge the dataframes TODO: parallelize this merge
            df = reduce(lambda x, y: pd.merge(x, y, how='outer', suffixes=(False, False)), df)
        # otherwise
        else:
            df = df[0]
    #print(df)
    # if the study is longitudinal
    if is_longitudinal(project):
        # reformat to a wide dataframe
        df = df.pivot(index = project.def_field, columns = "redcap_event_name") #chosen_fields[0]
        collapsed_cols = []
        for col in df.columns:
            collapsed_cols.append(col[0] + '#' + col[1]) # '#' used to separate field and event
        df.columns = collapsed_cols
    #_______________________
    #print(df)
    # TODO: implement pipe running here (with its own cache?)
    # here, if the dataframe is empty and the only chosen field is the def_field (allows returning only records names)
    if df.empty and chosen_fields == [project.def_field]:
        # then set the df to a set of the records
        df = tuple(df.index)
        # convert the set into a json string
        df = json.dumps(df)
    # otherwise
    else:
        # convert back to json and return
        df = df.to_json()
    df = json.loads(df)
    #print(df)
    return df

# method to drop arms from a returned api call (dict)
def drop_arms(arms_list, df):
    # drop arms not in the selection
    df = [x for x in df if x["redcap_event_name"].split("_arm_")[-1] in arms_list]
    # return the updated dict
    return df

# method to drop events from a returned api call (dict)
def drop_events(events_list, df):
    # drop events not in the selection
    df = [x for x in df if x["redcap_event_name"].split("_arm_")[0] in events_list]
    # return the updated dict
    return df

# method to trim unwanted longitudinal data (arms and events given as comma-separated strings)
def trim_longitudial_project(df, arms="", events="", n_cpus=1):
    # TODO: parallelize this step
    # initialize the input_is_dict boolean to False
    input_is_dict = False
    # if the df is a single dict
    if isinstance(df, dict):
        # then wrap it in a list
        df = [df]
        # set the input_is_dict boolean to True
        input_is_dict = True
    # if arms are given for the selection
    if arms != "":
        # TODO: check the regex instead
        arms_list = arms.split(",")
        # drop arms not in the arms selection
        df = [drop_arms(arms_list=arms_list, df=x) for x in df]
    # if events are given for the selection
    if events != "":
        # TODO: check the regex instead
        events_list = events.split(",")
        # drop events not in the events selection
        df = [drop_events(events_list=events_list, df=x) for x in df]
    # if the list is of length 1 and the input was a dict, return to just a dict
    if len(df) == 1 and isinstance(df, list) and input_is_dict:
        df = df[0]
    # return the trimmed project data (dict)
    return df
    
# convenience function to see if the item is a field or selection of fields
def field_or_selection(project = None, item = None):
    is_field = False
    #is_form = False
    # check if field
    if item in project.field_names:
        is_field = True
    # check if form
    #if item in project.forms:
    #    is_form = True
    # return options
    if is_field == False and '[' in item:
        # split by '[' and grab the first item
        field_name = item.split('[')[0]
        if field_name in project.forms:
            return "field_selection"
    #elif is_field == is_form == False:
    #    return "neither"
    elif is_field == True: #and is_form == False:
        return "field"
    else:
        return "neither"

# async method to run a list of api calls
async def run_pycap_requests(project, function_name, api_calls):
    print('Trying async {num_of_calls} call(s) ...'.format(num_of_calls=str(len(api_calls))))
    # get thge list of asynchronous api calls
    tasks = []
    call_num = 0
    for api_call in api_calls:
        # iterate the call_num
        call_num = call_num + 1
        #print(api_call)
        task = asyncio.ensure_future(async_pycap(project=project, function_name=function_name, call_args=api_call, call_id=call_num))
        tasks.append(task)
    # run and return the list of calls
    response = await asyncio.gather(*tasks)
    return response

# method that generates chunks
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    #for i in range(0, len(lst), n): -> by a chunk-size n
    #    yield lst[i:i + n]
    for i in range(0, n): # number of chunks
        yield lst[i::n]

# method that runs the deep merge over a chunk
def merge_chunk(chunk_as_list_of_dicts):
    # initialize the return dict as an empty dict
    chunk_as_dict = dict()
    # merge all of the dicts in the chunk
    merge(chunk_as_dict, *chunk_as_list_of_dicts, strategy=Strategy.TYPESAFE_ADDITIVE)
    # drop duplicated items in any lists
    for key in chunk_as_dict.keys():
        # if the value is a list
        if isinstance(chunk_as_dict[key], list):
            # drop duplicate items
            chunk_as_dict[key] = list(set(chunk_as_dict[key]))
    # return the combined dict
    return chunk_as_dict
    
# TODO: parallelize this
# TODO: try adding events to extended_by
# method to create all individual api calls for a selection, follows an "opt-in" approach instead of PyCaps's "opt-out" approach on selection
def extend_api_calls(project, selection_criteria=None, extended_by=['records'], num_chunks=10): # , 'fields', 'forms'
    # drop any empty selection criteria
    selection_criteria = {key: selection_criteria[key] for key in selection_criteria.keys() if selection_criteria[key] != [] and selection_criteria[key] != None}
    # for any selection criteria set to 'all', set to a list of all items for that project
    # TODO: add some type of schema here
    # update what is given the selection criteria if 'all' is selected
    for key in selection_criteria.keys():
        # if selecting all elements of this
        if selection_criteria[key] == 'all':
            # update the selection
            selection_criteria[key] = getattr(project, key) # NOTE: can add a schema here that attempts this if not found in schema
    # get the set of criteria to not extend by
    try:
        not_extended_by = set(selection_criteria.keys()) - set(extended_by)
         # get the criteria not being extended by while removing them from the selection_criteria
        not_extended_by = {key: selection_criteria.pop(key) for key in not_extended_by}
    except:
        not_extended_by = set()
    # if not_extended_by is empty, then set it to None
    if len(not_extended_by) == 0:
        not_extended_by = None
    # converts the dict into lists with tags identifying the criteria: from criteria: value to <criteria>_value
    criteria_list = [[key + '_' + item for item in selection_criteria[key]] for key in selection_criteria.keys()]
    # gets all permutations to get all individual calls
    extended_call_list_of_tuples = list(itertools.product(*criteria_list))
    # method to convert the resultant list of tubles into a list of dicts
    def crit_tuple_to_dict(this_tuple, extend_to_dicts=None):
        # get the list of key
        keys = {x.split('_')[0] for x in this_tuple}
        # initialize the dicts
        this_dict = {this_key: [] for this_key in keys}
        # fill the list of dicts
        for item in this_tuple:
            # get the key
            key = item.split('_')[0]
            # get the value
            value = item.replace(key + '_', '', 1)
            # add the value
            this_dict[key].append(value)
        # if there were fields the calls were not extended by
        if extend_to_dicts != None:
            this_dict.update(not_extended_by)
        # return the list of dicts
        return this_dict
    # convert the list of lists back into a list of dicts
    extended_call_list_of_dicts = [crit_tuple_to_dict(this_tuple=x, extend_to_dicts=not_extended_by) for x in extended_call_list_of_tuples]
    #print(extended_call_list_of_dicts)
    # method to re-combine the max-width jobs split into n chunks
    def condense_to_chunks(all_api_calls, num_chunks):
        # chunk the api_calls list
        chunked_calls_unmerged = list(chunks(lst=all_api_calls, n=num_chunks))
        # merge the chunks idividual calls
        chunked_calls_merged = [merge_chunk(x) for x in chunked_calls_unmerged]
        # return the api calls
        return chunked_calls_merged
    # chunk the calls
    final_call_list = condense_to_chunks(all_api_calls=extended_call_list_of_dicts, num_chunks=num_chunks)
    # drop any empty api_calls
    final_call_list = [x for x in final_call_list if x != {}]
    #print(final_call_list)
    # return the list of api requests
    return final_call_list

# method to retun if a project has events
def has_events(project):
    # if the project has no events, return False
    if len(project.events) == 0:
        return False
    # otherwise, return True
    else:
        return True

# method to retun if a project has arms
def has_arms(project):
    # if the project has no arms, return False
    if len(project.arm_nums) == 0:
        return False
    # otherwise, return True
    else:
        return True

# method to return if a project is longitudinal or not
def is_longitudinal(project):
    # if the project has events or arms, return True
    if has_events(project) or has_arms(project):
        return True
    # otherwise, return false
    else:
        return False

# method to get the records for a project asynchronously
async def async_get_records(rc_name):
    # get the credentials
    creds = await gc_creds.async_get_project_config(project = rc_name)
    # generate the payload
    payload = {
        'token': creds['token'],
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'fields[0]': creds['def_field'],
        'rawOrLabel': 'raw',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json',
    }
    # run a basic request to fetch these ids
    async with aiohttp.ClientSession() as session:
        async with session.post(creds['url'], data=payload) as response:
            resp = await response.text()
            print(response)
    # clean the result into a list
    resp_dict = json.loads(resp)
    # get the ids only from the response
    records = [x['registration_redcapid'] for x in resp_dict]
    # return the resultant list
    return records
