import re
from table import *

class Config:
    def __init__(self, util, cnfs):
        self.util = util.replace('[', '').replace(']', '')
        self.impact_table_hit = []
        self.impact_table_id = -1
        self.costs = {}
        self.configs = self.__get_default_configs()
        
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
                self.pairs = [p for p in self.pairs if p.costs['ET'] < self.costs['ET']]
                self.impact_table_id = _id
                break
        return hit

    def write_result(self, result_file):

        result_file.write('[+] VIOLET has detected some potential bad configurations in your configuration file:\n\n')

        for p in self.pairs:
            diff_c = []
            for p_c in p.constraints:
                if p.constraints[p_c] != self.configs[p_c]:
                    diff_c.append(p_c)
            if not diff_c:
                continue # shouldn't be empty
            for c in diff_c:
                result_file.write('[%s]' % (c))
            result_file.write('\nYour current setting is:\n')
            for c in diff_c:
                result_file.write('    %s = %s\n' % (c, self.configs[c]))
            result_file.write('A better setting could be:\n')
            for c in diff_c:
                result_file.write('    %s = %s\n' % (c, p.constraints[c]))
            result_file.write('Potential performance impacts are:\n')
            result_file.write('    When the workload is\n')
            p.write_workloads(result_file, 8)
            r = self.costs['ET'] / p.costs['ET'] * 100
            result_file.write('    The new setting is %s faster than your current setting\n'
                % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
            )
            p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
            total_readbytes = self.costs['IO']['read'][0] + self.costs['IO']['pread'][0]
            if p_total_readbytes < total_readbytes:
                result_file.write('    The total bytes read (read+pread) is reduced by %.2f%%\n'
                    % ((total_readbytes - p_total_readbytes) / total_readbytes * 100)
                )
            p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
            total_readcalls = self.costs['IO']['read'][1] + self.costs['IO']['pread'][1]
            if p_total_readcalls < total_readcalls:
                result_file.write('    The total read calls (read+pread) is reduced by %.2f%%\n'
                    % ((total_readcalls - p_total_readcalls) / total_readcalls * 100)
                )
            p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
            total_writebytes = self.costs['IO']['write'][0] + self.costs['IO']['pwrite'][0]
            if p_total_writebytes < total_writebytes:
                result_file.write('    The total bytes written (write+pwrite) is reduced by %.2f%%\n'
                    % ((total_writebytes - p_total_writebytes) / total_writebytes * 100)
                )
            p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
            total_writecalls = self.costs['IO']['write'][1] + self.costs['IO']['pwrite'][1]
            if p_total_writecalls < total_writecalls:
                result_file.write('    The total write calls (write+pwrite) is reduced by %.2f%%\n'
                    % ((total_writecalls - p_total_writecalls) / total_writecalls * 100)
                )
            result_file.write('\n')


    def __get_default_configs(self):
        return {
            'autocommit' : 1,
            'sync_binlog' : 1,
            'binlog_format' : 0,
            'sql_log_bin' : 1,
        }