#!/usr/bin/python3
import argparse

from util import *
from config import *

def checker(input_file, output_file, table_file, n, diff, target, database, workload_option):
    result_file = open(output_file, 'w')
    impact_table = ImpactTable(table_file)
    impact_table.find_all_pairs(1, target)

    if database == 'mysqld':
        utils, cnfs = read_mysql_config_file(input_file)
    elif database == 'postgresql':
        cnfs = read_postgresql_config_file(input_file)
        utils = ['[postgresql]']

    # diff
    if diff:
        if not re.match(r'\S+\s*=\s*\S+', diff):
            print ('invalid config format')
            return
        for (u, c) in zip(utils, cnfs):
            config = Config(u, c, database, workload_option)
            if config.util != database:
                continue
            config_diff = Config(u, c)
            config_diff.util += '_diff'
            config_diff.add_configs([diff,])
            if config.check_impact(impact_table) and config_diff.check_impact(impact_table):
                config.write_result_diff(result_file, config_diff, ''.join(diff.split()).split('=')[0])
        print ('The result is written to ' + output_file)
        result_file.close()
        return

    # non diff 
    for (u, c) in zip(utils, cnfs):
        config = Config(u, c, database, workload_option)
        if config.util != database:
            continue
        if config.check_impact(impact_table):
            print ('HIT cost impact table state %s: %s' % (config.impact_table_id, config.util))
            config.write_result(result_file)
            config.write_worst_workload(result_file, n)
        else:
            result_file.write('[+] VIOLET detected no bad configuration in your file. You are good to go!\n')
    result_file.write('\n\n')
    print ('The result is written to ' + output_file)
    result_file.close()



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='check misconfigurations')
    parser.add_argument('-b', '--database', default='mysqld')                   # database type
    parser.add_argument('-i', '--input')                                        # input file name
    parser.add_argument('-o', '--output', default='result.txt')                 # output file name
    parser.add_argument('-t', '--table', nargs='+', default='impact_table.csv') # impact table file name
    parser.add_argument('-a', '--target', default='')                           # target system variable i.e. 'autocommit'
    parser.add_argument('-d', '--diff', default=False)                          # diff system variable w/ another value i.e. 'autocommit = 0'
    parser.add_argument('-w', '--workload_number', default=0)                   # top # workloads under current config shown in output file
    parser.add_argument('-l', '--workload_option', default='')                  # under what workload

    args = parser.parse_args()

    if args.input is None and args.output is None:
        parser.print_help()
        exit()
    
    if len(args.table) == 1:
        checker(args.input, args.output, args.table[0], int(args.workload_number), args.diff, args.target, args.database, args.workload_option)
    else:
        for i in range(len(args.table)):
            out = args.output.split('.')[0] + '_' + args.table[i].split('.')[0] + '.' + args.output.split('.')[1]
            checker(args.input, out, args.table[i], int(args.workload_number), args.diff, args.target, args.database, args.workload_option)