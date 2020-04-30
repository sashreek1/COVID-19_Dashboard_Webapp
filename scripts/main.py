import requests 
from bs4 import BeautifulSoup 
import numpy as np
import pandas as pd
import geopandas as gpd
import scripts.state_list as state_list
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Category20
from bokeh.plotting import figure
from bokeh.transform import cumsum
from math import pi
import folium
import branca.colormap as cm
import threading
from multiprocessing import Pool
from bokeh.embed import components
from apscheduler.schedulers.background import BackgroundScheduler


extract_contents = lambda row: [x.text.replace('\n', '') for x in row] 
site = 'https://www.mohfw.gov.in/'
df_data = None
SHORT_HEADERS = ['SNo', 'State', 'Total_Confirmed', 'Cured', 'Death'] 

########################## Get data from ministry of health #####################################
def get_data():
	print("Process 1")
	df_1 = None
	df_2 = None
	df_data = None
	df_data = pd.read_pickle("df_data.pkl")
	response = requests.get(site).content
	soup = BeautifulSoup(response, 'html.parser') 
	header = extract_contents(soup.tr.find_all('th')) 

	stats = [] 
	all_rows = soup.find_all('tr') 
	for row in all_rows: 
		stat = extract_contents(row.find_all('td')) 
		if stat: 
			if len(stat) == 4: 
				stat = ['', *stat] 
				stats.append(stat) 
			elif len(stat) == 5:
				stat[1] = stat[1].replace(" and "," & ")
				stat[1] = stat[1].replace("Delhi","NCT of Delhi")
				stat[1] = stat[1].replace("Telengana","Telangana")
				stat[1] = stat[1].replace("Arunachal","Arunanchal")
				stat[1] = stat[1].replace("Andaman & Nicobar Islands","Andaman & Nicobar Island")
				stat[1] = stat[1].replace("Dadra & Nagar Haveli","Dadara & Nagar Havelli")

				stats.append(stat) 
	prev_sno = int(stats[-2][0])
	stats[-1][1] = "Total Cases"
	stats[-1][0] = str(prev_sno+1)
	objects = [] 
	for row in stats : 
		objects.append(row[1]) 
		row[2]=(row[2].strip("#")).strip("*")

	
	y_pos = np.arange(len(objects)-1) 

	data = stats[0:-1]
	data.insert(0,["SNo","State","Total_Confirmed","Cured","Death"])

	performance = [] 
	for row in stats :
		try:
			performance.append(int((row[2].strip("#")).strip("*")))
		except:
			performance.append(int((row[2].strip("#")).strip("*")))

	for i in range(len(data)):
		for j in range(len(data[i])):
			if data[i][j].isdigit():
				data[i][j] = int(data[i][j])


	column_names = data.pop(0)
	df_1 = pd.DataFrame(data, columns=column_names)
	
	column_names = ["SNo_def","State_def","Total-Confirmed_def","Cured_def","Death_def"]
	df_2 = pd.DataFrame(state_list.stats_edit, columns=column_names)
	
	df_data = pd.merge(left=df_2, right=df_1, how='left', left_on='State_def', right_on='State')
	
	net_results = []
	net_results.append(int((stats[-1][2].strip("#")).strip("*")))
	net_results.append(int((stats[-1][3].strip("#")).strip("*")))
	net_results.append(int((stats[-1][4].strip("#")).strip("*")))

	df_data = df_data.append({'State' : 'Total Cases' , 'Total_Confirmed' : net_results[0],'Cured' : net_results[1],'Death' : net_results[2]}, ignore_index=True)

	df_data.to_pickle("df_data.pkl")

	################################### Plot bar chart ##################################

def plot_bar():
	print("Process 2")
	df_data = pd.read_pickle("df_data.pkl")
	b = figure(
  	y_range=df_data["State"].dropna().tolist()[:-1],
  	title = '',
  	x_axis_label ='Cases',
  	plot_width=600,
  	plot_height=700,
  	tools="pan,box_select,zoom_in,zoom_out,save,reset")
	b.hbar(y=df_data["State"].dropna().tolist()[:-1],
    right=df_data["Total_Confirmed"].dropna().tolist()[:-1],
    left=0,
    height=0.4,
    color='red',
    fill_alpha=0.5,
    )
	b.yaxis.major_label_text_color = "white"
	b.xaxis.major_label_text_color = "white"
	b.background_fill_color = "#1c1c1c"
	b.border_fill_color = "#1c1c1c"
	b.xgrid.visible = False
	b.ygrid.visible = False

	script_bar, div_bar = components(b)

	f = open("app/templates/bar_div.html", "w")
	f.write(div_bar)
	f.close()
	
	f = open("app/templates/bar_script.html", "w")
	f.write(script_bar)
	f.close()
	
	 
	############################### Plot pie chart ####################################### 
def plot_pie():
	print("Process 3")
	x = {}
	df_data = pd.read_pickle("df_data.pkl")
	objects = df_data["State"].dropna().tolist()[:-1]
	performance = df_data["Total_Confirmed"].dropna().tolist()[:-1]
	for i in range(len(objects)):
		x[objects[i]] = performance[i]
	data = pd.Series(x).reset_index(name='value').rename(columns={'index':'state'})
	data['angle'] = data['value']/data['value'].sum() * 2*pi
	data.insert (1,"percentage_of_cases", round((data['value']/data['value'].sum())*100,2))
	c = Category20[20]
	lst1 = []
	for i in range(len(x)):
		lst1.append(c[abs(i-19)])
	data['color'] = tuple(lst1)

	pie = figure(plot_height=550,plot_width=620, title="",
           tools="hover,pan,box_select,zoom_in,zoom_out,save,reset", tooltips="@state: @percentage_of_cases%", x_range=(-0.5, 1.0))

	pie.wedge(x=0, y=1, radius=0.5,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', source=data)

	pie.axis.axis_label=None
	pie.axis.visible=False
	pie.grid.grid_line_color = None
	pie.background_fill_color = "#1c1c1c"
	pie.border_fill_color = "#1c1c1c"

	script_pie, div_pie = components(pie)
	
	f = open("app/templates/pie_div.html", "w")
	f.write(div_pie)
	f.close()
	
	f = open("app/templates/pie_script.html", "w")
	f.write(script_pie)
	f.close()

	######################### plot shape files ###########################################

def setup_map():
	df_data = pd.read_pickle("df_data.pkl")
	fp = "Igismap/Indian_States.shp"
	map_df = gpd.read_file(fp)
	map_df.insert (1,"state_name", map_df["st_nm"])
	df_data = df_data.fillna(0)
	merged = map_df.set_index('st_nm').join(df_data.set_index('State_def'))

	merged['percentage_cured'] = merged.apply(lambda row: round((row.Cured/row.Total_Confirmed)*100,2) if row.Total_Confirmed>0 else 0, axis = 1) 
	x_map=merged.centroid.x.mean()
	y_map=merged.centroid.y.mean()
	

	return merged, x_map, y_map

def plot_map(arguments):

	# Plot the number of confirmed cases
	colour = arguments[0]
	category = arguments[1]
	merged, x_map, y_map = setup_map()
	mymap = folium.Map(location=[y_map, x_map], zoom_start=4,tiles=None)
	folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(mymap)
	myscale = (merged[category].quantile((0,0.1,0.75,0.9,0.98,1))).tolist()
	folium.Choropleth(
	 geo_data=merged,
	 name='choropleth',
	 data=merged,
	 columns=['SNo_def',category],
	 key_on="feature.properties.SNo_def",
	 fill_color=colour,
	 threshold_scale=myscale,
	 fill_opacity=1,
	 line_opacity=0.2,
	 legend_name='Number of cases',
	 smooth_factor=0
	).add_to(mymap)
	style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}
	highlight_function = lambda x: {'fillColor': '#000000', 
	                                'color':'#000000', 
	                                'fillOpacity': 0.50, 
	                                'weight': 0.1}
	
	if category == "Total_Confirmed":
		NIL = folium.features.GeoJson(
		    merged,
		    style_function=style_function, 
		    control=False,
		    highlight_function=highlight_function, 
		    tooltip=folium.features.GeoJsonTooltip(
		        fields=['state_name',category],
		        aliases=['State: ','Number of cases: '],
		        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
		    )
		)
	if category == "percentage_cured":
		NIL = folium.features.GeoJson(
		    merged,
		    style_function=style_function, 
		    control=False,
		    highlight_function=highlight_function, 
		    tooltip=folium.features.GeoJsonTooltip(
		        fields=['state_name',category],
		        aliases=['State: ','Number of deaths: '],
		        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
		    )
		)
	if category == "Death":
		NIL = folium.features.GeoJson(
		    merged,
		    style_function=style_function, 
		    control=False,
		    highlight_function=highlight_function, 
		    tooltip=folium.features.GeoJsonTooltip(
		        fields=['state_name',category, 'percentage_cured'],
		        aliases=['State: ','Cured Cases: ','Percentage Cured'],
		        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
		    )
		)

	mymap.add_child(NIL)
	mymap.keep_in_front(NIL)
	folium.LayerControl().add_to(mymap)
	confirmed_map = mymap._repr_html_()
	
	f = open("app/templates/"+category+".html", "w")
	f.write(confirmed_map)
	f.close()

def plot_all_maps():
	print("Process 4")
	p = Pool()
	arguments_passed = [['YlOrRd','Total_Confirmed'],['YlGnBu','percentage_cured'],['OrRd','Death']]
	p.map(plot_map,arguments_passed)

scheduler = BackgroundScheduler()

scheduler.add_job(get_data, 'interval', hours = 2, minutes=5)
scheduler.add_job(plot_bar, 'interval', hours = 2, minutes=6)
scheduler.add_job(plot_pie, 'interval', hours = 2, minutes=7)
scheduler.add_job(plot_all_maps, 'interval', hours = 2, minutes=8)

scheduler.start()