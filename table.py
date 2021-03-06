import re
import csv
from util import *
from config import *

class ImpactTableRow:
    def __init__(self, state_id, constraints, costs, pairs, workloads, workload_option):
        self.state_id = state_id
        self.constraints = constraints
        self.costs = costs
        self.pairs = pairs
        self.workloads = workloads
        self.workload_option = workload_option

    def write_constraints(self, file):
        for c in self.constraints:
            file.write(' '*4 + '%s = %s\n' % (c, self.constraints[c]))

    def write_costs(self, file):
        file.write('The total execution time was %sms\n' % (self.costs['ET']))
        file.write('Meanwhile, total %s instructions and %s syscalls were occured\n' % (self.costs['IC'], self.costs['SC']))
    
    def write_workloads(self, file, n):
        if not self.workloads:
            file.write(' '*n + 'None')
            return
        for w in self.workloads:
            file.write(' '*n + '%s\n' % (w))
    
    def get_workload_file_name(self):
        return 'oltp_' + self.workload_option + '.lua'
    
    def write_IO_results(self, file):
        _c = self.costs['IO']
        file.write('IO details:\n')
        file.write(
            '    read ' + str(_c['read'][0]) + ' bytes from ' + str(_c['read'][1]) + ' read calls\n' +
            '    pread ' + str(_c['pread'][0]) + ' bytes from ' + str(_c['pread'][1]) + ' pread calls\n' +
            '    write ' + str(_c['write'][0]) + ' bytes from ' + str(_c['write'][1]) + ' write calls\n' +
            '    pwrite ' + str(_c['pwrite'][0]) + ' bytes from ' + str(_c['pwrite'][1]) + ' pwrite calls\n'
        )

        
class ImpactTable:
    def __init__(self, filename):
        self.constraints_process_table = self.__get_constraints_process_table()
        self.workload_json = self.__get_workload_json()

        with open(filename, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file)
            self.fields = next(csv_reader)
            self.rows = []
            self.dict = {}
            self.workload_type = {}
            for row in csv_reader:
                self.rows.append(row)
                state_id = int(row[0])
                self.dict[state_id] = {'constraints':{}, 'costs':{}}
                constraints = row[1].split('&&')
                costs = row[2].split(';')
                self.constraints_handler(state_id, constraints)
                self.costs_handler(state_id, costs)
                # dont care the state if there is no workload index
                if 'workloads' not in self.dict[state_id]:
                    self.dict.pop(state_id, None)
                    continue
                self.workloads_handler(state_id)

    '''
    Handle constraints from each impact table row
    '''
    def constraints_handler(self, state_id, constraints):
        for c in [c.split('==') for c in constraints]:
            try:
                c[1] = int(c[1])
            except:
                try:
                    c[1] = float(c[1])
                except:
                    pass
            if c[0] in self.constraints_process_table:
                if c[1] == self.constraints_process_table[c[0]][0]:
                    c[1] = self.constraints_process_table[c[0]][1]
            if c[0] == 'index':
                if 'workloads' in self.dict[state_id]:
                    self.dict[state_id]['workloads'].append(c[1])
                else:
                    self.dict[state_id]['workloads'] = [c[1],]
                continue
            self.dict[state_id]['constraints'][c[0]] = c[1]
    
    '''
    Handle costs from each impact table row
    '''
    def costs_handler(self, state_id, costs):
        for c in [c.split('=>') for c in costs]:
            if c[0] == "IO":
                result = [int(n) for n in c[1].split(' ')]
                self.dict[state_id]['costs']['IO'] = {
                    'read' : [result[0], result[1]],
                    'write' : [result[2], result[3]],
                    'pread' : [result[4], result[6]],
                    'pwrite' : [result[6], result[7]],
                }
            elif c[0] == "ET":
                self.dict[state_id]['costs']['ET'] = float(c[1].split('ms')[0])
            elif c[0] == "IC":
                self.dict[state_id]['costs']['IC'] = int(c[1])
            elif c[0] == "SC":
                self.dict[state_id]['costs']['SC'] = int(c[1])

    '''
    Handle workloads from each impact table row
    '''
    def workloads_handler(self, state_id):
        if 'workloads' not in self.dict[state_id]:
            self.dict[state_id]['workloads'] = []
            return

        workload = None
        index = self.dict[state_id]['workloads']
        if len(index) == 1:
            workload = self.workload_json[index[0]]
        elif len(index) == 2:
            workload = self.workload_json[index[0]][index[1]]
        if not workload:
            self.dict[state_id]['workload_index'] = ''
            self.dict[state_id]['workload_option'] = ''
            return
        
        if not isinstance(workload, list):
            assert isinstance(workload, str), "the instance should be a string"
            workload = [workload]
        else:
            #flattern the workload list
            # workload = flatten_list(workload)
            workload = workload
        
        self.dict[state_id]['workloads'] = workload

        workload_index = ''.join([str(i) for i in index])
        self.dict[state_id]['workload_index'] = workload_index
        self.dict[state_id]['workload_option'] = self.__get_workload_options()[workload_index]
        if workload_index in self.workload_type:
            self.workload_type[workload_index].append(state_id)
        else:
            self.workload_type[workload_index] = [state_id,]

    '''
    This function finds all pairs that each has N different configuration values 
    '''        
    def find_all_pairs(self, n, target):
        t = []
        if target:
            t = target.split(',')
        for id_i in self.dict:
            self.dict[id_i]['pairs'] = []
            for id_j in self.dict:
                _n = n
                ok = True
                if id_i == id_j:
                    continue
                elif self.dict[id_i]['workload_index'] != self.dict[id_j]['workload_index']:
                    continue
                else:
                    for c in self.dict[id_i]['constraints']:
                        if c in self.dict[id_j]['constraints']:
                            if self.dict[id_i]['constraints'][c] != self.dict[id_j]['constraints'][c]:
                                if t:
                                    if c not in t:
                                        ok = False
                                _n -= 1
                        else:
                            ok = False
                        if _n < 0:
                            ok = False
                    if ok:
                        self.dict[id_i]['pairs'].append(id_j)
        
    # TODO depreciated function
    def make_workload_suggestion(self, result_file, my_config):

        result_file.write('[+] VIOLET would suggest the best configuration under various workloads:\n\n')
        for index in self.workload_type:
            rows = [self.get_row(_id) for _id in self.workload_type[index]]
            rows.sort(key=lambda x: x.costs['ET'], reverse=False)
            for r in rows:
                result_file.write('Under the workload:\n')
                r.write_workloads(result_file, 4)
                result_file.write('If the configuration is:\n')
                r.write_constraints(result_file)
                r = my_config.costs['ET'] / r.costs['ET'] * 100
                result_file.write('The performance is the best and is %s better than your current setting\n\n'
                    % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
                )
                break

    def get_row(self, state_id):
        constraints = self.dict[state_id]['constraints']
        costs = self.dict[state_id]['costs']
        pairs = self.dict[state_id]['pairs']
        workloads = self.dict[state_id]['workloads']
        workload_option = self.dict[state_id]['workload_option']
        return ImpactTableRow(state_id, constraints, costs, pairs, workloads, workload_option)
    
    def __get_workload_json(self):
        ___point = 'SELECT * FROM table_name WHERE id = value'
        ___simple = 'SELECT * FROM table_name WHERE id BETWEEN value AND value'
        ___orderby = 'SELECT * FROM table_name WHERE id BETWEEN value AND value ORDER BY column'
        ___sum = 'SELECT sum FROM table_name WHERE id BETWEEN value AND value ORDER BY column'
        ___distinct = 'SELECT DISTINCT * FROM table_name WHERE id BETWEEN value AND value ORDER BY column'
        ___insert = 'INSERT INTO table_name value'
        ___no_index = 'UPDATE table_name SET column = no index update WHERE id = value'
        ___index = 'UPDATE table_name SET column = index update WHERE id = value'
        ___delete = 'DELETE FROM table_name WHERE id = value'
        __range = [___simple, ___orderby, ___sum, ___distinct]
        __select = [___point, __range]
        __update = [___no_index, ___index]
        _json = [__select, ___insert, __update, ___delete]

        _read = [_json[0][1], _json[0], _json[0], _json[0][0]]
        _insert = _json[1]
        _update = [_json[2][0], _json[2][1]]
        _write = _json[2]

        return [
            _read, _insert, _update, _write,
        ]

    def __get_workload_options(self):
        return {
            '0' : 'read',
            '1' : 'insert',
            '2' : 'update',
            '3' : 'write',
            '00' : 'read_range',
            '01' : 'read_write',
            '02' : 'read_only',
            '03' : 'read_point',
            '20' : 'update_non_index',
            '21' : 'update_index',
        }
    
    def workload_options(self):
        return list(self.__get_workload_options().values())

    '''
    In the impact table, each system variable may be assigned a out-of-range value sometimes.
    This happens due to converting it from its symbolic value to concrete value in S2E.
    This function returns a table that allows us to preprocess those out-of-range value, 
    and it needs to be expand if necessary.
    '''
    def __get_constraints_process_table(self):
        return {
            'autocommit' : [255, 1],
            'binlog_format' : [72340172838076676, 4],
            'sql_log_bin' : [255, 1],
            'innodb_flush_log_at_trx_commit' : [72340172838076673, 2],
            'log_statement' : [16843009, 3],
        }

            