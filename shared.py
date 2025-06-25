from pathlib import Path
import pandas as pd
from utils.data_utils import get_chains
#import json

chains_dir = "Chains/"
corn_single = get_chains(chains_dir + "corn", nsteps=1)
corn_double = get_chains(chains_dir + "ddgs", nsteps=2)
soy = get_chains(chains_dir + "soy", nsteps = 2)
fullchains = {'corn_direct':corn_single, 'corn_ddgs':corn_double, 'soy': soy}

#fs_counties = pd.read_csv("data/fs_counties.csv")['FIPS'].tolist()

# with open('data/geojson-counties-fips.json') as f:
#     counties = json.load(f)
