#!/usr/bin/python3
import argparse

from util import *
from config import *

def checker(input_file, output_file, table_file):

    impact_table = ImpactTable(table_file)
    utils, cnfs = read_config_file(input_file)
    impact_table.find_all_pairs(1)


    result_file = open(output_file, 'w')

    # for d in impact_table.dict:
    #     print (impact_table.dict[d]['constraints'])
    #     print (impact_table.dict[d]['pairs'])

    _l = []

    for (u, c) in zip(utils, cnfs):
        config = Config(u, c)
        if config.util != 'mysqld':
            continue

        for c in config.configs:
            print (c + " = " + str(config.configs[c]))
        print ('#'*39)
        if config.check_impact(impact_table):
            print ('Cost impact table HIT %s: %s' % (config.impact_table_id, config.util))
            config.write_result(result_file)

        print ('-'*39)


    print ('The result is written to ' + output_file)
    result_file.close()



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='check misconfigurations')
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output', default='result.txt')
    parser.add_argument('-t', '--table', default='impact_table.csv')

    args = parser.parse_args()

    if args.input is None and args.output is None:
        parser.print_help()
        exit()
    
    checker(args.input, args.output, args.table)