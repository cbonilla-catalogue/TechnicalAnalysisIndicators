# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 12:28:10 2019

@author: cbonilla
"""
#%% ----------------------------------- Package Imports
import pandas as pd
from numpy import nan
from fredapi import Fred
fred = Fred(api_key='287dcf1a4ec41e9f44645fb74180eb42')

#%% ----------------------------------- Read Data
#df = pd.read_excel('{}/{}'.format(csv_location, csv_filename))
#USrates = ['T10YIEM','DGS1','DGS10','TB3MS']
USrates = ['DGS1','DGS10']

df = pd.DataFrame()
for i in range(0,len(USrates)):
    df[USrates[i]] = fred.get_series(USrates[i])
#df.head()

#%% ----------------------------------- RSI Signal Engineering
def generate_RSI_stats(df, series,RSI_decay=3):
    dff = 'diff_'+series
    dn = series+'_dn'
    up = series+'_up'
    
    df[dff] = df[series].diff()
    df[up] = df[dff]
    df.loc[df[dff] < 0, up] = 0
    df[up] = (df[up]).ewm(alpha=(1/RSI_decay)).mean()
    df[dn] = df[dff]
    df.loc[df[dff] > 0, dn] = 0
    df[dn] = (df[dn]).ewm(alpha=(1/RSI_decay)).mean()
    df[series+'_RSI_signal'] = 100-100/(1-df[up]/df[dn])

#%% ----------------------------------- RSI Trading Logic
def RSI_trade_strategies(df, series,buy_signal=90, sel_signal=10, buy_exit=50,sel_exit=50):
    buy_sel_signal = str(series+'_buy_sel_signal')
    
    # Calculate Buy Signal
    df['buy_signal'] = nan
    #df['buy_signal'] = 0
    df.loc[df[series] > buy_signal, 'buy_signal'] = 1
    df.loc[df[series] <= buy_exit, 'buy_signal'] = 0
    df['buy_signal'] = df['buy_signal'].ffill()
    df.loc[(df['buy_signal'].shift() == 1) & (df['buy_signal'] == 0), 'buy_signal'] = -1
    
    # Calculate Sell Signal
    df.loc[df[series] < sel_signal, 'sel_signal'] = 1
    df.loc[df[series] >= sel_exit, 'sel_signal'] = 0
    df['sel_signal'] = df['sel_signal'].ffill()
    df.loc[(df['sel_signal'].shift() == 1) & (df['sel_signal'] == 0), 'sel_signal'] = -1
    
    # Combine
    df[buy_sel_signal] = df['buy_signal'] - df['sel_signal']
    # Cleanup
    df[buy_sel_signal] = df[buy_sel_signal].fillna(0)
    df.drop(['buy_signal', 'sel_signal'], axis=1, inplace=True)

#%% ----------------------------------- RSI Trading MTM

# Engineer RSI signal and trading logic
generate_RSI_stats(df=df, series = 'DGS10',RSI_decay=3)
RSI_trade_strategies(df, series = 'diff_DGS10',buy_signal=90, sel_signal=10, buy_exit=50,sel_exit=50)

# Calculate trade p&l
import seaborn as sns
sns.set(style="whitegrid")
df['MTM']= df['buy_sel_signal']*df['diff_USGG10YR']

PositiveMTM = df.loc[df['MTM'] > 0, 'MTM'].count() / (df.loc[df['MTM'] > 0, 'MTM'].count() +df.loc[df['MTM'] < 0, 'MTM'].count() )
NegativeMTM = df.loc[df['MTM'] < 0, 'MTM'].count() / (df.loc[df['MTM'] > 0, 'MTM'].count() +df.loc[df['MTM'] < 0, 'MTM'].count() )

print('Positive hit ratio '+"{:.3}%".format(PositiveMTM*100))
print('Negative hit ratio '+"{:.3}%".format(NegativeMTM*100))
print('Mean MTM ex transaction costs '+"{:.3}%".format(df['MTM'].mean()))

ax = sns.violinplot(x=df.loc[df['MTM'] != 0, 'MTM'])

#df['MTM'].hist()
#print(df['MTM'].loc['20110102':'20181231'].describe())
#df['MTM'].loc['20110102':'20181231'].plot()

#%% --------------------------------- Notes Appendix
# https://mortada.net/python-api-for-fred.html
# T10YIEM = 10-year inflation expectations
# GS1 = 1-Year Treasury Constant Maturity Rate
# GS10 = 10-Year Treasury Constant Maturity Rate
# TB3MS =  3-Month Treasury Bill: Secondary Market Rate
# Federal Debt: Total Public Debt (GFDEBTN
# Federal government current expenditures: Interest payments (A091RC1Q027SBEA)
#http://pandas.pydata.org/pandas-docs/stable/user_guide/computation.html