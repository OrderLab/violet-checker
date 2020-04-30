#!/usr/bin/python3
import argparse

from util import *
from config import *

def checker(input_file, output_file, table_file):

    impact_table = ImpactTable(table_file)
    utils, cnfs = read_config_file(input_file)


    # for d in impact_table.dict:
    #     print (impact_table.dict[d])

    for (u, c) in zip(utils, cnfs):
        # print (u, c)
        a = Config(u, c)
        # print (a.util)
        for c in a.cnfs:
            print (c)
        # if a.check(impact_table):
        #     print ('>>>>>>>YES')
        if a.check_impact(impact_table):
            print ('impact table hit:')
            print (a.state_id)
            print (a.costs)
            
        print ('-'*50)



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