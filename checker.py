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
    # print (cnfs)

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
        
        # print(config.util)
        # for c in config.configs:
        #     print (c + " = " + str(config.configs[c]))
        # print ('-'*39)

        if config.util != database:
            continue

        # print ('-'*39)
        if config.check_impact(impact_table):
            print ('HIT cost impact table state %s: %s' % (config.impact_table_id, config.util))
            config.write_result(result_file)
            config.write_worst_workload(result_file, n)
        else:
            result_file.write('[+] VIOLET detected no bad configuration in your file. You are good to go!\n')
            # result_file.write('\n\n')
            # impact_table.make_workload_suggestion(result_file, config) # assume it will only be printed once
        # print ('-'*39)

    result_file.write('\n\n')
    # impact_table.find_worst_workload(result_file, n)

    print ('The result is written to ' + output_file)
    result_file.close()



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='check misconfigurations')
    parser.add_argument('-b', '--database', default='mysqld')
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output', default='result.txt')
    parser.add_argument('-t', '--table', nargs='+', default='impact_table.csv')
    parser.add_argument('-a', '--target', default='') # i.e. 'autocommit, binlog'
    parser.add_argument('-w', '--workload_number', default=0)
    parser.add_argument('-d', '--diff', default=False)
    parser.add_argument('-l', '--workload_option', default='')

    args = parser.parse_args()

    if args.input is None and args.output is None:
        parser.print_help()
        exit()
    
    for i in range(len(args.table)):
        out = args.output.split('.')[0] + '_' + str(i+1) + '.' + args.output.split('.')[1]
        checker(args.input, out, args.table[i], int(args.workload_number), args.diff, args.target, args.database, args.workload_option)