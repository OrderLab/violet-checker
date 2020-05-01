import re
from table import *

class Config:
    def __init__(self, util, cnfs):
        self.util = util.replace('[', '').replace(']', '')
        self.cnfs = []
        self.impact_table_hit = []
        self.costs = {}
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                if t[1].isdigit():
                    t[1] = int(t[1])
                # else:
                #     t_list = [ord(c) for c in list(t[1])]
                #     valueAsInt = 0
                #     for i in range(len(t_list)):
                #         valueAsInt |= t_list[i] << (i*8)
                #     t[1] = valueAsInt
                self.cnfs.append([t[0],t[1]])
            else:
                self.cnfs.append([c,1])


    def add_cnfs(self, cnfs):
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                self.cnfs.append([t[0],t[1]])
            else:
                self.cnfs.append([c,])

    def find(self, cnfname):
        # print (self.cnfs)
        for c in self.cnfs:
            if c[0] == cnfname:
                return c
        return []

    def check_impact(self, impact_table):
        hit = True
        for _id in impact_table.dict:
            self._id = _id
            for c in self.cnfs:
                name = c[0]
                # TODO when there is no value
                value = c[1]
                hit = True
                if name in impact_table.dict[_id]['constraints']:
                    if value != impact_table.dict[_id]['constraints'][name]:
                        hit = False
                else:
                    hit = False
            if hit:
                self.costs = impact_table.dict[_id]['costs']
                break

        return hit
