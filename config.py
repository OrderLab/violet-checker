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

    #TODO change to the current setting is how bad (how much slower,,,,)
    # TODO assume there's only one difference
    def write_result(self, result_file):

        diff = {}
        for c in self.configs:
            for p in self.pairs:
                if c not in p.constraints:
                    continue
                if self.configs[c] != p.constraints[c]:
                    if c not in diff:
                        diff[c] = [p,]
                    else:
                        diff[c].append(p)

        result_file.write(
            '[+] VIOLET has detected %s potential bad configuration%s in your configuration file:\n\n' % (
                len(diff), ['s',''][len(diff)==1]
            )
        )
        # TODO add summary; like this?

        for c in diff:
            result_file.write('[%s]\n' % (c))
            result_file.write('Your current setting is:\n')
            result_file.write('    %s = %s\n' % (c, self.configs[c]))
            result_file.write('There %s %s better setting%s:\n' % (['are','is'][len(diff[c])==1],len(diff[c]),['s',''][len(diff[c])==1]))
            for p in diff[c]:
                result_file.write('%s' % ([
                            ', %s'%([p.constraints[c],str(p.constraints[c])+'\n'][p is diff[c][len(diff[c])-1]]),
                            '    %s = %s'%(c, p.constraints[c])
                        ][p is diff[c][0]]))

            for p in diff[c]:
                result_file.write('> Compare to %s = %s:\n' % (c, p.constraints[c]))
                result_file.write('    Under the workload:\n')
                p.write_workloads(result_file, 8)
                result_file.write('    Potential performance impacts are:\n')
                r =  (self.costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
                result_file.write('        Your current setting is %s slower than the new setting\n'
                    % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
                )

                p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
                total_readbytes = self.costs['IO']['read'][0] + self.costs['IO']['pread'][0]
                p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
                total_readcalls = self.costs['IO']['read'][1] + self.costs['IO']['pread'][1]
                p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
                total_writebytes = self.costs['IO']['write'][0] + self.costs['IO']['pwrite'][0]
                p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
                total_writecalls = self.costs['IO']['write'][1] + self.costs['IO']['pwrite'][1]

                if total_readbytes > p_total_readbytes or total_readcalls > p_total_readcalls or\
                    total_writebytes > p_total_writebytes or total_writecalls > p_total_writecalls:
                    result_file.write('        I/O (read+pread/write+pwrite) impacts are:\n')

                if total_readbytes > p_total_readbytes:
                    if (p_total_readbytes == 0):
                        result_file.write('            The total bytes read is increased from 0 to %s bytes\n'
                            % (total_readbytes)
                        )
                    else:
                        result_file.write('            The total bytes read is increased by %.2f%%\n'
                            % ((total_readbytes - p_total_readbytes) / p_total_readbytes * 100)
                        )
                

                if total_readcalls > p_total_readcalls:
                    if (p_total_readcalls == 0):
                        result_file.write('            The total read calls is increased from 0 to %s calls\n'
                            % (total_readcalls)
                        )
                    else:
                        result_file.write('            The total read calls is increased by %.2f%%\n'
                            % ((total_readcalls - p_total_readcalls) / p_total_readcalls * 100)
                        )
                
                if total_writebytes > p_total_writebytes:
                    if (p_total_writebytes == 0):
                        result_file.write('            The total bytes written is increased from 0 to %s bytes\n'
                            % (total_writebytes)
                        )
                    else:
                        result_file.write('            The total bytes written is increased by %.2f%%\n'
                            % ((total_writebytes - p_total_writebytes) / p_total_writebytes * 100)
                        )
                
                if total_writecalls > p_total_writecalls:
                    if (p_total_writecalls == 0):
                        result_file.write('            The total write calls is increased from 0 to %s calls\n'
                            % (total_writecalls)
                        )
                    else:
                        result_file.write('            The total write calls is increased by %.2f%%\n'
                            % ((total_writecalls - p_total_writecalls) / p_total_writecalls * 100)
                        )

            result_file.write('\n')



        # for p in self.pairs:
        #     diff_c = []
        #     for p_c in p.constraints:
        #         if p.constraints[p_c] != self.configs[p_c]:
        #             diff_c.append(p_c)
        #     if not diff_c:
        #         continue # shouldn't be empty
        #     for c in diff_c:
        #         result_file.write('[%s]' % (c))
        #     result_file.write('\nYour current setting is:\n')
        #     for c in diff_c:
        #         result_file.write('    %s = %s\n' % (c, self.configs[c]))
        #     result_file.write('A better setting could be:\n')
        #     for c in diff_c:
        #         result_file.write('    %s = %s\n' % (c, p.constraints[c]))
        #     result_file.write('Potential performance impacts are:\n')
        #     result_file.write('    When the workload is\n')
        #     p.write_workloads(result_file, 8)
        #     r =  (self.costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
        #     result_file.write('    Your current setting is %s slower than the new setting\n'
        #         % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
        #     )
        #     p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
        #     total_readbytes = self.costs['IO']['read'][0] + self.costs['IO']['pread'][0]
        #     if p_total_readbytes < total_readbytes:
        #         result_file.write('    The total bytes read (read+pread) is reduced by %.2f%%\n' # TODO increased
        #             % ((total_readbytes - p_total_readbytes) / total_readbytes * 100)
        #         )
        #     p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
        #     total_readcalls = self.costs['IO']['read'][1] + self.costs['IO']['pread'][1]
        #     if p_total_readcalls < total_readcalls:
        #         result_file.write('    The total read calls (read+pread) is reduced by %.2f%%\n'
        #             % ((total_readcalls - p_total_readcalls) / total_readcalls * 100)
        #         )
        #     p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
        #     total_writebytes = self.costs['IO']['write'][0] + self.costs['IO']['pwrite'][0]
        #     if p_total_writebytes < total_writebytes:
        #         result_file.write('    The total bytes written (write+pwrite) is reduced by %.2f%%\n'
        #             % ((total_writebytes - p_total_writebytes) / total_writebytes * 100)
        #         )
        #     p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
        #     total_writecalls = self.costs['IO']['write'][1] + self.costs['IO']['pwrite'][1]
        #     if p_total_writecalls < total_writecalls:
        #         result_file.write('    The total write calls (write+pwrite) is reduced by %.2f%%\n'
        #             % ((total_writecalls - p_total_writecalls) / total_writecalls * 100)
        #         )
        #     result_file.write('\n')


    def __get_default_configs(self):
        return {
            'autocommit' : 1,
            'sync_binlog' : 1,
            'binlog_format' : 0,
            'sql_log_bin' : 1,
        }

        # write result --->
        # for p in self.pairs:
        #     diff_c = []
        #     for p_c in p.constraints:
        #         if p.constraints[p_c] != self.configs[p_c]:
        #             diff_c.append(p_c)
        #     if not diff_c:
        #         continue # shouldn't be empty
        #     for c in diff_c:
        #         result_file.write('[%s]' % (c))
        #     result_file.write('\nYour current setting is:\n')
        #     for c in diff_c:
        #         result_file.write('    %s = %s\n' % (c, self.configs[c]))
        #     result_file.write('A better setting could be:\n')
        #     for c in diff_c:
        #         result_file.write('    %s = %s\n' % (c, p.constraints[c]))
        #     result_file.write('Potential performance impacts are:\n')
        #     result_file.write('    When the workload is\n')
        #     p.write_workloads(result_file, 8)
        #     r =  (self.costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
        #     result_file.write('    Your current setting is %s slower than the new setting\n'
        #         % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
        #     )
        #     p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
        #     total_readbytes = self.costs['IO']['read'][0] + self.costs['IO']['pread'][0]
        #     if p_total_readbytes < total_readbytes:
        #         result_file.write('    The total bytes read (read+pread) is reduced by %.2f%%\n' # TODO increased
        #             % ((total_readbytes - p_total_readbytes) / total_readbytes * 100)
        #         )
        #     p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
        #     total_readcalls = self.costs['IO']['read'][1] + self.costs['IO']['pread'][1]
        #     if p_total_readcalls < total_readcalls:
        #         result_file.write('    The total read calls (read+pread) is reduced by %.2f%%\n'
        #             % ((total_readcalls - p_total_readcalls) / total_readcalls * 100)
        #         )
        #     p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
        #     total_writebytes = self.costs['IO']['write'][0] + self.costs['IO']['pwrite'][0]
        #     if p_total_writebytes < total_writebytes:
        #         result_file.write('    The total bytes written (write+pwrite) is reduced by %.2f%%\n'
        #             % ((total_writebytes - p_total_writebytes) / total_writebytes * 100)
        #         )
        #     p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
        #     total_writecalls = self.costs['IO']['write'][1] + self.costs['IO']['pwrite'][1]
        #     if p_total_writecalls < total_writecalls:
        #         result_file.write('    The total write calls (write+pwrite) is reduced by %.2f%%\n'
        #             % ((total_writecalls - p_total_writecalls) / total_writecalls * 100)
        #         )
        #     result_file.write('\n')