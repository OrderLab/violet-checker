#!/usr/bin/python3
import argparse

from util import *
from config import *

def checker(input_file, output_file, table_file):

    impact_table = ImpactTable(table_file)
    utils, cnfs = read_config_file(input_file)
    impact_table.find_all_pairs(1)

    # for d in impact_table.dict:
    #     print (impact_table.dict[d]['constraints'])
    #     print (impact_table.dict[d]['pairs'])

    _l = []

    for (u, c) in zip(utils, cnfs):
        config = Config(u, c)
        # for c in config.cnfs:
            # print (c)
        if config.check_impact(impact_table):
            print ('----------- Impact Table HIT ----------')
            print ('ID in impact table: ' + str(config._id))
            # print (config.costs)
            _l.append(config)
            for pair_id in impact_table.dict[config._id]['pairs']:
                print ('Could compare to STATE ' + str(pair_id))


        print ('-'*39)

    print_result_file(output_file, _l)



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