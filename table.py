import re
import csv
from util import *

class ImpactTableRow:
    def __init__(self, state_id, constraints, costs, pairs, workloads):
        self.state_id = state_id
        self.constraints = constraints
        self.costs = costs
        self.pairs = pairs
        #TODO add workload?
        self.workloads = workloads
    
    def write_to_file(self, file):
        file.write('########## STATE %s RECORD ##########\n' % (self.state_id))
        # file.write('state %s from the cost impact table\n' % (self.state_id))
        file.write('constraints =>\n')
        for c in self.constraints:
            file.write(' '*5 + '%s = %s\n' % (c, self.constraints[c]))
        file.write('the total execution time was %sms\n' % (self.costs['ET']))
        file.write('total %s instructions and %s syscalls were occured\n' % (self.costs['IC'], self.costs['SC']))
        file.write('\n')
        
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
                if 'workloads' in self.dict[state_id]:
                    print (self.dict[state_id]['workloads'])
                self.costs_handler(state_id, costs)
                self.workloads_handler(state_id)
                # print (self.dict[state_id]['workloads'])
                for i in self.dict[state_id]['workloads']:
                    print (i)
                print ('-'*20)

    def constraints_handler(self, state_id, constraints):
        for c in [c.split('==') for c in constraints]:
            if c[1].isdigit():
                    c[1] = int(c[1])
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

    def workloads_handler(self, state_id):
        if 'workloads' not in self.dict[state_id]:
            self.dict[state_id]['workloads'] = []
            return

        workload = None
        index = self.dict[state_id]['workloads']
        if len(index) == 1:
            # TODO handle workload by -> self.workloadindex['workload_<index>'].append[state_id]
            workload = self.workload_json[index[0]]
        elif len(index) == 2:
            workload = self.workload_json[index[0]][index[1]]
        if not workload:
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
        if workload_index in self.workload_type:
            self.workload_type[workload_index].append(state_id)
        else:
            self.workload_type[workload_index] = [state_id,]

        
        
    def find_all_pairs(self, n):
        for id_i in self.dict:
            self.dict[id_i]['pairs'] = []
            for id_j in self.dict:
                _n = n
                ok = True
                if id_i == id_j:
                    continue
                else:
                    for c in self.dict[id_i]['constraints']:
                        if c in self.dict[id_j]['constraints']:
                            if self.dict[id_i]['constraints'][c] != self.dict[id_j]['constraints'][c]:
                                _n -= 1
                        else:
                            ok = False
                        if _n < 0:
                            ok = False
                    if ok:
                        self.dict[id_i]['pairs'].append(id_j)

    def write_worst_workload(self, file, n):

        assert n >= 0, "n must be larger than zero"
        if n == 0:
            return

        rows = [self.get_row(_id) for _id in self.dict]
        rows.sort(key=lambda x: x.costs['ET'], reverse=True)
        
        file.write('--------- TOP %s WORST WORKLOAD(s) FROM THE IMPACT TABLE ---------\n' % (n))

        for r in rows:
            file.write('########## WORKLOAD RECORD ##########\n')
            file.write('State %s workloads =>\n' % (r.state_id))
            if not r.workloads:
                file.write('          None\n')
            else:
                for w in r.workloads:
                    file.write('          %s\n' % (w))
            file.write('constraints =>\n')
            for c in r.constraints:
                file.write(' '*5 + '%s = %s\n' % (c, r.constraints[c]))
            file.write('the total execution time was %sms\n' % (r.costs['ET']))
            file.write('total %s instructions and %s syscalls were occured\n' % (r.costs['IC'], r.costs['SC']))
            file.write('\n')

            n -= 1
            if not n:
                break
        
        file.write('\n')

    def write_workload_suggestion(self, file):

        file.write('------------------------ WORKLOAD SUGGESTIONS --------------------\n')

        for index in self.workload_type:
            rows = [self.get_row(_id) for _id in self.workload_type[index]]
            rows.sort(key=lambda x: x.costs['ET'], reverse=False)
            for r in rows:
                file.write('########## WORKLOAD RECORD ##########\n')
                file.write('State %s workloads =>\n' % (r.state_id))
                if not r.workloads:
                    file.write('          None\n')
                else:
                    for w in r.workloads:
                        file.write('          %s\n' % (w))
                file.write('constraints =>\n')
                for c in r.constraints:
                    file.write(' '*5 + '%s = %s\n' % (c, r.constraints[c]))
                file.write('the total execution time was %sms\n' % (r.costs['ET']))
                file.write('total %s instructions and %s syscalls were occured\n' % (r.costs['IC'], r.costs['SC']))
                file.write('\n')
                break

        file.write('\n')


    def get_row(self, state_id):
        constraints = self.dict[state_id]['constraints']
        costs = self.dict[state_id]['costs']
        pairs = self.dict[state_id]['pairs']
        workloads = self.dict[state_id]['workloads']
        return ImpactTableRow(state_id, constraints, costs, pairs, workloads)
    
    def __get_workload_json(self):
        ___point = 'SELECT * FROM tbl WHERE id = 1'
        ___simple = 'SELECT * FROM tbl WHERE id BETWEEN 5 AND 10'
        ___orderby = 'SELECT * FROM tbl WHERE id BETWEEN 5 AND 10 ORDER BY col'
        ___sum = 'SELECT SUM(col) FROM tbl WHERE id BETWEEN 5 AND 10 ORDER BY col'
        ___distinct = 'SELECT DISTINCT * FROM tbl WHERE id BETWEEN 5 AND 10 ORDER BY col'
        ___insert = 'INSERT INTO tbl(col) VALUES(10)'
        ___no_index = 'UPDATE tbl SET col=10 WHERE id=4'
        ___index = 'UPDATE tbl SET col=col+1 WHERE id=4'
        ___delete = 'DELETE FROM tbl WHERE id = 1'
        __range = [___simple, ___orderby, ___sum, ___distinct]
        __select = [___point, __range]
        __update = [___no_index, ___index]
        _json = [__select, ___insert, __update, ___delete]

        _read = [_json[0][1], _json[0], _json[0], _json[0][0]]
        _insert = _json[1]
        _update = [_json[2][0], _json[2][1]]
        _write = _json[2]

        return [
            _read, _insert, _update, _write
        ]

        # return [
        #     flatten_list(_read), flatten_list(_insert)
        # ]

    def __get_constraints_process_table(self):
        return {
            'autocommit' : [255, 1],
            'binlog_format' : [72340172838076676, 4],
            'sql_log_bin' : [255, 1],
        }

            