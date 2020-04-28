#!/usr/bin/python3
from util import *
from config import *

def main():

    impact_table = read_impact_table('config_impact_table.csv')
    utils, cnfs = read_config_file('my.cnf')

    for (u, c) in zip(utils, cnfs):
        # print (u, c)
        a = Config(u, c)
        print (a.util)
        for c in a.cnfs:
            print (c)
        # if a.check(impact_table):
        #     print ('>>>>>>>YES')
        if a.check_impact(impact_table):
            print ('impact table hit:')
            for i in a.impact_table_hit:
                print (i)
            
        print ('-'*50)



if __name__ == "__main__":
    main()