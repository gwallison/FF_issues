"""This code is used to read the FF_issues_master_X.txt files and produce outputs that are useful for the 
browser system, etc."""

import pandas as pd
import os

issues_files_dir = r"C:\MyDocs\integrated\FF_issues\issues_files"  # adjust to your system

class Process_Master_Files():
    def __init__(self,input_dir=issues_files_dir,out_dir='./',verbose=False):
        self.input_dir = input_dir
        self.out_dir = out_dir
        self.verbose = verbose
        self.legal_fields = {'Title':[],'Flag_id':[],'Date_entered':[],'Description':[],'Notes':[],'Reported_to_FF':[],
                             'Other_notifications':[],'Tags':[],'Warning_level':[]}

    def fetch_all_obj(self):
        flst = os.listdir(self.input_dir)
        allobj = []
        for fn in flst:
            if fn[:17] !='FF_issues_master_':
                if self.verbose:
                    print(f'Name of file <{fn}> does not match expected format.  Ignoring it.')
                continue
            with open(os.path.join(self.input_dir,fn),'r') as f:
                alltext = f.read()
            split_lst = alltext.split('::START:\n')
            #print(split_lst[1:])
            allobj = allobj + split_lst[1:]  # don't include the file's header text
        self.rawobj = allobj

    def process_obj(self):
        self.fetch_all_obj()
        allobj = []
        ok = True
        for obj in self.rawobj:
            ldict = {}
            # clip the end:
            clipped = obj.split('::END')[0]
            # break into fields
            fields = clipped.split('::')[1:] 
            # print(fields)
            for i,field in enumerate(fields):
                field = field.strip()
                tmp = field.split(':',1)
                first = tmp[0]
                try:
                    value = tmp[1].strip()
                except:
                    value = ''
                value = value.replace('\n',' ')
                ldict[first] = value
                # verify that all fields are legally named
                if not first in self.legal_fields.keys():
                    print(f'Illegal field name in {field}')
                    print(f'field num: {i}, value: <{first}>')
                    print('*** Correct before continuing. ***')
                    ok = False
                    break
            # now move them into the buildiing dictionary
            if not ok:
                break
            try:
                # don't keep items without an id , such as templates
                if ldict['Flag_id'] != '':
                    for fname in self.legal_fields.keys():
                        try:
                            self.legal_fields[fname].append(ldict[fname])
                        except: #this field isn't in the object
                            self.legal_fields[fname].append('')
            except:
                pass    
        return pd.DataFrame(self.legal_fields)            

 
if __name__ == '__main__':
    pmf = Process_Master_Files()
    df = pmf.process_obj()
    print(df.info())
    # print(pmf.legal_fields)