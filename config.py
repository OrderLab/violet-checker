import re
from table import *

class Config:
    def __init__(self, util, cnfs):
        self.util = util.replace('[', '').replace(']', '')
        self.impact_table_hit = []
        self.impact_table_id = -1
        self.costs = {}
        self.configs = self.__get_default_configs()
        self.config_translate_table = self.__get_config_translate_table()
        self.impact_table_rows = {}
        self.impact_table_pairs = {}
        
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                if t[1].isdigit():
                    t[1] = int(t[1])
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
                if t[1].isdigit():
                    t[1] = int(t[1])
                if t[0] in self.config_translate_table:
                    if t[1] in self.config_translate_table[t[0]]:
                        t[1] = self.config_translate_table[t[0]][t[1]]
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
        hit = False
        for _id in impact_table.dict:
            ok = True
            for k in impact_table.dict[_id]['constraints']:
                v = impact_table.dict[_id]['constraints'][k]
                if k in self.configs:
                    if v != self.configs[k]:
                        ok = False
                else:
                    ok = False
            if ok:
                hit = True
                r = impact_table.get_row(_id)
                assert r.workload_option not in self.impact_table_rows, "duplicated workload option"
                self.impact_table_rows[r.workload_option] = r
                self.impact_table_pairs[r.workload_option] = [impact_table.get_row(p) for p in r.pairs]
                self.impact_table_pairs[r.workload_option].sort(key=lambda x: x.costs['ET'], reverse=False)
                self.impact_table_pairs[r.workload_option] = [
                    p for p in self.impact_table_pairs[
                        r.workload_option
                    ] if p.costs['ET'] < self.impact_table_rows[r.workload_option].costs['ET']
                ]
                # TODO for debug use, delete later
                for c in r.constraints:
                    print ('    %s = %s' % (c, r.constraints[c]))
                print ('     => %s, %s' % (r.workload_option, r.costs['ET']))
                for p in self.impact_table_pairs[r.workload_option]:
                    print ('    p')
                    for c in p.constraints:
                        print ('    %s = %s' % (c, p.constraints[c]))
                    print ('    ' + str(p.costs['ET']))
                    # print (p.workload_option)
                print ('-'*20)
                # self.pairs = [impact_table.get_row(p) for p in impact_table_row.pairs]
                # self.pairs.sort(key=lambda x: x.costs['ET'], reverse=False)
                # self.pairs = [p for p in self.pairs if p.costs['ET'] < self.costs['ET']]
                # self.impact_table_id = _id
                # break
        return hit

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
        
        for w in worst_workloads:
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




    # FIXME assume there's only one difference ... could change to write_result(self, result_file, n) ...
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
            result_file.write('VIOLET has detected 0 bad configuration in your current configuration file. You are good to go!\n')
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
                # identical value but under different workloads
                for p in [p for p in diff_w[c] if p.constraints[c] == pp.constraints[c]]:
                    if p.workload_option not in self.impact_table_rows:
                        continue
                    costs = self.impact_table_rows[p.workload_option].costs
                    # result_file.write('\n')
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

                    # result_file.write(
                    #     '%s      %s\n' % (p.costs['ET'], costs['ET'])
                    # )

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
            # result_file.write('the total execution time is %sms\n\n' % (r.costs['ET']))

            top += 1
            n -= 1
            if not n:
                break

    def __get_default_configs(self):
        return {
            'autocommit' : 1,
            'sync_binlog' : 1,
            'binlog_format' : 0,
            'sql_log_bin' : 1,
            'innodb_flush_log_at_trx_commit' : 1,
            'innodb_fast_shutdown' : 1,
            'innodb_force_recovery' : 0,

        }
    
    def __get_config_translate_table(self):
        return {
            'binlog_format' : {'row':0, 'statement':1, 'mixed':2},
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