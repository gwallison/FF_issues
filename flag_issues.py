"""This code is used to detect specific issues in the Open-FF generated "full_df.parquet" file.  For each issue,
a fuction is written to produce a flag when certain conditions are met. Those flags are then used to create
a database that lists all the disclosures/records that are involved.  This database is specific to a particular
full_df file and therefore a specific bulk data download and its date.  Because of the fluid nature of FracFocus
entries (and the fact that they can be modified without public notice), specific instances of issues may be corrected
after these flags were created."""

import pandas as pd
import numpy as np
import os

class Disclosure_Issues():
    def __init__(self,df):
        self.df = df
        self.gb = df.groupby('DisclosureId',as_index=False)[['APINumber','TotalBaseWaterVolume','has_TBWV',
                                                             'is_duplicate','MI_inconsistent','ws_perc_total',
                                                             'no_chem_recs']].first()

    # ALL Issues must be named "dIssues_x"  where x is usually a consecutive number.
    # x will become the flag's name as in "d_x"
        
    def get_disc_set(self,cond):
        disc_set = self.gb[cond].DisclosureId.tolist()
        return disc_set

    def dIssue_001(self):
        '''TotalBaseWaterVolume is missing or zero. Mass calculations are not possible.'''
        cond = self.gb.has_TBWV==False
        return self.get_disc_set(cond)

    def dIssue_002(self):
        """ this disclosure has a duplicate in FracFocus; that is, has the same APINumber and JobEndDate."""
        cond = self.gb.is_duplicate
        return self.get_disc_set(cond)

    def dIssue_003(self):
        """ The MassIngredient data do not pass the internal consistency test, so are is used when reporting mass."""
        cond = self.gb.MI_inconsistent
        return self.get_disc_set(cond)

    def dIssue_004(self):
        """ The reported water source percentages do not sum to 100%"""
        cond = (self.gb.ws_perc_total.notna()) & ~(self.gb.ws_perc_total==100)
        return self.get_disc_set(cond)

    def dIssue_005(self):
        """ Early FracFocus disclosures have no chemical records"""
        cond = self.gb.no_chem_recs
        return self.get_disc_set(cond)

    def dIssue_006(self):
        """ Disclosure records only a single chemical record"""
        c = self.df.ingKeyPresent
        gb = self.df[c].groupby('DisclosureId',as_index=False).size()
        return gb[gb['size']==1].DisclosureId.tolist()

        return self.get_disc_set(cond)

class Record_Issues():
    def __init__(self,df,cas_curated):
        self.df = df
        self.cas_curated = cas_curated

    # ALL Issues must be named "rIssues_x"  where x is usually a consecutive number.
    # x will become the flag's name as in "r_x"

    def get_rec_set(self,cond):
        reckey_set = self.df[cond].reckey.tolist()
        return reckey_set

    def rIssue_001(self):
        """This flag indicates that a record is a redundant duplicate of another in the same disclosure."""
        c1 = self.df.dup_rec
        return self.get_rec_set(c1)

    def rIssue_002(self):
        """PercentHFJob is 0 or not reported; mass cannot be calculated and MassIngredient is typically also missing."""
        c1 = self.df.ingKeyPresent & ~(self.df.PercentHFJob>0)
        return self.get_rec_set(c1)

    def rIssue_003(self):
        """CASNumber must be corrected"""
        caslst = self.cas_curated[self.cas_curated.categoryCAS=='corrected'].CASNumber.tolist()
        c1 = self.df.CASNumber.isin(caslst)
        return self.get_rec_set(c1)

class Flag_issues():
    """Used to detect known data issues in the FracFocus data and generate appropriate flags to warn users.
    For each issue, a list is returned of DisclosureId (or IngredientsId) for the flags"""

    def __init__(self,df,cas_curated,out_dir):
        self.df = df
        self.cas_curated = cas_curated
        self.out_dir = out_dir
        self.dIssues = Disclosure_Issues(df)
        self.rIssues = Record_Issues(df,cas_curated)
        self.get_disc_issues()
        self.get_rec_issues()

    def get_disc_issues(self):
        self.disc_issue_dic = {}
        for item in dir(self.dIssues):
            if item[:7] == 'dIssue_':
                name = 'd_'+item[7:]
                self.disc_issue_dic['self.dIssues.'+item+'()'] = name
        # print(self.disc_issue_dic)

    def make_disc_flag_df(self,disc_set,disc_issues):
        self.disc_df = pd.DataFrame({'DisclosureId':list(disc_set)})
        for issue in disc_issues:
            self.disc_df[issue[1]] = self.disc_df.DisclosureId.isin(issue[0])


    def get_rec_issues(self):
        self.rec_issue_dic = {}
        for item in dir(self.rIssues):
            if item[:7] == 'rIssue_':
                name = 'r_'+item[7:]
                self.rec_issue_dic['self.rIssues.'+item+'()'] = name
        # print(self.rec_issue_dic)

    def make_rec_flag_df(self,reckey_set,rec_issues):
        self.rec_df = pd.DataFrame({'reckey':list(reckey_set)})
        for issue in rec_issues:
            self.rec_df[issue[1]] = self.rec_df.reckey.isin(issue[0])

    def detect_all_issues(self):
        disc_set = set()
        names = []
        disissues = []
        for test in self.disc_issue_dic.keys():
            name = self.disc_issue_dic[test]
            # print(test)
            lst = eval(test)
            print(f'generating flags for: {name}')
            disc_set.update(lst)
            names.append(name)
            disissues.append((lst,name))
        # make sure we don't have duplicate names
        seen = set()
        dupes = [x for x in names if x in seen or seen.add(x)]
        assert len(dupes)== 0, f'Duplicates in flag names: {dupes}'
        self.make_disc_flag_df(disc_set,disissues)

        rec_set = set()
        names = []
        recissues = []
        for test in self.rec_issue_dic.keys():
            name = self.rec_issue_dic[test]
            lst = eval(test)
            print(f'generating flags for: {name}')            
            rec_set.update(lst)
            names.append(name)
            recissues.append((lst,name))
        # make sure we don't have duplicate names
        seen = set()
        dupes = [x for x in names if x in seen or seen.add(x)]
        assert len(dupes)== 0, f'Duplicates in flag names: {dupes}'

        self.make_rec_flag_df(rec_set,recissues)

    def add_summary_fields(self):
        """add field with all true flag names"""
            # now add single flag fields to each
        t = self.disc_df
        # print(len(t), t.columns)
        cols = t.columns.tolist()
        cols.remove('DisclosureId')  # all the rest should be flag columns
        # print(cols)
        t['d_flags'] = ''
        for col in cols:
            dkeys = t[t[col]].DisclosureId.tolist() # list of DId that are True
            t.d_flags = np.where(t.DisclosureId.isin(dkeys),
                                    t.d_flags+col+' ',
                                    t.d_flags)
        t.to_parquet(os.path.join(self.out_dir,'disclosure_issues.parquet'))

        t = self.rec_df
        cols = t.columns.tolist()
        cols.remove('reckey')  # all the rest should be flag columns
        t['r_flags'] = ''
        for col in cols:
            rkeys = t[t[col]].reckey.tolist() # list of DId that are True
            t.r_flags = np.where(t.reckey.isin(rkeys),
                                    t.r_flags+col+' ',
                                    t.r_flags)
        t.to_parquet(os.path.join(self.out_dir,'record_issues.parquet'))


    