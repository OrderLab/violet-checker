import re

def read_config_file(filename):
    with open(filename, 'r') as cnf_file:
        cnf_data = cnf_file.read()
        cnf_data = re.sub(re.compile('#.*?\n'), ' ', cnf_data) # remove all comments
        utils = re.findall(r'\[\w+\]', cnf_data) # find all utilities
        cnf_data = re.split(r'\[\w+\]\s*', cnf_data) # split data by utilities
        cnf_data = [re.findall(r'\S+\s*=\s*\S+|\S+', c) for c in cnf_data] # find all configs
        cnfs = cnf_data[1:]
        return utils, cnfs


# def read_impact_table(filename):
#     with open(filename, 'r', encoding='utf-8-sig') as csv_file:
#         csv_reader = csv.reader(csv_file)
#         fields = next(csv_reader) # TODO return?
#         rows = []
#         for row in csv_reader:
#             print (row)
#             rows.append(row)
#         return rows
