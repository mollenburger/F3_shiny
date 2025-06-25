import pandas as pd
import geopandas as gpd


# read in geodata
#TODO: convert everything to long,lat
state_poly = gpd.read_file("data/ConUS_state_5070.gpkg")
state_poly["centroid"] = state_poly.centroid
state_points = state_poly[["GEOID","centroid"]].rename({"centroid":"geometry"}, axis=1)
state_poly = state_poly.to_crs(epsg = "4326")
state_points = state_points.to_crs(epsg = "4326")


county_poly = gpd.read_file("data/ConUS_county_5070.gpkg")
county_poly["GEOID"]=county_poly["GEOID"].astype("int64")
county_poly["centroid"] = county_poly.centroid
county_poly = county_poly.to_crs(epsg = "4326")
county_points = county_poly[["GEOID","centroid"]].rename({"centroid":"geometry"}, axis=1).to_crs(epsg = "4326")
county_points['lon'] = county_points['geometry'].x
county_points['lat'] = county_points['geometry'].y
county_points_dict = {i: pt for i, pt in zip(county_points['GEOID'], county_points['geometry'])}

fac_data = pd.read_csv("data/company_location_fips_2017_v5.csv")
facilities_points = (gpd.GeoDataFrame(fac_data, 
        geometry=gpd.points_from_xy(fac_data.longitude,fac_data.latitude))
        .set_crs(epsg="4326"))
facilities_points["code"]= facilities_points["code"].astype(int)
fac_points_dict = {i: pt for i, pt in zip(facilities_points['code'], facilities_points['geometry'])}

geopoints = {}
geopoints['FIPS'] = county_points
geopoints['facility'] = facilities_points

arcdicts = {}
arcdicts['FIPS']=county_points_dict
arcdicts['facility'] = fac_points_dict

# brand colors
colors = {
    "hog": "#a36978",
    "ddgs": "#57ad4d",
    "cattle": "#6d6a85",
    "broiler": "#e39338",
    "facilities":"#2c2c2c",
    "corn":"#e3b338",
    "alfalfa":"#e2cbe5",
    "soy":"#4f873b",
    "cows":"#bbb9c8"
}
