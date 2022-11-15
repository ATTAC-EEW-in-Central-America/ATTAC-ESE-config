#from seiscomp import core
from datetime import datetime
import dash, os, sys, glob, json
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import timedelta
import pandas as pd
import numpy as np
from pandas.io.json import json_normalize
from dash.dependencies import Input,Output,State
import plotly.graph_objs as go
import plotly.express as px
import fnmatch
#sys.path.insert(0, '/home/cam/EEW/sceewv/sceewv/')
#sys.path.append("/home/cam/EEW/sceewv/sceewv/")

external_stylesheets=[dbc.themes.BOOTSTRAP]
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

def numDays(timeRange):
	dic = {"d":"1","w":"7","m":"30"}
	ID = list(filter(str.isalpha, str(timeRange)))
	num = list(filter(str.isdigit, str(timeRange)))
	numDays = int(dic[ID[0]])*int(num[0])
	return numDays

def prepare_data(timeRange):
	today = datetime.today().date()
	yest = today-timedelta(1)
	dicts = []
	days = []
	json_path = "/opt/seiscomp/share/scqcalert"
	num_days = numDays(timeRange)
	for i in range(num_days):
		days.append(yest-timedelta(days=i))
	for day in days:
		tt = day.timetuple()
		jday = tt.tm_yday
		for root, dirs, files in os.walk(json_path):
			for item in fnmatch.filter(files, "*."+str(jday)):
				fil = os.path.join(root, item)
				with open(os.path.join(os.getcwd(), fil), 'r') as f:
					filedata = f.read()
					if '\n}{\n' in filedata:
						filedata = filedata.replace('\n}{\n', ',\n')
						with open(os.path.join(os.getcwd(), fil), 'w') as f:
							f.write(filedata)
				with open(os.path.join(os.getcwd(), fil), 'r') as f:
					d = json.load(f)
					metricnum = len(d["alerts"])
					types = []
					for i in range(metricnum):
						types.append(d["alerts"][i]["metric"])
						alertnum = len(d["alerts"][i]["values"])
						d["alerts"][i]["alertnum"] = alertnum
						d["alerts"][i]["types"] = d["alerts"][i]["metric"]
					d_metricnum = {'metric':"alert_types",'endtime':None,'values':None,'alertnum':metricnum,'starttime':None,'types':types}
					d["alerts"].append(d_metricnum)
					d['jday'] = day
					d['net'] = d['mseedid'][0:2]
					dicts.append(d)
	input_data = json_normalize(dicts, record_path='alerts',meta=['mseedid','jday','net'])
	data = []
#	#default dataframe
#	for i in days:
#		for j in input_data["mseedid"]:
#			data.append([i,j])
#	data = pd.DataFrame(data,columns=['jday','mseedid'])
	SORT = ["default", "net-sta", "total ascending", "max ascending", "total descending"]
	SORT_default = "default"
	##default visualization
	MET = input_data["metric"].unique()
	MET_default = "alert_types"
	df_default = input_data[input_data['metric'] == MET_default]
	#df_default = df_default.sort_values(by=["alertnum"], ascending=True)
	#df_default = df_default.reset_index(drop=True)
	TIME = ["1d", "2d", "3d", "4d", "5d", "1w", "2w", "3w", "1m", "2m"]
#	for i in range(30):
#		TIME.append(i+1)
	TIME_default = "1w"
	return input_data, MET, MET_default, df_default, SORT, SORT_default, TIME, TIME_default

input_data, MET, MET_default, df_default, SORT, SORT_default, TIME, TIME_default = prepare_data("1w")


#create layout menu with metric and default visualization of dashboard
#app.layout = html.Div([

# html.H1('Dashboard qc summary'),
# 
# html.Div([

# html.Div([
#  html.H3('Select Time'),
#  dcc.Dropdown(
#  id='TIME_dropdown',
#  options=[{'label': i, 'value': i} for i in TIME],
#  value = TIME_default,
#  style={'width': '80%', 'display': 'inline-block'}),
# ], className="three columns"),

# html.Div([
#  html.H3('Select metric'),
#  dcc.Dropdown(
#  id='MET_dropdown',
#  options=[{'label': i, 'value': i} for i in MET],
#  value = MET_default,
#  style={'width': '80%', 'display': 'inline-block'}),
# ], className="three columns"),

# html.Div([
#  html.H3('Select sort order'),
#  dcc.Dropdown(
#  id='SORT_dropdown',
#  options=[{'label': i, 'value': i} for i in SORT],
#  value = SORT_default,
#  style={'width': '80%', 'display': 'inline-block'}),
# ], className="three columns"),

# ], className="row"),

# html.Div([
# html.Div([
##  html.H3('Left'),
#  dcc.Graph(id='heatmap')
##  style={'width': '100%','height':'100%'}),
#  ], className="six columns"),

# html.Div([
##  html.H3('Right'),
#  dcc.Graph(id='histo'),
#  ], className="six columns"),
# ], className="row")

#])


#app.layout = html.Div([
# dcc.Location(id='url', refresh=False),
# html.Div(id='page-content')
#])

index_page = html.Div([
    dcc.Link('Go to scqcalert', href='/scqcalert'),
    html.Br(),
    dcc.Link('Go to event', href='/event'),
    html.Br(),
    dcc.Link('Go to events', href='/events'),
    html.Br(),
    dcc.Link('Go to stations', href='/stations'),
    html.Br(),
    dcc.Link('Go to networks', href='/networks'),
    html.Br(),
    dcc.Link('Go to eewd', href='/eewd'),
])



scqcalert_layout = html.Div([
 html.H1('scqcalert NET_name'),
 dbc.Row(
  [
#   dbc.Col(html.Div('Select Time')),
    dbc.Col([
     html.H4('Select Time'),html.H6('"d" day, "w" week and "m" month'),
     dcc.Dropdown(
     id='TIME_dropdown',
     options=[{'label': i, 'value': i} for i in TIME],
     value = TIME_default,
     style={'width': '80%', 'display': 'inline-block'})]),

    dbc.Col([
     html.H4('Select metric'),html.H6('"alert_types" includes the number of all metrics with alerts'),
     dcc.Dropdown(
     id='MET_dropdown',
     options=[{'label': i, 'value': i} for i in MET],
     value = MET_default,
     style={'width': '80%', 'display': 'inline-block'})]),

    dbc.Col([
     html.H4('Select sort order'),html.H6('Please select "default" to unblock the other dropdowns'),
     dcc.Dropdown(
     id='SORT_dropdown',
     options=[{'label': i, 'value': i} for i in SORT],
     value = SORT_default,
     style={'width': '80%', 'display': 'inline-block'})]),
  ]
 ),
 dbc.Row(
  [
   dbc.Col(
   dcc.Graph(id='heatmap'),width="7"),
   dbc.Col(
   dcc.Graph(id='histo'),width="5"),
  ],
 ),
    html.Div(id='scqcalert-content'),
    html.Br(),
#    dcc.Link('Go to Page 2', href='/page-2'),
#    html.Br(),
    dcc.Link('Go back to home', href='/'),
])

event_layout = html.Div([
 html.H1('event'),
 dcc.Link('Go back to home', href='/')
])

events_layout = html.Div([
 html.H1('events'),
 dcc.Link('Go back to home', href='/')
])

stations_layout = html.Div([
 html.H1('stations'),
 dcc.Link('Go back to home', href='/')
])

networks_layout = html.Div([
 html.H1('networks'),
 dcc.Link('Go back to home', href='/')
])

eewd_layout = html.Div([
 html.H1('eewd'),
 dcc.Link('Go back to home', href='/')
])

## Update the index
#@callback(dash.dependencies.Output('page-content', 'children'),
#			[dash.dependencies.Input('url', 'pathname')])
#def display_page(pathname):
#	if pathname == '/scqcalert':
#		return scqcalert_layout
#	elif pathname == '/event':
#		return event_layout
#	elif pathname == '/events':
#		return events_layout
#	elif pathname == '/stations':
#		return stations_layout
#	elif pathname == '/networks':
#		return networks_layout
#	elif pathname == '/eewd':
#		return eewd_layout
#	else:
#		return index_page

@callback(
	Output('MET_dropdown','options'),
	[Input('SORT_dropdown','value'),Input('MET_dropdown','value')]
	)
def update_dropdown(input_sort,input_met):
	if input_sort == 'default':
		return [dict(label=i, value=i) for i in MET]
	else:
		return [dict(label=input_met, value=input_met)]

@callback(
	Output('MET_dropdown', 'value'),
	Input('MET_dropdown', 'value'))
def set_dropdown_value(input_met):
	return input_met



@callback(
	Output('TIME_dropdown','options'),
	[Input('SORT_dropdown','value'),Input('TIME_dropdown','value')]
	)
def update_dropdown(input_sort,input_time):
	if input_sort == 'default':
		return [dict(label=i, value=i) for i in TIME]
	else:
		return [dict(label=input_time, value=input_time)]

@callback(
	Output('TIME_dropdown', 'value'),
	Input('TIME_dropdown', 'value'))
def set_dropdown_value(input_time):
	return input_time


#@callback(
#	Output('display-selected-values', 'children'),
#	Input('MET_dropdown', 'value'),
#	Input('SORT_dropdown', 'value'))
#def set_display_children(selected_MET, selected_SORT):
#	return u'{} is a city in {}'.format(selected_MET, selected_SORT,
#	)


@callback(
	[Output('heatmap','figure'),Output('histo','figure')],
	[Input('MET_dropdown','value'),Input('SORT_dropdown','value'),Input('TIME_dropdown','value')]
	)

#def clean_data(value):
#	# some expensive clean data step
#	cleaned_df =input_data[input_data['metric'] == value][['jday','mseedid','alertnum']]
#	# more generally, this line would be
#	# json.dumps(cleaned_df)
#	return cleaned_df.to_json(date_format='iso', orient='split')

# Actualizar heatmap despues de seleccionar las metricas

def multi_output(input_metric,input_sort,input_time):
	input_data, MET, MET_default, df_default, SORT, SORT_default, TIME, TIME_default = prepare_data(input_time)
	heatmap_data = input_data[input_data['metric'] == input_metric][['jday','mseedid','alertnum','net','types']]
#	heatmap_data = pd.merge(data,heatmap_data, on=['jday','mseedid'],how='outer').fillna(0)
	maxsale = heatmap_data[heatmap_data['alertnum']==heatmap_data['alertnum'].max()]
	maxsale = maxsale.reset_index()

	order_vec = []
	if input_sort == "net-sta":
		alerts_sta = heatmap_data.groupby(['mseedid'])['alertnum'].sum().reset_index()
		stas_innet = heatmap_data.groupby(['net'])['mseedid'].count().reset_index()
		dic = []
		for ind in alerts_sta.index:
			for ind2 in stas_innet.index:
				if alerts_sta["mseedid"][ind][0:2] == stas_innet['net'][ind2]:
					n_alerts_sta = alerts_sta["alertnum"][ind]
					n_stas_innet = stas_innet["mseedid"][ind2]
					num_sort = n_stas_innet*1000 + n_alerts_sta
					d_temp = {"sta":alerts_sta['mseedid'][ind],"num":num_sort}
					dic.append(d_temp)
		df = pd.DataFrame(dic)
		df = df.sort_values(by=["num"],ascending=True)
		df = df.reset_index(drop=True)
		order_vec = df['sta']
	if input_metric == "alert_types":
		barname = "Number types of alerts"
		xname = "Sum of alert types during selected period"
		hovertext = heatmap_data['types']
	else:
		hovertext = heatmap_data['types']
		barname = "Number of alerts"
		xname = "Sum of alerts during selected period"
	if input_sort == "default":
		input_sort = "trace"
	elif input_sort == "net-sta":
		input_sort = "array"

#	for index, row in heatmap_data.iterrows():
#		k = row['net']
#		n_stas_innet = sum(x == k for x in heatmap_data['net'])
#		n_alerts_sta = 0
#		k = row['mseedid']
#		for ind in heatmap_data.index:
#			if heatmap_data['mseedid'][ind] == k:
#				n_alerts_sta += heatmap_data['alertnum'][ind]
#		for idex2, row2 in heatmap_data.iterrows():
#			if row2['mseedid'] == k:
#				n_alerts_sta += row2['alertnum']
#		n_alerts_sta = row['alertnum']
#		num_sort = n_stas_innet*1000 + n_alerts_sta
#		d_temp = {"sta":row["mseedid"],"num":num_sort}
#		dic.append(d_temp)

	heatmap = go.Figure(
		data = [
			go.Heatmap(x=heatmap_data['jday'],
			y=heatmap_data['mseedid'],
			z=heatmap_data['alertnum'],
			xgap = 2,
			ygap = 2,
			colorscale='Viridis',
#			colorbar = {'yanchor':'middle','xanchor':'center'}
			colorbar = {'title':barname,'title.side':'right','len':0.5,'x':1,'xanchor':'left','yanchor':'bottom'},
			hovertemplate = '<i>Station</i>: %{y}<br><i>Day</i>: %{x}<br><i>Number</i>: %{z}<br><i>Alerts</i>: %{hovertext}<extra></extra>',
			hovertext=hovertext,
			)],
		layout = go.Layout(
#			title="Heatmap",
#			responsive= True,
#			autosize= True,
#			width=1000,
			height=1500,
			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': input_sort, 'categoryarray':order_vec},
#			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': 'array','categoryarray':order_vec },
#			yaxis = sort,
			xaxis = {'nticks':len(heatmap_data['jday'].unique()),'tickformat':'%b %d%\n%Y','side':'top'})
		)
#hovertext=heatmap_data['net']
	histo = go.Figure(
		data = [
			go.Bar(y=heatmap_data['mseedid'],x=heatmap_data['alertnum'],orientation='h',
			hovertemplate = '<i>Station</i>: %{y}<br><i>Number</i>: %{x}<br><i>Day</i>: %{hovertext}<extra></extra>',
			hovertext=heatmap_data['jday'],
			showlegend = False)],
		layout = go.Layout(
#			title="Histogram",
#			responsive= True,
#			autosize= True,
#			width=1000,
			height=1500,
			yaxis = {'side':'right','title':'Stations','visible':True,'showticklabels':True,'categoryorder': input_sort,'categoryarray':order_vec},
#			yaxis = {'side':'right','title':'Stations','visible':True,'showticklabels':True,'categoryorder': "array",'categoryarray':order_vec },
			xaxis = {'title.text':xname,'side':'top'})
		)
	return heatmap, histo

#@callback(
#	[Output('heatmap','figure'),Output('histo','figure')],
#	[Input('SORT_dropdown','value')]
#	)

#def multi_output(value):
#	heatmap = go.Figure(
#		data = [
#			go.Heatmap(x=heatmap_data['jday'],
#			y=heatmap_data['mseedid'],
#			z=heatmap_data['alertnum'],
#			xgap = 2,
#			ygap = 2,
#			colorscale='Viridis',
##			colorbar = {'yanchor':'middle','xanchor':'center'}
#			)],
#		layout = go.Layout(
#			title="Heatmap",
#			width=900,
#			height=1500,
#			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': value },
#			xaxis = {'side':'top'})
#		)
#	histo = go.Figure(
#		data = [
#			go.Bar(y=heatmap_data['mseedid'],x=heatmap_data['alertnum'],orientation='h')],
#		layout = go.Layout(
#			title="Histogram",
#			width=900,
#			height=1500,
#			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': value },
#			xaxis = {'side':'top'})
#		)
#	return heatmap, histo


#@callback(
#	Output('heatmap','figure'),
#	Input('MET_dropdown','value')
#	)
#def update_figure(value):
#	heatmap_data = input_data[input_data['metric'] == value][['jday','mseedid','alertnum']]
##	heatmap_data = pd.merge(data,heatmap_data, on=['jday','mseedid'],how='outer').fillna(0)
#	maxsale = heatmap_data[heatmap_data['alertnum']==heatmap_data['alertnum'].max()]
#	maxsale = maxsale.reset_index()

#	heatmap = go.Figure(
#		data = [
#			go.Heatmap(x=heatmap_data['jday'],
#			y=heatmap_data['mseedid'],
#			z=heatmap_data['alertnum'],
#			xgap = 2,
#			ygap = 2,
#			colorscale='Viridis',
##			colorbar = {'yanchor':'middle','xanchor':'center'}
#			)],
#		layout = go.Layout(
#			title="Heatmap",
#			width=900,
#			height=1500,
##			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': 'total ascending' },
#			yaxis = {'categoryorder': 'total ascending'},
#			xaxis = {'side':'top'})
#		)
#	return heatmap


#@callback(
#	Output('histo','figure'),
#	Input('MET_dropdown','value')
#	)
#def update_figure2(value):
#	heatmap_data = input_data[input_data['metric'] == value][['jday','mseedid','alertnum']]
##	heatmap_data = pd.merge(data,heatmap_data, on=['jday','mseedid'],how='outer').fillna(0)
#	maxsale = heatmap_data[heatmap_data['alertnum']==heatmap_data['alertnum'].max()]
#	maxsale = maxsale.reset_index()

#	histo = go.Figure(
#		data = [
#			go.Bar(y=heatmap_data['mseedid'],x=heatmap_data['alertnum'],orientation='h')],
#		layout = go.Layout(
#			title="Histogram",
#			width=900,
#			height=1500,
#			yaxis = {'title':'Stations','visible':True,'showticklabels':True,'categoryorder': 'total ascending' },
#			xaxis = {'side':'top'})
#		)
#	return histo

#if __name__ == '__main__':
## app.run_server(debug=True)
# app.run_server(debug=True, use_reloader=False, host='0.0.0.0', port='8050')


