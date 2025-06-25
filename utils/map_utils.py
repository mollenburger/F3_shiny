import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.colors as mcolors
import re
from utils.ref_data import county_points, county_poly, state_poly, arcdicts, geopoints, colors
from utils.flow_utils import build_flow, assign_bins
from plotnine import geom_map, scale_size_continuous, scale_fill_manual, aes

def hex_color_gradient(start_hex, end_hex, steps=4):
    start = mcolors.to_rgb(start_hex)
    end = mcolors.to_rgb(end_hex)
    colors = [mcolors.to_hex(tuple([(1-t)*s + t*e for s, e in zip(start, end)])) for t in np.linspace(0, 1, steps)]
    return colors

def is_hex_color(s):
    return bool(re.fullmatch(r"#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})", s))


fill_gradients = {
    "corn" : hex_color_gradient("#f7e8bf","#e3b338"),
    "alfalfa" : hex_color_gradient("#b273ba","#e2cbe5"),
    "hog" : hex_color_gradient("#e1ced3", "#a36978"),
    "soy" : hex_color_gradient("#d3e1ce", "#4f873b"),
    "ghg" : hex_color_gradient("#cabeb3","#a19386")
    }


state_outline = geom_map(data = state_poly, color="#000000", fill = None, size = 0.2)

def build_chloro (chains_list, crop, chloro_column, com):
    """
    Generate a geospatial dataframe for choropleth mapping of a commodity flow chain.

    Parameters
    ----------
    chains_list : dict
        A dictionary containing the dataframes for all the commodity chains.
    crop : str
        The commodity name for the chain to be processed.
    chloro_column : str
        The column name for the data to be used for the choropleth mapping.
    com : list of str
        A list of commodity names that are the destination of the flow in the chain.

    Returns :
    map_data: gpd.GeoDataFrame
        a geopandas GeoDataFrame ready for plotting using p9.geom_map()


    """
    chain_data = chains_list[crop]
    chain_data = (chain_data[chain_data['dest_final'].isin(com)]
                    .groupby('source_FIPS_0')
                    .agg({"flow_kg_0":"sum"}).reset_index())
    map_data = gpd.GeoDataFrame(pd.merge(chain_data,county_poly,
                        left_on = "source_FIPS_0",
                        right_on = "GEOID",
                        how = "inner"))
    color_bin_values, bin_edges = assign_bins(map_data[chloro_column], max_bins = 4)
    map_data["colorbin"]= color_bin_values.fillna(2).astype("category")
    return map_data

# in: chain data, number of steps, [subset of chain?]
# out: map_data - polygons with colorbin values, source_0 point, dest_0_point, dest_1_point, .... dest_[number of steps-1]_point
# dest points can be either FIPS or facility (but just FIPS for now)
# we may want to continue using FIPS for the flow arcs, aggregating the facilities that share one FIPS (by industry?)
# do need facilities spatial for size-scaled bubbles etc

#def pick_chains(chain_list, source, dest, type = "direct"):
    


def flow_components(chain_data, 
        steps = 2, 
        subset=0, 
        dest_types = ['FIPS','FIPS'],
        flow_units = ["kg","kg"]): 
    
    """
    Generate map components for visualizing flow data across multiple stages.

    This function processes chain data to create geospatial map components,
    including polygons for choropleth mapping, source points, destination points,
    and flow arcs between them. It supports filtering by subsets and varying
    destination types and flow units.

    Args:
        chain_data (pd.DataFrame): Input data containing the flow chains.
        steps (int, optional): Number of stages in the flow chain. Default is 2.
        subset (str or int, optional): Subset of the chain for filtering. Default is 0.
        dest_types (list of str, optional): Types of destination identifiers. Default is ['FIPS', 'FIPS'].
        flow_units (list of str, optional): Units for flow measurement. Default is ["kg", "kg"].
        chloro_column (str, optional): Column name for choropleth mapping. Default is "flow_kg_0".

    Returns:
        tuple: A tuple containing:
            - map_data (gpd.GeoDataFrame): Geospatial dataframe for choropleth mapping.
            - flow_points (list of gpd.GeoDataFrame): List of geospatial dataframes for source and destination points.
            - flow_arcs (list of LineString): List of flow arcs connecting the points.
    """

    flows = [f"flow_{flow_units[i]}_{i}" for i in range(steps)]
    destinations = [f"destination_{dest_types[i]}_{i}" for i in range(steps)]

    if subset:
        print(f"chain ending in {subset}")
        chain_data = chain_data[chain_data[f'dest_final']==subset]   


    source_point = gpd.GeoDataFrame(pd.merge(chain_data,county_points, 
                                left_on = "source_FIPS_0",
                                right_on = "GEOID",
                                how = "left"))
    flow_points = [source_point]
    for i in range(steps):
        dp = gpd.GeoDataFrame(pd.merge(chain_data,geopoints[dest_types[i]], 
                            left_on = destinations[i],
                            right_on = "GEOID",
                            how = "left"))
        flow_points.append(dp) 

    flow0_arc = build_flow(chain_data, "source_FIPS_0",destinations[0], flows[0], 
                            arcdicts['FIPS'], arcdicts[dest_types[0]])
    flow_arcs = [flow0_arc]
    for i in range(steps)[1:]:
        fa = build_flow(chain_data,destinations[i-1], destinations[i], flows[i],
                        arcdicts[dest_types[i-1]], arcdicts[dest_types[i]])
        flow_arcs.append(fa)                        

    return flow_points, flow_arcs

def build_flow_data(input_data, flows_to = ["broiler", "hog", "cows", "cattle"], steps = 2):
    farclist = {}
    fptlist = {}
    for com in flows_to:
        flowpoints, flowarcs = flow_components(input_data, subset = com, steps = steps)
        farclist[com] = flowarcs
        fptlist[com] = flowpoints
    flow_data = {
        "flowarcs":farclist,
        "flowpoints":fptlist}

    return flow_data

# map components includes: 
#   chloro - set with chloro_column
#   flow points - all stages
#   flow arcs - all stages 
        # steps = 3 # total number of sources/dstinations (one source to one destination = 2 steps, source -> destination0 -> destination1 = 3 steps)``
        # subset=0, # this needs to be subset to one com for units, dest_types to make sense
        #    should this take a list of coms?
        # dest_types = ['FIPS','FIPS'] # should be length steps-1
        # flow_units = ["kg","kg"], # should be length steps-1
        # chloro_column = "flow_kg_0" # default is initial crop flow, can be any flow in chain file
        # ? can we have these saved for all coms to filter later for webapp ?

# map based on map components output and params 
# shiny app - set dest_types and flow_units based on com 
# shiny filters: scale_fill_manual
#   counties at stage n 
#   commodities at stage n - currently only final com in chain

# input data to mapping function is dict of         maplist[com] = mapslist of maps, flowpts, flowarcs 
#   - map[com](only one, "colorbin" column for color) 
#   - flow[com][stage] (arc and points) 


def make_geom_flow(flowlist, commodity, stage, **kwargs):
    """
    Create a plotnine geom for a given commodity and stage.

    Args:
        commodity (str): The name of the destination commodity
        stage (int): The stage number - for arcs, this is the stage for the first node (so stage 0 is from source0 to dest0)
        flowlist (dict): A dictionary containing flow data for each commodity and stage.
        **kwargs: Additional keyword arguments, including:
            color: either a hex color code or a key in the colors dict.
            size (str): The size type for the geom. Can be "fixed" or "scaled". 
            default: the default size value (only used if size is "fixed").
        
    Returns:
        plotnine.geom: The created geom_map object, either points or arcs
    """
    color = kwargs.get("color", commodity)
    default = kwargs.get("default", 0.2)
    size = kwargs.get("size", "fixed")

    if color in colors.keys():
        color = colors[color]
    elif is_hex_color(color):
        color = color
    else: 
        raise ValueError("color must be a hex code or key in colors dict")
    if size == "fixed":
        return geom_map(data = flowlist[commodity][stage], size = default, color = color)
    if size == "scaled":
        return geom_map(aes(size = "flowsize"), data=flowlist[commodity][stage], color = color)
    else:
        raise ValueError("size must be 'fixed' or 'scaled'")

def make_geom_chloro(chlorodata, dest_com):
    """
    Create a plotnine geom for the chloropleth map of a given commodity.

    Args:
        maplist (list): list including chloropleth map data for each commodity.
        commodity(str): The destination commodity (e.g. "hog").
    Returns:
        plotnine.geom: geom_map object, for a chloropleth map
    """
    return geom_map(aes(fill="colorbin"), data=chlorodata, color = "white", size = 0.1)

def make_scale(type, **kwargs):   
    """
    Create a plotnine scale for a given component and type.

    Args:
        commodity (str): the commodity name  - used for color gradients
        type (str): The type of scale to create. Can be "fill" or "size".

    Returns:
        plotnine.scale: The created scale.
    """
    commodity = kwargs.get("commodity")
    if type == "size":
        return scale_size_continuous(range = (0,1))
    elif type == "fill":
        try: 
            return scale_fill_manual(values = fill_gradients[commodity])
        except KeyError:
            raise ValueError("commodity must be defined for fill scale and must be a key in fill_gradients dict")
    else:
        raise ValueError("type must be 'fill' or 'size'")
    
# additional automation that isn't quite working yet

# def make_map(components, scales):
#     """
#     Create a plotnine ggplot figure from a list of components.

#     Args:
#         components (list): List of plotnine geoms
#         scales (list): List of plotnine scales

#     Returns:
#         plotnine.ggplot: The assembled plot.
#     """
#     plot = ggplot()
#     for comp in components:
#         plot = plot + comp
#     for scale in scales:
#         plot = plot + scale
#     plot = (plot 
#             + theme_void()
#             + theme(figure_size=(10,6), 
#                     panel_background=element_rect(fill="white"),
#                     legend_position="none"))
#     return plot

# def flow_map(mapdata, commodity, chloro_com, point_stage=[], arc_stage = [], arc_colors = [], arc_sizes = [], point_size = "fixed"):
#     """
#     Create a flow map using plotnine

#     Args:
#         mapdata (dict): A dictionary containing the map data, flow points, and flow arcs.
#         commodity (str): The destination commodity name (eg "hog").
#         chloro_com (str): The commodity name for the chloropleth map (eg "corn").
#         point_stage (list): A list of stages for the flow points.
#         arc_stage (list): A list of stages for the flow arcs.
#         arc_size (str): The size type for the flow arcs. Can be "fixed" or "scaled".
#         point_size (str): The size type for the flow points. Can be "fixed" or "scaled".

#     Returns:
#         plotnine.ggplot: The created flow map.
#     """
#     chloro = make_geom_chloro(mapdata["basemap"], commodity)
#     arcs = []
#     points = []
#     scales = [make_scale(chloro_com, "fill")]
#     if len(point_stage) > 0:
#         for stage in point_stage:        
#             points.append(make_geom_flow(mapdata["flowpoints"], commodity, stage, size = point_size))
#     else: 
#         points = 0
#     for stage, color,size in zip(arc_stage, arc_colors, arc_sizes):
#         arcs.append(make_geom_flow(mapdata["flowarcs"], commodity, stage, size = size, color = color))
#         if size == "scaled":
#             scales.append(make_scale(commodity, "size"))
#     components = [chloro, state_outline, arcs, points]
#     return make_map(components, scales)
