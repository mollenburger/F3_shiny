import glob
import os
import pandas as pd
from pathlib import Path

def get_chains(folderpath,nsteps=1):
    """
    Reads all files in a folderpath that end with "_full.csv", reads them in as pandas dataframes,
    and adds columns to each dataframe for the commodity names in the source and destination
    of the commodity flow. Concatenates all dataframes into one and returns the result.

    Parameters
    ----------
    folderpath : str
        path to folder containing files to be read in

    Returns
    -------
    pd.DataFrame
        concatenated dataframes from all files in folderpath
    """
    all_files = glob.glob(os.path.join(folderpath, "*_full.csv"))
    # can output files make com name 1 word (no spaces) eg cattlefeed, cowsmilk
    li = []
    for name in all_files:
        df = pd.read_csv(name,  index_col=None)
        df["source_0_com"] = Path(name).stem.split('_')[0].split('-')[0]
        for i in range(nsteps):
            com = Path(name).stem.split('_')[0].split('-')[i]
            df[f"flow_{i}_com"] = com
        df[f"dest_final"] = Path(name).stem.split('_')[0].split('-')[i+1]
        li.append(df)
    return pd.concat(li, ignore_index=True)



def filter_chains(fullchains, filterlist, column_in_chain):
    """
    Filter a dictionary of dataframes by a column in each dataframe.

    Parameters
    ----------
    fullchains : dict
        dictionary of dataframes, where each key is a string representing a commodity
        chain and each value is a pd.DataFrame
    filterlist : list
        list of strings representing the values of the column to filter by
    column_in_chain : str
        name of the column in each dataframe to filter by

    Returns
    -------
    filtered: dict
        dictionary of filtered dataframes
    """
    filtered = {}
    for chain, df in fullchains.items():
        filtered[chain] = df[df[column_in_chain].isin(filterlist)]
    return filtered