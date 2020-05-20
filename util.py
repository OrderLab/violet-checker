import re

def read_mysql_config_file(filename):
    with open(filename, 'r') as cnf_file:
        cnf_data = cnf_file.read()
        cnf_data = re.sub(re.compile('#.*?\n'), ' ', cnf_data) # remove all comments
        utils = re.findall(r'\[\w+\]', cnf_data) # find all utilities
        cnf_data = re.split(r'\[\w+\]\s*', cnf_data) # split data by utilities
        cnf_data = [re.findall(r'\S+\s*=\s*\S+|\S+', c) for c in cnf_data] # find all configs
        cnfs = cnf_data[1:]
        return utils, cnfs

def read_postgresql_config_file(filename):
    with open(filename, 'r') as cnf_file:
        cnf_data = cnf_file.read()
        cnf_data = re.sub(re.compile('#.*?\n'), ' ', cnf_data) # remove all comments
        # cnf_data = cnf_data.split
        # utils = re.findall(r'\[\w+\]', cnf_data) # find all utilities
        # cnf_data = re.split(r'\[\w+\]\s*', cnf_data) # split data by utilities
        # print (cnf_data)
        # \S+\s*=\s*\'.*\'|
        cnf_data = [re.findall(r'\S+\s*=\s*\S+', cnf_data)] # find all configs
        # print (cnf_data)
        cnfs = cnf_data
        return cnfs

def flatten_list(l):
    r = []
    for e in l:
        if isinstance(e, str):
            r.append(e)
        elif isinstance(e, list):
            t = flatten_list(e)
            for i in t:
                if i not in r:
                    r.append(i)
    return r
