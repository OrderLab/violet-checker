#!/usr/bin/python3
import argparse

from util import *
from config import *

def checker(input_file, output_file, table_file, n, diff):

    result_file = open(output_file, 'w')

    impact_table = ImpactTable(table_file)
    utils, cnfs = read_config_file(input_file)
    impact_table.find_all_pairs(1)

    # diff
    if diff:
        if not re.match(r'\S+\s*=\s*\S+', diff):
            print ('invalid config format')
            return
        for (u, c) in zip(utils, cnfs):
            config = Config(u, c)
            if config.util != 'mysqld':
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
        config = Config(u, c)
        
        # print(config.util)
        # for c in config.configs:
        #     print (c + " = " + str(config.configs[c]))
        # print ('-'*39)

        if config.util != 'mysqld':
            continue

        print ('-'*39)
        if config.check_impact(impact_table):
            print ('HIT cost impact table state %s: %s' % (config.impact_table_id, config.util))
            config.write_result(result_file)
            config.write_worst_workload(result_file, n)
            # result_file.write('\n\n')
            # impact_table.make_workload_suggestion(result_file, config) # assume it will only be printed once
        print ('-'*39)

    result_file.write('\n\n')
    # impact_table.find_worst_workload(result_file, n)

    print ('The result is written to ' + output_file)
    result_file.close()



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='check misconfigurations')
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output', default='result.txt')
    parser.add_argument('-t', '--table', default='impact_table.csv')
    parser.add_argument('-w', '--workload_number', default=0)
    parser.add_argument('-d', '--diff', default=False)


    args = parser.parse_args()

    if args.input is None and args.output is None:
        parser.print_help()
        exit()
    
    checker(args.input, args.output, args.table, int(args.workload_number), args.diff)