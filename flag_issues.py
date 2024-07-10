"""This code is used to detect specific issues in the Open-FF generated "full_df.parquet" file.  For each issue,
a fuction is written to produce a flag when certain conditions are met. Those flags are then used to create
a database that lists all the disclosures/records that are involved.  This database is specific to a particular
full_df file and therefore a specific bulk data download and its date.  Because of the fluid nature of FracFocus
entries (and the fact that they can be modified without public notice), specific instances of issues may be corrected
after these flags were created."""

import pandas as pd
import numpy as np
import os
import FF_issues.process_master_files as pmf

class Disclosure_Issues():
    def __init__(self,df):
        self.df = df
        self.gb = df.groupby('DisclosureId',as_index=False)[['APINumber','TotalBaseWaterVolume','has_TBWV',
                                                             'bgStateName',
                                                             'is_duplicate','MI_inconsistent','ws_perc_total',
                                                             'no_chem_recs','pub_delay_days']].first()

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
        """ The MassIngredient data do not pass the internal consistency test, so are not used when reporting mass."""
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

    def dIssue_007(self):
        """ Chlorine dioxide percentage is over 80%"""
        cond = (self.df.bgCAS=='10049-04-4') & (self.df.PercentHFJob>80)
        return self.df[cond].DisclosureId.unique().tolist()

    def dIssue_008(self):
        """Percent of sand is over 50%"""
        cond = (self.df.bgCAS=='14808-60-7') & (self.df.PercentHFJob>50)
        return self.df[cond].DisclosureId.unique().tolist()

    def dIssue_009(self):
        """Cororado pub delay > 120 day"""
        cond = (self.gb.bgStateName=='colorado') & (self.gb.pub_delay_days>120)
        return self.get_disc_set(cond)

    def dIssue_010(self):
        """Ohio pub delay > 60 day"""
        cond = (self.gb.bgStateName=='ohio') & (self.gb.pub_delay_days>60)
        return self.get_disc_set(cond)

    def dIssue_011(self):
        """Texas pub delay > 30 days"""
        cond = (self.gb.bgStateName=='texas') & (self.gb.pub_delay_days>30)
        return self.get_disc_set(cond)

    def dIssue_012(self):
        """Pennsylvania pub delay > 60 days"""
        cond = (self.gb.bgStateName=='pennsylvania') & (self.gb.pub_delay_days>60)
        return self.get_disc_set(cond)

    def dIssue_013(self):
        """New Mexico pub delay > 45 days"""
        cond = (self.gb.bgStateName=='new mexico') & (self.gb.pub_delay_days>45)
        return self.get_disc_set(cond)

    def dIssue_014(self):
        """Oklahoma pub delay > 60 days"""
        cond = (self.gb.bgStateName=='oklahoma') & (self.gb.pub_delay_days>60)
        return self.get_disc_set(cond)

    def dIssue_015(self):
        """North Dakota pub delay > 60 days"""
        cond = (self.gb.bgStateName=='north dakota') & (self.gb.pub_delay_days>60)
        return self.get_disc_set(cond)

    def dIssue_016(self):
        """Wyoming pub delay > 30 days"""
        cond = (self.gb.bgStateName=='wyoming') & (self.gb.pub_delay_days>30)
        return self.get_disc_set(cond)

    def dIssue_017(self):
        """Utah pub delay > 60 days"""
        cond = (self.gb.bgStateName=='utah') & (self.gb.pub_delay_days>60)
        return self.get_disc_set(cond)

    def dIssue_018(self):
        """West Virginia pub delay > 90 days"""
        cond = (self.gb.bgStateName=='west virginia') & (self.gb.pub_delay_days>90)
        return self.get_disc_set(cond)

    def dIssue_019(self):
        """MassIngredient of water is not consistent with TBWV"""
        gb1 = self.df.groupby('DisclosureId',as_index=False)['TotalBaseWaterVolume'].first()
        c1 = self.df.MassIngredient.notna() # ignore records without data
        c2 = self.df.is_water_carrier

        gb2 = self.df[c1&c2].groupby('DisclosureId',as_index=False)\
            ['MassIngredient'].sum()
        mg = pd.merge(gb1,gb2,on='DisclosureId',how='inner')
        mg['TBWV_mass'] = mg.TotalBaseWaterVolume * 8.34
        mg['fracdiff'] = np.absolute(mg.MassIngredient - mg.TBWV_mass)/mg.TBWV_mass
        return mg[mg.fracdiff>0.2].DisclosureId.unique().tolist()

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
        """CASNumber must be corrected; minor cleaning is not counted"""
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
        pobj = pmf.Process_Master_Files()
        self.masterdf = pobj.process_obj()
        self.warnings = pobj.get_warning_dict()
        
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

    def get_max_warning_as_df(self,lst):
        level_dict = {'alert': (3,'alert'), 
                      'watch': (2,'watch'),
                      'info': (1,'info'),
                      '': ('',0)}
        max_level = []
        for combination in lst:
            # print(combination)
            flags = combination.strip().split(' ')
            levels = []
            for flag in flags:
                warning = self.warnings[flag]
                levels.append(level_dict[warning])
            max_level.append(max(levels)[1])
        out = pd.DataFrame({'flag_combo':lst,'max_level':max_level})            
        # print(out)
        return out

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
        """add field with all true flag names and for each flag, update a "warning" summary
        field"""
            # now add single flag fields to each
        t = self.disc_df
        # print(len(t), t.columns)
        cols = t.columns.tolist()
        cols.remove('DisclosureId')  # all the rest should be flag columns
        # print(cols)
        t['d_flags'] = ''
        # t['d_warnings'] = 'info'
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

        
# if __name__ == "__main__":
#     import sys
#     sys.path.insert(0,'c:/MyDocs/integrated/') # adjust to your setup
#     import openFF.common.text_handlers as th
#     import openFF.common.file_handlers as fh
#     import openFF.common.handles as hndl
# #    import FF_issues.flag_issues as fi
#     import numpy as np
#     root_dir = 'sandbox'
#     orig_dir = os.path.join(root_dir,'orig_dir')
#     work_dir = os.path.join(root_dir,'work_dir')
#     final_dir = os.path.join(root_dir,'final')
#     ext_dir = os.path.join(root_dir,'ext')
    
#     print('assembling tables of FracFocus flaws')
#     df = fh.get_df(os.path.join(final_dir,'full_df.parquet'))
#     cas_curated = fh.get_df(os.path.join(final_dir,'curation_files','cas_curated.parquet'))
    
#     obj = Flag_issues(df=df,cas_curated=cas_curated,
#                          out_dir=final_dir)
#     obj.detect_all_issues()
