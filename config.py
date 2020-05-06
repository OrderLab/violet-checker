import re
from table import *

class Config:
    # def __init__(self, util, cnfs):
    #     self.util = util.replace('[', '').replace(']', '')
    #     self.cnfs = []
    #     self.impact_table_hit = []
    #     self.costs = {}
    #     # self.constraints = {}
    #     for c in cnfs:
    #         if re.match(r'\S+\s*=\s*\S+', c):
    #             t = ''.join(c.split()).split('=')
    #             if t[1].isdigit():
    #                 t[1] = int(t[1])
    #             # else:
    #             #     t_list = [ord(c) for c in list(t[1])]
    #             #     valueAsInt = 0
    #             #     for i in range(len(t_list)):
    #             #         valueAsInt |= t_list[i] << (i*8)
    #             #     t[1] = valueAsInt
    #             self.cnfs.append([t[0],t[1]])
    #         else:
    #             self.cnfs.append([c,1])
    
    def __init__(self, util, cnfs):
        self.util = util.replace('[', '').replace(']', '')
        self.impact_table_hit = []
        self.impact_table_id = -1
        self.costs = {}
        self.configs = self.get_default_configs()
        
        # self.constraints = {}
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                if t[1].isdigit():
                    t[1] = int(t[1])
                self.configs[t[0]] = t[1]
            else:
                self.configs[c] = 1


    def add_cnfs(self, cnfs):
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                if t[1].isdigit():
                    t[1] = int(t[1])
                self.configs[t[0]] = t[1]
            else:
                self.configs[c] = 1

    def find(self, cnfname):
        # print (self.cnfs)
        for c in self.configs:
            if c == cnfname:
                return self.configs[c]
        return []

    def check_impact(self, impact_table):
        hit = True
        for _id in impact_table.dict:
            hit = True
            for k in impact_table.dict[_id]['constraints']:
                v = impact_table.dict[_id]['constraints'][k]
                if k in self.configs:
                    if v != self.configs[k]:
                        hit = False
                else:
                    hit = False
            if hit:
                impact_table_row = impact_table.get_row(_id)
                self.costs = impact_table_row.costs
                self.constraints = impact_table_row.constraints
                self.pairs = [impact_table.get_row(p) for p in impact_table_row.pairs]
                self.pairs.sort(key=lambda x: x.costs['ET'], reverse=False)
                self.impact_table_id = _id
                break
        return hit

    # def check_impact(self, impact_table):
    #     hit = True
    #     for _id in impact_table.dict:
    #         self._id = _id
    #         for c in self.configs:
    #             name = c
    #             value = self.configs[c]
    #             hit = True
    #             if name in impact_table.dict[_id]['constraints']:
    #                 if value != impact_table.dict[_id]['constraints'][name]:
    #                     hit = False
    #             else:
    #                 hit = False
    #         if hit:
    #             impact_table_row = impact_table.get_row(_id)
    #             self.costs = impact_table_row.costs
    #             self.constraints = impact_table_row.constraints
    #             self.pairs = [impact_table.get_row(p) for p in impact_table_row.pairs]
    #             self.pairs.sort(key=lambda x: x.costs['ET'], reverse=False)
    #             break
    #     return hit

    # def sort_pairs(self):
    #     self.pairs.sort(key=lambda x: x.costs['ET'], reverse=False)
    
    def write_result(self, result_file):

        result_file.write('The configuration of ' + self.util + '...\n')
        result_file.write('hits STATE ' + str(self.impact_table_id) + ' from the impact table\n')


        result_file.write('\n')
        result_file.write('-'*20 + 'COSTS' + '-'*20 + '\n')
        if 'IO' in self.costs:
            _c = self.costs['IO']
            result_file.write(
                'read ' + str(_c['read'][0]) + ' bytes from ' + str(_c['read'][1]) + ' read calls\n' +
                'pread ' + str(_c['pread'][0]) + ' bytes from ' + str(_c['pread'][1]) + ' pread calls\n' +
                'write ' + str(_c['write'][0]) + ' bytes from ' + str(_c['write'][1]) + ' write calls\n' +
                'pwrite ' + str(_c['pwrite'][0]) + ' bytes from ' + str(_c['pwrite'][1]) + ' pwrite calls\n'
            )
        if 'ET' in self.costs:
            result_file.write(
                'Execution Time is ' + str(self.costs['ET']) + 'ms\n'
            )
        if 'IC' in self.costs:
            result_file.write(
                str(self.costs['IC']) + ' instructions'
            )
        if 'SC' in self.costs:
            result_file.write(
                ' and ' + str(self.costs['SC']) + ' system calls occured\n'
            )
        else:
            result_file.write(
                ' occured\n'
            )
        
        result_file.write('\n')
        result_file.write('-'*20 + 'RECOMMENDATIONS' + '-'*20 + '\n')
        for p in self.pairs:
            if p.costs['ET'] < self.costs['ET']:
                p.write_to_file(result_file)
            # result_file.write(str(p.costs['ET']) + '\n')




    def get_default_configs(self):
        return {
            'autocommit' : 1,
            'sync_binlog' : 1,
            'binlog_format' : 0,
            'sql_log_bin' : 1,
        }