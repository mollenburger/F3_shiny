from shared import fullchains, fs_counties
from utils.data_utils import filter_chains
from utils.map_utils import build_chloro, state_outline, fill_gradients, build_flow_data, make_geom_chloro, make_geom_flow
import plotnine as p9
import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, ui, render

# Define UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                id = "crop", label = "Select crop", 
                choices= {"corn_direct":"Corn - direct", "corn_ddgs":"Corn - as DDGS", "soy":"Soy"},
                selected = "Corn - direct"),
            ui.input_checkbox_group("com", "Select destination commodities", 
                choices = {"hog":"Hogs","broiler":"Broiler chickens","ddgs":"Ethanol", "cattle":"Cattle on feed"}
                ),
            ui.input_checkbox_group(id = "arcs", label = "Flow arcs to display", 
                choices = { 0:"Stage 1", 1:"Stage 2"}),
            ui.input_switch("arcsize", "Scale flow arcs by flow volume", value = True),
            ui.input_select(id = "filter", label = "Select source counties to fileter",
                choices = {"none":"No filter", "fs_counties":"Upper Mississippi Foodscape"}, selected = "none"),
        ),
        ui.output_plot("chloro")
    )
        )
        

def server(input: Inputs, output: Outputs, session: Session):
    @reactive.effect
    def _():
        x = input.crop()
        if x == "corn_direct":
            ui.update_checkbox_group("arcs", choices={0:"Stage 1"})
            ui.update_checkbox_group("com", choices = {"hog":"Hogs","broiler":"Broiler chickens", "cattle":"Cattle on feed", "ddgs":"Ethanol"} )
        else:
            ui.update_checkbox_group("com", choices = {"hog":"Hogs","broiler":"Broiler chickens", "cattle":"Cattle on feed"} )
            ui.update_checkbox_group("arcs", choices={0:"Stage 1", 1:"Stage 2"})
    @render.plot    
    def chloro():
        if input.filter() == "none":
            chain_data = fullchains
        else:
            counties = pd.read_csv('data/'+input.filter()+'.csv')['FIPS'].tolist()
            chain_data = filter_chains(fullchains, counties, "source_FIPS_0")
        flowarcs = []
        if len(input.arcs())>0:
            if input.crop() == "corn_direct":
                steps = 1
            else: steps = 2
            if input.arcsize():
                arc_size = "scaled"
                flowarcs.append(p9.scale_size_continuous(range = [0,1]))
            else: arc_size = "fixed"
            flows_to = list(input.com())
            flows = build_flow_data(chain_data[input.crop()], flows_to, steps)
            stages = list(map(int,input.arcs()))
            if len(input.arcs()) ==1:
                for com in input.com():
                    flowarcs.append(make_geom_flow(flows['flowarcs'], com, stages[0], size = arc_size))
            elif len(input.arcs()) ==2:
                for com in input.com():
                    flowarcs.append(make_geom_flow(flows['flowarcs'], com, 1, size = arc_size))
                    flowarcs.append(make_geom_flow(flows['flowarcs'], com, 0, color = "#2c2c2c", size = arc_size))       
        if input.com():
            mapdata = build_chloro(chain_data, input.crop(), "flow_kg_0",input.com())
            basemap = make_geom_chloro(mapdata, input.com())
        else: 
            basemap = 0
        if input.crop() == "soy":
            colorval = "soy"
        else: colorval = "corn"
        chloromap = (p9.ggplot()
            + basemap
            + state_outline
            + flowarcs
            + p9.scale_fill_manual(values = fill_gradients[colorval])
            + p9.theme_void()
            + p9.theme(figure_size=(10,6), 
                        panel_background=p9.element_rect(fill="white"),
                        legend_position="none"))
        return chloromap


app = App(app_ui, server)