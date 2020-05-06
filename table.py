import re
import csv

class ImpactTableRow:
    def __init__(self, state_id, constraints, costs, pairs):
        self.state_id = state_id
        self.constraints = constraints
        self.costs = costs
        self.pairs = pairs
        #TODO add workload?
    
    def write_to_file(self, file):
        file.write('########## STATE %s RECORD ##########\n' % (self.state_id))
        # file.write('state %s from the cost impact table\n' % (self.state_id))
        file.write('constraints are =>\n')
        for c in self.constraints:
            file.write(' '*5 + '%s = %s\n' % (c, self.constraints[c]))
        file.write('the total execution time is %sms\n' % (self.costs['ET']))
        file.write('total %s instructions and %s syscalls were occured\n' % (self.costs['IC'], self.costs['SC']))
        file.write('\n')
        


class ImpactTable:
    def __init__(self, filename):
        self.constraints_process_table = self.get_constraints_process_table()

        with open(filename, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file)
            self.fields = next(csv_reader)
            self.rows = []
            self.dict = {}
            for row in csv_reader:
                self.rows.append(row)
                state_id = int(row[0])
                self.dict[state_id] = {'constraints':{}, 'costs':{}}
                constraints = row[1].split('&&')
                costs = row[2].split(';')
                self.constraints_handler(state_id, constraints)
                self.costs_handler(state_id, costs)

    def constraints_handler(self, state_id, constraints):
        for c in [c.split('==') for c in constraints]:
            if c[1].isdigit():
                    c[1] = int(c[1])
            if c[0] in self.constraints_process_table:
                if c[1] == self.constraints_process_table[c[0]][0]:
                    c[1] = self.constraints_process_table[c[0]][1]
            if c[0] == 'index':
                if 'workload' in self.dict[state_id]:
                    self.dict[state_id]['workload'].append(c[1])
                else:
                    self.dict[state_id]['workload'] = [c[1],]
                return
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

    def workload_handler(self, state_id):
        if 'workload' not in self.dict[state_id]:
            return
        if self.dict[state_id]['workload'] == [0,1]:
            self.dict[state_id]['workload'] = 'range, options ...'
        elif self.dict[state_id]['workload'] == [0]:
            self.dict[state_id]['workload'] = 'write, '
        elif self.dict[state_id]['workload'] == [0,0]:
            pass
        elif self.dict[state_id]['workload'] == [1]:
            pass
        elif self.dict[state_id]['workload'] == [2,0]:
            pass
        elif self.dict[state_id]['workload'] == [2,1]:
            pass
        elif self.dict[state_id]['workload'] == [2]:
            pass
        
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

    def get_row(self, state_id):
        constraints = self.dict[state_id]['constraints']
        costs = self.dict[state_id]['costs']
        pairs = self.dict[state_id]['pairs']
        return ImpactTableRow(state_id, constraints, costs, pairs)
    

    def get_constraints_process_table(self):
        return {
            'autocommit' : [255, 1],
            'binlog_format' : [72340172838076676, 4],
            'sql_log_bin' : [255, 1],
        }

            