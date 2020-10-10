import re
from table import *

class Config:
    def __init__(self, util, cnfs, database, workload_option):
        self.workload_option = workload_option
        self.util = util.replace('[', '').replace(']', '')
        self.impact_table_hit = []
        self.impact_table_id = -1
        self.costs = {}
        # self.configs = self.__get_default_configs()
        if database == 'mysqld':
            self.configs = self.__get_mysql_default_configs()
            self.config_translate_table = self.__get_mysql_config_translate_table()
        elif database == 'postgresql':
            self.configs = self.__get_postgresql_default_configs()
            self.config_translate_table = self.__get_postgresql_config_translate_table()
        else:
            self.configs = {}
            self.config_translate_table = {}
        
        self.impact_table_rows = {}
        self.impact_table_pairs = {}
        
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                try:
                    t[1] = int(t[1])
                except:
                    try:
                        t[1] = float(t[1])
                    except:
                        if len(t[1]) > 1 and [c for c in t[1]][0] == '\'' and [c for c in t[1]][-1] == '\'':
                            t[1] = ''.join([c for c in t[1]][1:-1])
                if t[0] in self.config_translate_table:
                    if t[1] in self.config_translate_table[t[0]]:
                        t[1] = self.config_translate_table[t[0]][t[1]]
                self.configs[t[0]] = t[1]
            else:
                self.configs[c] = 1

    def add_configs(self, cnfs):
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                try:
                    t[1] = int(t[1])
                except:
                    try:
                        t[1] = float(t[1])
                    except:
                        pass
                if t[0] in self.config_translate_table:
                    if t[1] in self.config_translate_table[t[0]]:
                        t[1] = self.config_translate_table[t[0]][t[1]]
                self.configs[t[0]] = t[1]
            else:
                self.configs[c] = 1

    def find(self, cnfname):
        for c in self.configs:
            if c == cnfname:
                return self.configs[c]
        return []

    def check_impact(self, impact_table):
        self.workload_options = impact_table.workload_options()
        hit = False
        for _id in impact_table.dict:
            # first check if there is a hit in the impact table
            ok = True
            for k in impact_table.dict[_id]['constraints']:
                v = impact_table.dict[_id]['constraints'][k]
                if k in self.configs:
                    if v != self.configs[k]:
                        ok = False
                else:
                    ok = False
            # if there is a hit, extract all related infomation
            if ok:
                hit = True
                r = impact_table.get_row(_id)
                # assert r.workload_option not in self.impact_table_rows, "duplicated workload option"
                # use the best case
                if r.workload_option in self.impact_table_rows:
                    if r.costs['ET'] > self.impact_table_rows[r.workload_option].costs['ET']:
                        continue
                self.impact_table_rows[r.workload_option] = r
                pl = [impact_table.get_row(p) for p in r.pairs]
                remove = []
                # pick the best pair if there are pairs with similar constraints
                for p1 in pl:
                    # p1_remove = False
                    for p2 in pl:
                        if p1 == p2:
                            continue
                        same = True
                        if len(p1.constraints) > len(p2.constraints):
                            for c in p1.constraints:
                                if c not in p2.constraints:
                                    same = False
                                    break
                                if p1.constraints[c] != p2.constraints[c]:
                                    same = False
                                    break
                        else:
                            for c in p2.constraints:
                                if c not in p1.constraints:
                                    same = False
                                    break
                                if p1.constraints[c] != p2.constraints[c]:
                                    same = False
                                    break
                        if same:
                            if p1.costs['ET'] > p2.costs['ET']:
                                remove.append(p1)
                            else:
                                remove.append(p2)
                for p in remove:
                    if p in pl:
                        pl.remove(p)
                self.impact_table_pairs[r.workload_option] = pl
                self.impact_table_pairs[r.workload_option].sort(key=lambda x: x.costs['ET'], reverse=False)
                self.impact_table_pairs[r.workload_option] = [
                    p for p in self.impact_table_pairs[
                        r.workload_option
                    ] if p.costs['ET'] < self.impact_table_rows[r.workload_option].costs['ET']
                ]
        return hit

    '''
    This function write overall results to the result file under diff. It only supports when there's only one difference
    between current configurations and the configurations in each impact table row. To support more than one
    differences, could modifify this function by adding another parameter N indicating the # of differences.
    '''
    def write_result_diff(self, result_file, config_diff, config_diff_name):
        worst_workloads = []
        for w in self.impact_table_rows:
            if w not in config_diff.impact_table_rows:
                continue
            if self.impact_table_rows[w].costs['ET'] > config_diff.impact_table_rows[w].costs['ET']:
                worst_workloads.append(w)

        if not worst_workloads:
            result_file.write('[+] VIOLET has detected your current configuration is relative good\n')
            return
        
        result_file.write('[+] VIOLET has detected your current configuration is relative bad\n\n')
        result_file.write('[%s]\n' % (config_diff_name))
        result_file.write('Your current setting is:\n')
        result_file.write('    %s = %s\n' % (config_diff_name, self.configs[config_diff_name]))
        result_file.write('A better setting is:\n')
        result_file.write('    %s = %s\n' % (config_diff_name, config_diff.configs[config_diff_name]))

        result_file.write('    >> Under the current workload:\n')
        if self.workload_option in worst_workloads:
            costs = self.impact_table_rows[w].costs
            p = config_diff.impact_table_rows[w]
            p.write_workloads(result_file, 8)
            result_file.write(
                '        $sysbench --mysql-socket=' + self.configs['socket'] + 
                ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
            )
            result_file.write('    Potential performance impacts are:\n')
            r =  (costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
            result_file.write('        Your current setting is %s slower than the new setting\n'
                % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
            )
            if 'IO' in p.costs:
                p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
                total_readbytes = costs['IO']['read'][0] + costs['IO']['pread'][0]
                p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
                total_readcalls = costs['IO']['read'][1] + costs['IO']['pread'][1]
                p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
                total_writebytes = costs['IO']['write'][0] + costs['IO']['pwrite'][0]
                p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
                total_writecalls = costs['IO']['write'][1] + costs['IO']['pwrite'][1]

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
        else:
            result_file.write(' '*8 + 'Your current configuration is relative good\n')
        
        for w in worst_workloads:
            if (w == self.workload_option):
                continue
            costs = self.impact_table_rows[w].costs
            p = config_diff.impact_table_rows[w]
            result_file.write('    >> Under the workload:\n')
            p.write_workloads(result_file, 8)
            result_file.write(
                '        $sysbench --mysql-socket=' + self.configs['socket'] + 
                ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
            )
            result_file.write('    Potential performance impacts are:\n')
            r =  (costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
            result_file.write('        Your current setting is %s slower than the new setting\n'
                % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
            )
            if 'IO' in p.costs:
                p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
                total_readbytes = costs['IO']['read'][0] + costs['IO']['pread'][0]
                p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
                total_readcalls = costs['IO']['read'][1] + costs['IO']['pread'][1]
                p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
                total_writebytes = costs['IO']['write'][0] + costs['IO']['pwrite'][0]
                p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
                total_writecalls = costs['IO']['write'][1] + costs['IO']['pwrite'][1]

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


    '''
    This function write overall results to the result file. It only supports when there's only one difference
    between current configurations and the configurations in each impact table row. To support more than one
    differences, could modifify this function by adding another parameter N indicating the # of differences.
    '''
    def write_result(self, result_file):

        diff, diff_w = {}, {} # diff_w contains same constraints under different workloads

        for c in self.configs:
            for w in self.impact_table_pairs:
                # print ([p.constraints for p in self.impact_table_pairs[w]])
                for p in self.impact_table_pairs[w]:
                    if c not in p.constraints:
                        continue
                    if self.configs[c] != p.constraints[c]:
                        if c not in diff:
                            diff[c], diff_w[c] = [p,], [p,]
                        else:
                            diff_w[c].append(p)
                            if p.constraints[c] not in [pp.constraints[c] for pp in diff[c]]:
                                diff[c].append(p)


        result_file.write('[+] VIOLET Result\n')

        if not len(diff):
            result_file.write('VIOLET has detected 0 bad configuration in your current configuration file. You are good to go!\n\n')
            return

        result_file.write(
            'VIOLET has detected %s potential bad configuration%s in your current configuration file, ' % (
                len(diff), ['s',''][len(diff)==1]
            )
        )
        result_file.write('and they are ')
        ok = False
        for c in diff:
            if ok:
                result_file.write(', ')
            else:
                ok = True
            result_file.write(c)
            
        dw = []
        for c in diff_w:
            for p in diff_w[c]:
                if p.workload_option not in dw:
                    dw.append(p.workload_option)
        result_file.write('. Under %s different workloads, you have better choices to make. \n' % (len(dw)))

        for c in diff:
            result_file.write('For %s, ' % (c))
            fw = True
            for w in dw:
                f,t = True, False
                for p in diff_w[c]:
                    if p.workload_option != w:
                        continue
                    if f:
                        result_file.write(
                            '%shen your workload is *%s*, you can get a better performance by setting its value to %s' % 
                            (['W','w'][fw],w.replace('_', ' '), p.constraints[c])
                        )
                        f, fw = False, False
                        continue
                    t = True
                    result_file.write('/%s' % (p.constraints[c]))
                if t:
                    result_file.write('. ')
            result_file.write('\n')
                    
        result_file.write('\nDetails are shown below.\n\n')

        for c in diff:
            result_file.write('[%s]\n' % (c))
            result_file.write('Your current setting is:\n')
            result_file.write('    %s = %s\n' % (c, self.configs[c]))
            result_file.write('There %s %s better setting%s:\n' % (['are','is'][len(diff[c])==1],len(diff[c]),['s',''][len(diff[c])==1]))
            for p in diff[c]:
                result_file.write('%s' % ([
                            ', %s'%([p.constraints[c],str(p.constraints[c])+'\n'][p is diff[c][len(diff[c])-1]]),
                            '    %s = %s'%(c, [p.constraints[c],str(p.constraints[c])+'\n'][p is diff[c][len(diff[c])-1]])
                        ][p is diff[c][0]]))

            for pp in diff[c]:
                result_file.write('> Compare to %s = %s:\n' % (c, pp.constraints[c]))
                # under the current workload
                if self.workload_option in [p.workload_option for p in diff_w[c] if p.constraints[c] == pp.constraints[c]]:
                    p = [p for p in diff_w[c] if p.constraints[c] == pp.constraints[c] and p.workload_option == self.workload_option][0]
                    costs = self.impact_table_rows[p.workload_option].costs
                    # result_file.write('\n')
                    result_file.write('    >> Under your current workload:\n')
                    p.write_workloads(result_file, 8)
                    if 'socket' in self.configs:
                        result_file.write(
                            '        $sysbench --mysql-socket=' + self.configs['socket'] + 
                            ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                            ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
                        )
                    else:
                        result_file.write(
                            '        $sysbench --mysql-socket=' + 
                            ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                            ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
                        )
                    result_file.write('    Potential performance impacts are:\n')
                    r =  (costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
                    result_file.write('        Your current setting is %s slower than the new setting\n'
                        % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
                    )
                    if 'IO' in p.costs:
                        p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
                        total_readbytes = costs['IO']['read'][0] + costs['IO']['pread'][0]
                        p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
                        total_readcalls = costs['IO']['read'][1] + costs['IO']['pread'][1]
                        p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
                        total_writebytes = costs['IO']['write'][0] + costs['IO']['pwrite'][0]
                        p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
                        total_writecalls = costs['IO']['write'][1] + costs['IO']['pwrite'][1]

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
                else:
                    if self.workload_option in self.workload_options:
                        result_file.write('    >> Under your current workload:\n')
                        result_file.write('        Your current configuration is relative good\n')

                # identical value but under different workloads
                for p in [p for p in diff_w[c] if p.constraints[c] == pp.constraints[c]]:
                    if p.workload_option not in self.impact_table_rows:
                        continue
                    if p.workload_option == self.workload_option:
                        continue
                    costs = self.impact_table_rows[p.workload_option].costs
                    # result_file.write('\n')
                    result_file.write('    >> Under the workload:\n')
                    p.write_workloads(result_file, 8)
                    if 'socket' in self.configs:
                        result_file.write(
                            '        $sysbench --mysql-socket=' + self.configs['socket'] + 
                            ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                            ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
                        )
                    else:
                        result_file.write(
                            '        $sysbench --mysql-socket=' + 
                            ' --mysql-db=test --table-size= 100000 --threads=1 --time=120 --events=0' + 
                            ' --report-interval=10 ' + p.get_workload_file_name() + ' prepare\n'
                        )
                    result_file.write('    Potential performance impacts are:\n')
                    r =  (costs['ET'] - p.costs['ET']) / p.costs['ET'] * 100
                    result_file.write('        Your current setting is %s slower than the new setting\n'
                        % (['%.2f%%'%(r), 'almost infinitely'][r == float('inf')])
                    )
                    if 'IO' in p.costs:
                        p_total_readbytes = p.costs['IO']['read'][0] + p.costs['IO']['pread'][0]
                        total_readbytes = costs['IO']['read'][0] + costs['IO']['pread'][0]
                        p_total_readcalls = p.costs['IO']['read'][1] + p.costs['IO']['pread'][1]
                        total_readcalls = costs['IO']['read'][1] + costs['IO']['pread'][1]
                        p_total_writebytes = p.costs['IO']['write'][0] + p.costs['IO']['pwrite'][0]
                        total_writebytes = costs['IO']['write'][0] + costs['IO']['pwrite'][0]
                        p_total_writecalls = p.costs['IO']['write'][1] + p.costs['IO']['pwrite'][1]
                        total_writecalls = costs['IO']['write'][1] + costs['IO']['pwrite'][1]

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

    def write_worst_workload(self, result_file, n):
        assert n >= 0, "n must be larger than zero"
        if n == 0:
            return

        rows = [self.impact_table_rows[w] for w in self.impact_table_rows]
        rows.sort(key=lambda x: x.costs['ET'], reverse=True)

        if n > len(rows):
            n = len(rows)
        result_file.write('[+] Based on VIOLET’s analysis, the top %s worst workload%s %s:\n\n'
            % (n, ['s', ''][n == 1], ['are', 'is'][n == 1])
        )

        top = 1
        for r in rows:
            result_file.write('#%s\n' % (top))
            result_file.write('When the workload is:\n')
            r.write_workloads(result_file, 4)
            result_file.write('And the configuration is:\n')
            r.write_constraints(result_file)
            r.write_costs(result_file)
            r.write_IO_results(result_file)
            result_file.write('\n')

            top += 1
            n -= 1
            if not n:
                break

    '''
    This function returns MySQL system variables with their default value
    '''
    def __get_mysql_default_configs(self):
        return {
            'autocommit' : 1,
            'sync_binlog' : 1,
            'binlog_format' : 0,
            'sql_log_bin' : 1,
            'innodb_flush_log_at_trx_commit' : 1,
            'innodb_fast_shutdown' : 1,
            'innodb_force_recovery' : 0,
            'query_cache_type' : 0,
            'query_cache_size' : 1048576,

            ### default value generated from MySQL 5.5.59 source code
            # 'performance_schema' : 0,
            # 'performance_schema_events_waits_history_long_size' : 10000,
            # 'performance_schema_events_waits_history_size' : 10,
            # 'performance_schema_max_cond_classes' : 80,
            # 'performance_schema_max_cond_instances' : 1000,
            # 'performance_schema_max_file_classes' : 50,
            # 'performance_schema_max_file_handles' : 32768,
            # 'performance_schema_max_file_instances' : 10000,
            # 'performance_schema_max_mutex_classes' : 200,
            # 'performance_schema_max_mutex_instances' : 1000000,
            # 'performance_schema_max_rwlock_classes' : 30,
            # 'performance_schema_max_rwlock_instances' : 1000000,
            # 'performance_schema_max_table_handles' : 100000,
            # 'performance_schema_max_table_instances' : 50000,
            # 'performance_schema_max_thread_classes' : 50,
            # 'performance_schema_max_thread_instances' : 1000,
            # 'auto_increment_increment' : 1,
            # 'auto_increment_offset' : 1,
            # 'automatic_sp_privileges' : 1,
            # 'back_log' : 50,
            # 'basedir' : None,
            # 'binlog_cache_size' : 32768,
            # 'binlog_stmt_cache_size' : 32768,
            # 'binlog_format' : 1,
            # 'binlog_direct_non_transactional_updates' : 0,
            # 'bulk_insert_buffer_size' : 8388608,
            # 'character_sets_dir' : None,
            # 'completion_type' : 0,
            # 'concurrent_insert' : 1,
            # 'connect_timeout' : 10,
            # 'datadir' : None,
            # 'debug' : 12899968,
            # 'delay_key_write' : 1,
            # 'delayed_insert_limit' : 100,
            # 'delayed_insert_timeout' : 300,
            # 'delayed_queue_size' : 1000,
            # 'event_scheduler' : 0,
            # 'expire_logs_days' : 0,
            # 'flush' : 0,
            # 'flush_time' : 0,
            # 'ft_max_word_len' : 84,
            # 'ft_min_word_len' : 4,
            # 'ft_query_expansion_limit' : 20,
            # 'ft_stopword_file' : None,
            # 'ignore_builtin_innodb' : 0,
            # 'init_connect' : 12899968,
            # 'init_file' : None,
            # 'init_slave' : 12899968,
            # 'interactive_timeout' : 28800,
            # 'join_buffer_size' : 131072,
            # 'key_buffer_size' : 8388608,
            # 'key_cache_block_size' : 1024,
            # 'key_cache_division_limit' : 100,
            # 'key_cache_age_threshold' : 300,
            # 'large_files_support' : 1,
            # 'large_page_size' : 0,
            # 'large_pages' : 0,
            # 'lc_messages_dir' : None,
            # 'local_infile' : 1,
            # 'lock_wait_timeout' : 31536000,
            # 'locked_in_memory' : 0,
            # 'log_bin' : 0,
            # 'log_bin_trust_function_creators' : 0,
            # 'log_error' : 0,
            # 'log_queries_not_using_indexes' : 0,
            # 'log_warnings' : 1,
            # 'long_query_time' : 10.000000,
            # 'low_priority_updates' : 0,
            # 'sql_low_priority_updates' : 0,
            # 'lower_case_file_system' : 0,
            # 'lower_case_table_names' : 0,
            # 'max_allowed_packet' : 1048576,
            # 'slave_max_allowed_packet' : 1073741824,
            # 'max_binlog_cache_size' : -4096,
            # 'max_binlog_stmt_cache_size' : -4096,
            # 'max_binlog_size' : 1073741824,
            # 'max_connections' : 151,
            # 'max_connect_errors' : 10,
            # 'max_insert_delayed_threads' : 20,
            # 'max_delayed_threads' : 20,
            # 'max_error_count' : 64,
            # 'max_heap_table_size' : 16777216,
            # 'metadata_locks_cache_size' : 1024,
            # 'pseudo_thread_id' : 0,
            # 'max_join_size' : -1,
            # 'max_seeks_for_key' : -1,
            # 'max_length_for_sort_data' : 1024,
            # 'sql_max_join_size' : -1,
            # 'max_long_data_size' : 1048576,
            # 'max_prepared_stmt_count' : 16382,
            # 'max_relay_log_size' : 0,
            # 'max_sort_length' : 1024,
            # 'max_sp_recursion_depth' : 0,
            # 'max_user_connections' : 0,
            # 'max_tmp_tables' : 32,
            # 'max_write_lock_count' : -1,
            # 'min_examined_row_limit' : 0,
            # 'net_buffer_length' : 16384,
            # 'net_read_timeout' : 30,
            # 'net_write_timeout' : 60,
            # 'net_retry_count' : 10,
            # 'new' : 0,
            # 'old' : 0,
            # 'old_alter_table' : 0,
            # 'old_passwords' : 0,
            # 'open_files_limit' : 0,
            # 'optimizer_prune_level' : 1,
            # 'optimizer_search_depth' : 62,
            # 'optimizer_switch' : 31,
            # 'pid_file' : None,
            # 'plugin_dir' : None,
            # 'port' : 0,
            # 'preload_buffer_size' : 32768,
            # 'protocol_version' : 10,
            # 'read_buffer_size' : 131072,
            # 'read_only' : 0,
            # 'read_rnd_buffer_size' : 262144,
            # 'div_precision_increment' : 4,
            # 'rpl_recovery_rank' : 0,
            # 'range_alloc_block_size' : 4096,
            # 'multi_range_count' : 256,
            # 'query_alloc_block_size' : 8192,
            # 'query_prealloc_size' : 8192,
            # 'skip_external_locking' : 1,
            # 'skip_networking' : 0,
            # 'skip_name_resolve' : 0,
            # 'skip_show_database' : 0,
            # 'socket' : None,
            # 'thread_concurrency' : 10,
            # 'thread_stack' : 262144,
            # 'tmpdir' : None,
            # 'transaction_alloc_block_size' : 8192,
            # 'transaction_prealloc_size' : 4096,
            # 'thread_handling' : 0,
            # 'query_cache_size' : 0,
            # 'query_cache_limit' : 1048576,
            # 'query_cache_min_res_unit' : 4096,
            # 'query_cache_type' : 1,
            # 'query_cache_wlock_invalidate' : 0,
            # 'secure_auth' : 0,
            # 'secure_file_priv' : NULL,
            # 'server_id' : 0,
            # 'slave_compressed_protocol' : 0,
            # 'slave_exec_mode' : 0,
            # 'slave_type_conversions' : 0,
            # 'slow_launch_time' : 2,
            # 'sort_buffer_size' : 2097152,
            # 'sql_mode' : 0,
            # 'ssl_ca' : None,
            # 'ssl_capath' : None,
            # 'ssl_cert' : None,
            # 'ssl_cipher' : None,
            # 'ssl_key' : None,
            # 'updatable_views_with_limit' : 1,
            # 'sync_frm' : 1,
            # 'table_definition_cache' : 400,
            # 'table_open_cache' : 400,
            # 'thread_cache_size' : 0,
            # 'tx_isolation' : 2,
            # 'tmp_table_size' : 16777216,
            # 'timed_mutexes' : 0,
            # 'version_comment' : 'Source distribution',
            # 'version_compile_machine' : 'x86_64',
            # 'version_compile_os' : 'Linux',
            # 'wait_timeout' : 28800,
            # 'engine_condition_pushdown' : 1,
            # 'debug_sync' : 0,
            # 'autocommit' : 1,
            # 'big_tables' : 0,
            # 'sql_big_tables' : 0,
            # 'sql_big_selects' : 0,
            # 'sql_log_off' : 0,
            # 'sql_log_bin' : 1,
            # 'sql_warnings' : 0,
            # 'sql_notes' : 1,
            # 'sql_auto_is_null' : 0,
            # 'sql_safe_updates' : 0,
            # 'sql_buffer_result' : 0,
            # 'sql_quote_show_create' : 1,
            # 'foreign_key_checks' : 1,
            # 'unique_checks' : 1,
            # 'profiling' : 0,
            # 'profiling_history_size' : 15,
            # 'sql_select_limit' : -1,
            # 'timestamp' : 0,
            # 'last_insert_id' : 0,
            # 'identity' : 0,
            # 'insert_id' : 0,
            # 'rand_seed1' : 0,
            # 'rand_seed2' : 0,
            # 'error_count' : 0,
            # 'warning_count' : 0,
            # 'default_week_format' : 0,
            # 'group_concat_max_len' : 1024,
            # 'report_host' : None,
            # 'report_user' : None,
            # 'report_password' : None,
            # 'report_port' : 0,
            # 'keep_files_on_create' : 0,
            # 'license' : 'GPL',
            # 'general_log_file' : None,
            # 'slow_query_log_file' : None,
            # 'general_log' : 0,
            # 'log' : 0,
            # 'slow_query_log' : 0,
            # 'log_slow_queries' : 0,
            # 'log_output' : 2,
            # 'log_slave_updates' : 0,
            # 'relay_log' : None,
            # 'relay_log_index' : None,
            # 'relay_log_info_file' : None,
            # 'relay_log_purge' : 1,
            # 'relay_log_recovery' : 0,
            # 'slave_load_tmpdir' : None,
            # 'slave_net_timeout' : 3600,
            # 'sql_slave_skip_counter' : 0,
            # 'slave_skip_errors' : None,
            # 'relay_log_space_limit' : 0,
            # 'sync_relay_log' : 0,
            # 'sync_relay_log_info' : 0,
            # 'sync_binlog' : 0,
            # 'sync_master_info' : 0,
            # 'slave_transaction_retries' : 10,
            # 'stored_program_cache' : 256,
            # 'pseudo_slave_mode' : 0,
        }
    
    '''
    This function returns PostgreSQL system variables with their default value
    '''
    def __get_postgresql_default_configs(self):
        return {
            'log_statement' : 0,
            'random_page_cost' : 4,
            'wal_sync_method' : 1,
            'wal_level' : 1,
            'password_encryption' : 1,
            'synchronous_commit' : 1,
        }
    
    def __get_mysql_config_translate_table(self):
        return {
            'binlog_format' : {'row':0, 'statement':1, 'mixed':2},
        }
    
    def __get_postgresql_config_translate_table(self):
        return {
            'log_statement' : {'none':0, 'ddl':1, 'mod':2, 'all':3},
            'synchronous_commit' : {'on':1, 'off':0},
        }


        '''
        
        a = [

            

        ]

        '''