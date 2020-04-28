import re

class Config:
    def __init__(self, util, cnfs):
        self.util = util.replace('[', '').replace(']', '')
        self.cnfs = []
        self.impact_table_hit = []
        for c in cnfs:
            if re.match(r'\S+\s*=\s*\S+', c):
                t = ''.join(c.split()).split('=')
                if t[1].isdigit():
                    t[1] = int(t[1])
                else:
                    t_list = [ord(c) for c in list(t[1])]
                    valueAsInt = 0
                    for i in range(len(t_list)):
                        valueAsInt |= t_list[i] << (i*8)
                    t[1] = valueAsInt
                self.cnfs.append([t[0],t[1]])
            else:
                self.cnfs.append([c,])


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
    
    # def check(self, impact_table):
    #     # true => violation
    #     for r in impact_table:
    #         rr = r
    #         constraints = [c.split() for c in rr[0].split('&&')]
    #         ok = False
    #         for c in constraints:
    #             cnf = self.find(c[0])
    #             # print (c); print (cnf)
    #             if not cnf:
    #                 break
    #             # print (cnf); print (c)
    #             # print ('#'*15)
    #             if c[1] == '==' and c[2] != cnf[1]:
    #                 print (rr)
    #                 ok = True; break
    #             elif c[1] == '!=' and c[2] == cnf[1]:
    #                 print (rr)
    #                 ok = True; break
    #         if ok: 
    #              return True
    #     return False

    def check_impact(self, impact_table):

        table_hit = False
        for row in impact_table:
            constraints = [r.split() for r in row[0].split('&&')]
            row_hit = True 
            for c in constraints:
                cnf = self.find(c[0])
                if not cnf:
                    row_hit = False
                    break
                if c[1] == '==' and c[2] == cnf[1]:
                    pass
                elif c[1] == '!=' and c[2] != cnf[1]:
                    pass
                else:
                    row_hit = False
                    break
            if row_hit:
                self.impact_table_hit.append(row)
                table_hit = True
                    
        return table_hit
