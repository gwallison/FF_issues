# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 18:00:12 2024

@author: Gary
"""
import pandas as pd
import os
import datetime
import openFF.common.handles as hndl 


class WatchListManager():
    def __init__(self,name='empty',):
        self.name = name
        self.wl_dir = hndl.watchlist_dir
        self.dirname = '?'
        
    def get_norm_name(self,name):
        nname = name.replace(' ','_')
        self.dirname = os.path.join(self.wl_dir,nname)
        

        
    def create_new_watchlist(self,name=None,description='empty',
                             FF_flaw_str = 'junk', 
                             init_df=pd.DataFrame({'APINumber':[],
                                                  'DisclosureId':[]})):
        """FF_flaw_str is the flawid that can be used to determine if the 
        particular disclosure is still flawed or not.  It will be used to indicate
        a fix by the company."""
        if name: self.name=name
        self.get_norm_name(self.name)
        assert not os.path.exists(self.dirname), f'watchlist "{self.name}" already exists!'
        os.mkdir(self.dirname)
        init_df['init_date'] = datetime.datetime.today()
        init_df['FF_notified'] = ' '
        init_df['status'] = 'initial'
        fn = os.path.join(self.dirname,'api_df.parquet')
        init_df.to_parquet(fn)
        print('init_df written')
        meta = '**FLAW_STR: '+FF_flaw_str+'\n'
        meta += '**DESCRIPTION: '+description+'\n\n'
        with open(os.path.join(self.dirname,'meta.txt'),'w') as f:
            f.write(meta)
        
        
    def update_one_watchlist(self,name=None,FF_notified=None,blogpage=None,
                      status=None):
        if name: self.name=name
        self.get_norm_name(self.name)
        assert os.path.exists(self.dirname), f'watchlist "{self.name}" does not exists!'
        if blogpage:
            with open(os.path.join(self.dirname,'meta.txt'),'a') as f:
                f.write(f'**BLOG_LINK: {blogpage} \n')
        if (FF_notified!=None) | (status!=None):
            fn = os.path.join(self.dirname,'api_df.parquet')
            t = pd.read_parquet(fn)
            if FF_notified:
                t.FF_notified = FF_notified
            if status:
                t.status = status
            t.to_parquet(fn)
            

    def update_master_watchlist(self):
        dirlst = os.listdir(self.wl_dir)
        df_lst = []
        for item in dirlst:
            try:
                df = pd.read_parquet(os.path.join(self.wl_dir,item,'api_df.parquet'))
                print(f'{item}: Num disclosures: {len(df)}')
                df_lst.append(df)
            except:
                print(f'{item}: No dataframe registered')
        alldf = pd.concat(df_lst)
        alldf.to_parquet(os.path.join(hndl.ff_issues_dir,'watch_list_master.parquet'))
        print('*** watch_list_master.parquet written ***')
            
    def get_summary(self):
        dirlst = os.listdir(self.wl_dir)
        for item in dirlst:
            try:
                df = pd.read_parquet(os.path.join(self.wl_dir,item,'api_df.parquet'))
                numdisc = len(df)
            except:
                numdisc = 'df not loaded'
            print(f'{item}: num disc: {numdisc}')
            
        
        
if __name__ == '__main__':
    wlm = WatchListManager()
    wlm.create_new_watchlist(name='new test')