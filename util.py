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

def print_result_file(filename, _list):
    with open(filename, 'w') as result_file:
        for config in _list:
            if 'IO' in config.costs:
                _c = config.costs['IO']
                result_file.write(
                    'read ' + str(_c['read'][0]) + ' bytes from ' + str(_c['read'][1]) + ' read calls\n' +
                    'pread ' + str(_c['pread'][0]) + ' bytes from ' + str(_c['pread'][1]) + ' pread calls\n' +
                    'write ' + str(_c['write'][0]) + ' bytes from ' + str(_c['write'][1]) + ' write calls\n' +
                    'pwrite ' + str(_c['pwrite'][0]) + ' bytes from ' + str(_c['pwrite'][1]) + ' pwrite calls\n'
                )
            if 'ET' in config.costs:
                result_file.write(
                    'Execution Time is ' + str(config.costs['ET']) + 'ms\n'
                )
            if 'IC' in config.costs:
                result_file.write(
                    str(config.costs['IC']) + ' instruction(s)'
                )

            if 'SC' in config.costs:
                result_file.write(
                    ' and ' + str(config.costs['SC']) + ' system call(s) happened\n'
                )
            else:
                result_file.write(
                    ' happened\n'
                )
    print ('The result is written to ' + filename)



# def read_impact_table(filename):
#     with open(filename, 'r', encoding='utf-8-sig') as csv_file:
#         csv_reader = csv.reader(csv_file)
#         fields = next(csv_reader) # TODO return?
#         rows = []
#         for row in csv_reader:
#             print (row)
#             rows.append(row)
#         return rows
