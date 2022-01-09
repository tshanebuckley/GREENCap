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
import redcap
import contextlib
import itertools
import requests
import pathlib

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
        # NOTE: REDCap's API opts-in by default, but we must set these criteria manually to setup asynchronous calls
        if chosen_records == []:
            # get the records
            chosen_records = run_selection(project=project, fields=project.def_field, syncronous=True)
        if chosen_fields == [] and chosen_forms == []:
            # get all of the fields
            chosen_fields = project.field_names
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
    # if running a single call
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
    print(df)
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
