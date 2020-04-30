import re
import csv

class ImpactTable:
    def __init__(self, filename):
        with open(filename, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file)
            self.fields = next(csv_reader)
            self.rows = []
            self.dict = {}
            for row in csv_reader:
                self.rows.append(row)
                state_id = int(row[0])
                self.dict[state_id] = {'constraints':{}, 'costs':{}}
                constraints = row[1].split('&&')
                costs = row[2].split(';')
                self.constraints_handler(state_id, constraints)
                self.costs_handler(state_id, costs)


    def constraints_handler(self, id, constraints):
        for c in [c.split('==') for c in constraints]:
            self.dict[id]['constraints'][c[0]] = int(c[1])
    
    def costs_handler(self, id, costs):
        for c in [c.split('=>') for c in costs]:
            if c[0] == "IO":
                result = [int(n) for n in c[1].split(' ')]
                self.dict[id]['costs']['IO'] = {
                    'read' : [result[0], result[1]],
                    'write' : [result[2], result[3]],
                    'pread' : [result[4], result[6]],
                    'pwrite' : [result[6], result[7]],
                }
            elif c[0] == "ET":
                self.dict[id]['costs']['ET'] = float(c[1].split('ms')[0])
            elif c[0] == "IC":
                self.dict[id]['costs']['IC'] = int(c[1])
            elif c[0] == "SC":
                self.dict[id]['costs']['SC'] = int(c[1])

            
            '''
             // TODO check if there is a IO tracer.dat
  impact_table_file_ << "IO=>" << record->io_trace.read_bytes << " " << record->io_trace.read_cnt << " "
    << record->io_trace.write_bytes << " " << record->io_trace.write_cnt << " " << record->io_trace.pread_bytes << " "
    << record->io_trace.pread_cnt << " " << record->io_trace.pwrite_bytes << " " << record->io_trace.pwrite_cnt;
            '''