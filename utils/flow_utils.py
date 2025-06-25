import numpy as np
import math
import pandas as pd 
import geopandas as gpd
from collections import namedtuple
from shapely.geometry import LineString
import matplotlib.pyplot as plt



Pt = namedtuple('Pt', 'x, y')
Circle = Cir = namedtuple('Circle', 'x, y, r')


def circles_from_p1p2r(p1, p2, r):
    'Following explanation at http://mathforum.org/library/drmath/view/53027.html'
    # update 0/16/24 - website is dead, try https://web.archive.org/web/20181018095220/http://mathforum.org/library/drmath/view/53027.html 
    # or in the documentation on FoodS^3 GDrive -MO
    if r == 0.0:
        raise ValueError('radius of zero')
    (x1, y1), (x2, y2) = p1, p2
    if p1 == p2:
        raise ValueError('coincident points gives infinite number of Circles')
    # delta x, delta y between points
    dx, dy = x2 - x1, y2 - y1
    # dist between points
    q = math.sqrt(dx**2 + dy**2)
    if q > 2.0*r:
        raise ValueError('separation of points > diameter')
    # halfway point
    x3, y3 = (x1+x2)/2, (y1+y2)/2
    # distance along the mirror line
    d = math.sqrt(r**2-(q/2)**2)
    # One answer
    c1 = Cir(x = x3 - d*dy/q,
             y = y3 + d*dx/q,
             r = abs(r))
    # The other answer
    c2 = Cir(x = x3 + d*dy/q,
             y = y3 - d*dx/q,
             r = abs(r))
    return c1, c2


def circles_from_p1p2theta(p1, p2, theta):
    d = math.sqrt( (p1[0]-p2[0])**2 + (p1[1] - p2[1])**2 )
    r = d/math.sqrt(2 - 2*math.cos(theta))
    return circles_from_p1p2r(p1, p2, r)


def angle(c, p):
    """
    angle of the vector from c to p measured as radians from the horizontal relative to c
    """
    (xc, yc), (xp, yp) = c, p
    dx, dy = xp-xc, yp-yc
    if dx == 0:
        if dy > 0:
            return 0.5 * math.pi
        else:
            return 1.5 * math.pi
    else: 
        if dx<=0:
            return math.pi + np.arctan(dy/dx)
        elif dy < 0:
            return 2*math.pi + np.arctan(dy/dx)
        else:
            return np.arctan(dy/dx)
    

def arc(p1, p2, theta=np.pi/3, n=25):
    if (p1.x < p2.x) and (p1.y > p2.y):
        return arc(p2, p1)
    
    c1, c2 = circles_from_p1p2theta(p1, p2, theta)
    r = c1.r
    c = Pt(c1.x, c1.y) if c1.y < c2.y else Pt(c2.x, c2.y) # pick the lower center
    t1 = angle(c, p1)
    t2 = angle(c, p2)
    
    if np.abs(t2-t1) > math.pi:
        T = np.linspace(max(t1, t2)-2*math.pi, min(t1, t2), num=n)
    else:
        T = np.linspace(t1, t2, num=n) 
    x = [c.x + r*math.cos(t) for t in T]
    y = [c.y + r*math.sin(t) for t in T]
    
    return x, y
    


def build_arcs(flow_data, source_point_dict, dest_point_dict):
    tmp_list = []
    # print(flow_data.head())
    for row in flow_data.itertuples(index=False):
        source, dest, flow_size = row[0], row[1], row[2] 
        if (source == dest) or (source not in source_point_dict) or (dest not in dest_point_dict):
            continue

        sloc = source_point_dict[source] 
        dloc = dest_point_dict[dest] 

        try:
            p1 = Pt(sloc.x, sloc.y)
            p2 = Pt(dloc.x, dloc.y)
        except:
            print("WARNING: missing points!")
            continue 
        # flow arc is drawn as a series of short segments 
        long, lat = arc(p1, p2)
        tmp_list.append({"source":source,
                "dest":dest,
                "flowsize":flow_size,
                "geometry":LineString(zip(long,lat))})

        # create linestring and append to df of linestrings (below)
    arcs_df = gpd.GeoDataFrame(tmp_list)
    return arcs_df

def build_flow(dataframe, source, dest, flow, source_dict, dest_dict, drop_bottom = 0.1):
    flow_data = dataframe [[source,dest,flow]].groupby([source, dest]).sum().reset_index()
    flow_data = flow_data[flow_data[flow]>flow_data[flow].quantile(drop_bottom)]
    flow_arcs = build_arcs(flow_data, source_dict, dest_dict)
    return flow_arcs 

def assign_bins(values, max_bins=4, bin_style='equal'):
    ''' 
    bin data to make heat maps look better, returning a list of integers from 0 to max_bins.
    assumes all values are positive or zero. also works for grouping facility points by size.
    '''

    def round_edge(x):
        ''' round a number to its first digit plus zeros'''
        order_of_mag = 10 ** np.floor(np.log10(x))
        first_digit = np.floor(x / order_of_mag)
        return first_digit * order_of_mag
              
    # group values into equally sized groups using pandas "quantile cut"
    if bin_style == 'equal':
        binned_data, bin_edges = pd.qcut(values, max_bins, retbins=True, labels=False)
        # 'labels=False' automatically returns integers as the bin values (starting from 0)
        new_edges = [round_edge(x) for x in bin_edges]
        if np.min(values) >= 1.0:
            new_edges = [int(y) for y in new_edges]

        # bin edges can't have duplicates, so we need to drop if we have any after the rounding
        binned_data = pd.cut(values, new_edges, duplicates='drop', labels=False)
    return binned_data, new_edges