#!/usr/bin/env python
"""
Copyright (C) by ETHZ/SED

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

Author of the Software: Camilo Munoz
"""

from dash import Dash, dcc, html, Input, Output, callback, dash_table, no_update
import json, glob, os, datetime
import dash_bootstrap_components as dbc
import pandas as pd
from pandas import json_normalize
from operator import itemgetter
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.figure_factory as ff
import math
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import plotly.io as pio
import numpy as np
from obspy import read_events
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import configparser


external_stylesheets=[dbc.themes.BOOTSTRAP]
config = configparser.RawConfigParser()
config.read("/opt/seiscomp/share/sceewv/apps.cfg")
cfg = dict(config.items('events'))
mapbox_access_token = open(cfg['mapboxtoken']).read()
extQuery = cfg['extquery']
extQuery = False if extQuery == 'False' else extQuery
extQuery = True if extQuery == 'True' else extQuery
fdsnwsName = cfg['fdsnwsname']
fdsnwsClient = cfg['fdsnwsclient']
agencia = cfg['agency']
deltaMin = int(cfg['deltatime'])
deltaDist = int(cfg['deltadist'])
validMagTypes = cfg['magtypes'].split(",")
lat_min = float(cfg['latmin'])
lat_max = float(cfg['latmax'])
lon_min = float(cfg['lonmin'])
lon_max = float(cfg['lonmax'])
json_path = cfg['jsonpath']
distInt = int(cfg['distint'])
fpStatus = cfg['fpstatus']
fpStatus = False if fpStatus == 'False' else fpStatus
fpStatus = True if fpStatus == 'True' else fpStatus
deltaDays = int(cfg['deltadays'])
minMag = float(cfg['minmag'])
maxMag = float(cfg['maxmag'])
cmaplat = float(cfg['cmaplat'])
cmaplon = float(cfg['cmaplon'])
zoomap = float(cfg['zoomap'])

def super(string):
	superscript_map = {
		"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
		"7": "⁷", "8": "⁸", "9": "⁹", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ",
		"e": "ᵉ", "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ᶦ", "j": "ʲ", "k": "ᵏ",
		"l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "q": "۹", "r": "ʳ",
		"s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ",
		"z": "ᶻ", "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ", "E": "ᴱ", "F": "ᶠ",
		"G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ", "M": "ᴹ",
		"N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "Q": "Q", "R": "ᴿ", "S": "ˢ", "T": "ᵀ",
		"U": "ᵁ", "V": "ⱽ", "W": "ᵂ", "X": "ˣ", "Y": "ʸ", "Z": "ᶻ", "+": "⁺",
		"-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾"}
	trans = str.maketrans(''.join(superscript_map.keys()),''.join(superscript_map.values()))
	return string.translate(trans)

def externalQuery(startTime,endTime,magValue,lat_min,lat_max,lon_min,lon_max):
	client = Client(fdsnwsClient)
	#client = Client(fdsnwsClient,debug=True)
	if magValue[1] < 9.5:
		maxMag = magValue[1]+0.5
	else:
		maxMag = magValue[1]
	cat = client.get_events(starttime=startTime,endtime=endTime,
	                        minmagnitude=magValue[0]-0.5,maxmagnitude=maxMag,
						    minlatitude=max([-90,lat_min-1]),maxlatitude=min([90,lat_max+1]),
						    minlongitude=max([-180,lon_min-1]),maxlongitude=min([180,lon_max+1]))	
	return cat

def compExt(EvalOri,extCat,prefOri):
	minute_delta = timedelta(minutes=deltaMin)
	degree_delta = deltaDist
	oriTime = UTCDateTime(prefOri["OriginTime"])
	oriLat = prefOri["latitude"]
	oriLon = prefOri["longitude"]
	for event in extCat.events:
		for origin in event.origins:
			extTime = origin.time
			deltaTime = timedelta(seconds=abs(extTime-oriTime))
			deltaLat = abs(origin.latitude - oriLat)
			deltaLon = abs(origin.longitude - oriLon)
			if deltaTime < minute_delta and deltaLat < degree_delta and deltaLon < degree_delta:
				EvalOri = 0
	return EvalOri

def ipe_allen2012_hyp(r, # hypocentral distance (km, float)
                      m, # magnitude (float)
                      a = 2.085,
                      b = 1.428,
                      c = -1.402,
                      d = 0.078,
                      s = 1,
                      m1=-0.209,
                      m2=2.042):
    rm = m1+m2*np.exp(m-5)
    I = a + b*m + c*np.log(np.sqrt(r**2 + rm**2))+s
    if r<50:
        I = a + b*m + c*np.log(np.sqrt(r**2 + rm**2))+d*np.log(r/50)+s
    return I # intensity (MMI, float)

def roman(num):
   res = ""
   table = [
      (10, "X"),
      (9, "IX"),
      (5, "V"),
      (4, "IV"),
      (1, "I")
   ]
   for cap, roman in table:
      d, m = divmod(num, cap)
      res += roman * d
      num = m
   if res == "":
      res == None
   return res

def prepare_data(startTime, endTime, magValue):
#	dictMag = []
	dictPref = []
	dictPlot = []
	Tp_vect = []
	Fp_vect = []
	Fn_vect = []
	fmt = '%Y-%m-%d %H:%M:%S'
	if extQuery:
		try:
			extCat = externalQuery(startTime,endTime,magValue,lat_min,lat_max,lon_min,lon_max)
		except Exception as e:
			print("Empty external query or external catalog not found")
			print(e)
			extCat = read_events()
			extCat.clear()

	for root, dirs, files in os.walk(json_path):
		length = len(root)
		try:
			dayPath = datetime.datetime.strptime(root[-11:length],'/%Y/%m/%d')
			dayPath = dayPath.date()
		except:
			continue
		if dayPath >= startTime and dayPath <= endTime:
			for item in files:
				# print(root)
				# print(item)
				checkExt = 0
				status = 1
				prefMagType = None
				prefMagVal = None
				EvalOri = None
				EvalMag = 1
				EvalEve = None
				mag = None
				regEval = 0
				magEval = 0
				fil = os.path.join(root, item)
				f = open(os.path.join(os.getcwd(), fil), 'r')
				creTime = []
				difOriTime = []
				dMag = []
				dPick = []
				tpAdd = []
				eewGMS = ""
				likelihoods = ""
				earlyMag = ""
				earlyDelay = ""
				delayEww = ""
				delayPtime = ""
				prefOriTime = None
				prefOriDepth = None
				data = json.load(f)
	#			dictMag.append(data)
				for iOri in range(len(data["origins"])):
					creTime.append(data["origins"][iOri]["CreationTime"])
					if data["prefOrigin"] == data["origins"][iOri]["ID"]:
						EvalOri = data["origins"][iOri]["EvaluationMode"]
						if EvalOri == 1 and extQuery:
							EvalOri = compExt(EvalOri,extCat,data["origins"][iOri])
							if EvalOri == 0:
								checkExt = 1
						lat = data["origins"][iOri]["latitude"]
						lon = data["origins"][iOri]["longitude"]
						if lat > lat_max or lat < lat_min or lon > lon_max or lon < lon_min:
							regEval = 1
							break
						prefOriTime = data["origins"][iOri]["OriginTime"]
						prefOriDepth = data["origins"][iOri]["depth"]
						data["origins"][iOri]["eventID"] = data["eventID"]
						prefOri = data["origins"][iOri]
	#					dictPref.append(data["origins"][iOri])
					try:
						lat = data["origins"][iOri]["latitude"]
						lon = data["origins"][iOri]["longitude"]
						for iMag in range(len(data["origins"][iOri]["mags"])):
							likelihood = 0
							eewCheck = 0
							magTime = data["origins"][iOri]["mags"][iMag]["CreationTime"]
							magType = data["origins"][iOri]["mags"][iMag]["type"]
							magVal = data["origins"][iOri]["mags"][iMag]["value"]
							if magType in validMagTypes:
								EvalMag = 0
								if "comments" in data["origins"][iOri]["mags"][iMag]:
									for icomm in range(len(data["origins"][iOri]["mags"][iMag]["comments"])):
										commentID = data["origins"][iOri]["mags"][iMag]["comments"][icomm]["ID"]
										commentText = data["origins"][iOri]["mags"][iMag]["comments"][icomm]["text"]
										if commentID == "likelihood":
											likelihood = commentText
										elif commentID == "EEW":
											eewCheck = 1
								dMag.append({"magTime":magTime,"magType":magType, "magVal":magVal, "likelihood":likelihood, "eewCheck":eewCheck, "lat":lat,"lon":lon})
							if data["prefMag"] == data["origins"][iOri]["mags"][iMag]["ID"]:
								mag = data["origins"][iOri]["mags"][iMag]["value"]
								if mag < magValue[0] or mag > magValue[1]:
									magEval = 1
									break
								prefMagType = magType
								prefMagVal = round(mag,2)
	#								dictPref[len(dictPref)-1]["Magnitude"] = "%s %s"%(magType,round(mag,2))
					except:
						pass
#						print("No mag in file %s origin %s" % (fil,data["origins"][iOri]["ID"]))
					try:
						for iPick in range(len(data["origins"][iOri]["picks"])):
							pickID = data["origins"][iOri]["picks"][iPick]["ID"]
							pCreaTime = data["origins"][iOri]["picks"][iPick]["CreationTime"]
							pTime = data["origins"][iOri]["picks"][iPick]["time"]
							dPick.append({"pickID":pickID,"pCreaTime":pCreaTime,"pTime":pTime})
					except:
						pass
#						print("No pick in file %s origin %s" % (f,data["origins"][iOri]["ID"]))

				if regEval == 1 or magEval ==1 or (prefMagType == None and prefMagVal == None):
					continue
				else:
					pass

				if EvalOri == 0 and EvalMag == 0:
					EvalEve = "Tp"
					status = 1
					Tp_vect.append(prefOriTime)
				elif EvalOri == 1 and EvalMag == 0:
					EvalEve = "Fp"
					# status = None
					status = fpStatus
					Fp_vect.append(prefOriTime)
				elif EvalOri == 0 and EvalMag == 1:
					EvalEve = "Fn"
					status = None
					Fn_vect.append(prefOriTime)
				elif EvalOri == 1 and EvalMag == 1:
					continue

				dictPref.append(prefOri)
				dictPref[len(dictPref)-1]["Magnitude"] = "%s %s"%(prefMagType,prefMagVal)
				dictPref[len(dictPref)-1]["EvalEve"]=EvalEve
				dictPref[len(dictPref)-1]["checkExt"]=checkExt

				oTime = datetime.datetime.strptime(prefOriTime, fmt)

#				Add dif time first origin
#				for i in range(len(creTime)):
#					try:
#						cTime = datetime.datetime.strptime(creTime[i], fmt)
#						difOriTime.append((cTime-oTime).total_seconds())
#					except:
#						pass
##						print("No creation time in %s" % f)
#				try:
#					difTime = min(difOriTime)
#				except:
#					difTime = None
#				d = {"type":"1OriTime","difTime":difTime,"prefOriTime":prefOriTime}
#				dictPlot.append(d)

				for i in range(len(dPick)):
#					If want to use creation timne use dPick[i]["pCreaTime"] if you want to use pick time dPick[i]["pTime"]
					pTime = datetime.datetime.strptime(dPick[i]["pTime"], fmt)
					difpTime = (pTime-oTime).total_seconds()
					dPick[i]["difpTime"] = difpTime
				dPickSort = sorted(dPick, key=itemgetter("difpTime"))
				pIDvec = []
				count = 0
				for i in range(len(dPickSort)):
					if dPickSort[i]["pickID"] not in pIDvec:
						pIDvec.append(dPickSort[i]["pickID"])
						count += 1
					if count == 4:
						tp = "4th P"
						Ptime = dPickSort[i]["difpTime"]
						if status:
							d = {"type":tp,"difTime":-Ptime,"prefOriTime":prefOriTime, "MMI":""}
							dictPlot.append(d)
						break
				if EvalMag == 1:
					dictPref[len(dictPref)-1]["Early mag"]="None"
					dictPref[len(dictPref)-1]["Loc error [km]"]="None"
					dictPref[len(dictPref)-1]["EEW-GM MMI"]="None"
					dictPref[len(dictPref)-1]["Delay 4th P [s]"]="None"
					dictPref[len(dictPref)-1]["Delay EEW [s]"]="None"
					dictPref[len(dictPref)-1]["Likelihood"]="None"
					dictPref[len(dictPref)-1]["EEW"]= "None"
				else:
					for i in range(len(dMag)):
						mTime = datetime.datetime.strptime(dMag[i]["magTime"], fmt)
						difMagTime = (mTime-oTime).total_seconds()
						dMag[i]["difMagTime"] = difMagTime
					dMagSort = sorted(dMag, key=itemgetter("difMagTime"))
					for i in range(len(dMagSort)):
						tp = dMagSort[i]["magType"]
						difTime = dMagSort[i]["difMagTime"]
						magVal = dMagSort[i]["magVal"]
						if tp not in tpAdd and tp in validMagTypes:
							if earlyMag != "":
								earlyMag += "\n"
								delayEww += "\n"
								delayPtime += "\n"
								eewGMS += "\n"
								likelihoods += "\n"
							tpAdd.append(tp)
							eewGM = ipe_allen2012_hyp((max([0.01, (difMagTime*3.3)**2-prefOriDepth**2]))**.5,magVal)
							if eewGM > 0:
								eewGM = roman(round(eewGM))
							else:
								eewGM = roman(round(0))
							eewTime = difTime-Ptime
							if status:
								d = {"type":tp,"difTime":eewTime,"prefOriTime":prefOriTime, "MMI":eewGM}
								dictPlot.append(d)
							likelihood = str(round(float(dMagSort[i]["likelihood"]),2))
							earlyMag += tp+" "+str(round(magVal,2))
							delayEww += str(eewTime)
							delayPtime += str(Ptime)
							eewGMS += str(eewGM)
							likelihoods += likelihood
							eewCheck = dMagSort[i]["eewCheck"]
							if eewCheck == 1:
								eewCheck = "✅"
							else:
								eewCheck = "❌"
							locPref = np.array((float(prefOri["latitude"]),float(prefOri["longitude"])))
							locOri = np.array((float(dMagSort[i]["lat"]),float(dMagSort[i]["lon"])))
							locErr = str(int(np.linalg.norm(locPref-locOri)*111.1))
#							r=10 # Ojo distancia utilizada para calcular EEW-GM
					dictPref[len(dictPref)-1]["Early mag"]=earlyMag
					dictPref[len(dictPref)-1]["Loc error [km]"]=locErr
					dictPref[len(dictPref)-1]["EEW-GM MMI"]=eewGMS
					dictPref[len(dictPref)-1]["Delay 4th P [s]"]=delayPtime
					dictPref[len(dictPref)-1]["Delay EEW [s]"]=delayEww
					dictPref[len(dictPref)-1]["Likelihood"]=likelihoods
					dictPref[len(dictPref)-1]["EEW"]=eewCheck

#	data_origins = json_normalize(dicts, record_path=['origins'],meta=['eventID'])
#	dataMag = json_normalize(dictMag, record_path=['origins','mags'],meta=['eventID', ['origins','CreationTime'],['origins','longitude'],['origins','latitude'],['origins','OriginTime'],['origins','ID']])
	dataPref = json_normalize(dictPref).drop(['CreationTime','mags','picks','ID'], axis='columns')
	dataPlot = json_normalize(dictPlot)
	dataPref.dropna(inplace=True)
	dataPref.reset_index(drop=True, inplace=True)
	dataPlot.dropna(inplace=True)
	dataPlot.reset_index(drop=True, inplace=True)
	dataPref['id']=dataPref['eventID']
	dataPref.set_index('id', inplace=True, drop=False)

#	print(dataPref)
#	data = data_origins.merge(data_mags, left_on="ID", right_on='origins.ID').drop('mags', axis='columns')
#	data_origins.to_csv("data_origins.csv")
#	data_mags.to_csv("data_mags.csv")
#	data.to_csv("data.csv")
	return dataPref, dataPlot, Fp_vect, Fn_vect, Tp_vect

today = date.today()
endTime = today
startTime = endTime - timedelta(days=deltaDays)
magValue = [minMag, maxMag]

dataPref,dataPlot,Fp_vect,Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)

initial_active_cell = {"row": 0, "column": 0, "column_id": "origins.ID"}
colors = ["royalblue","crimson","lightseagreen","orange","lightgrey"]
#tableColumns = ["OriginTime","eventID","Magnitude","EvalEve","Early mag","Delay"]
tableColumns = ["OriginTime","Magnitude","Early mag","Loc error [km]","Delay 4th P [s]","Delay EEW [s]","EEW-GM MMI","Likelihood","EEW","eventID"]


tab1_content = dcc.Graph(id='mag',config= {'displaylogo': False})

tab2_content = dbc.Row(
	[
	dbc.Col([
		dcc.Graph(id='histogram',config= {'displaylogo': False})
			],width=6),
	dbc.Col([
		dcc.Graph(id='pie',config= {'displaylogo': False})
			],width=6)
	],className="g-0"),

#tab2_content = dbc.Card(
#    dbc.CardBody(
#        [
#            html.P("This is tab 2!", className="card-text"),
#            dbc.Button("Don't click here", color="danger"),
#        ]
#    ),
#    className="mt-3",
#)

layout = html.Div(
	[
	html.Div(id='pageContent'),
		dbc.Row(
		[
			dbc.Col([
				dbc.Row(
				[
					dbc.Col([
						html.H4('Select Time Range'),html.H6('Please use calendar to select period of time'),
						dcc.DatePickerRange(
							id='date-range',
							minimum_nights=5,
							clearable=True,
							with_portal=True,
							start_date=startTime,
							end_date=endTime,
#							min_date_allowed=date(1995, 8, 5),
#							max_date_allowed=date(2017, 9, 19),
#							initial_visible_month=date(2017, 8, 5),
							style={'width': '80%', 'display': 'inline-block'}
						),
					]),
					dbc.Col([
						html.H4('Select Magnitude Range'),html.H6('Please use slider to select magnitude range'),
						dcc.RangeSlider(
							id='mag-range',
							min=0,
							max=10,
#							step=1,
							value=magValue,
							tooltip={"placement": "bottom", "always_visible": True}
						)
					]),
				],className="g-0"),
				dbc.Row(
				[
					dbc.Col([
						dcc.Graph(
							id='map',
							config= {'displaylogo': False},
							clickData={'points': [{'pointIndex': 0}]},
#							style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}
						), 
					]),
				],className="g-0"),
			],xs=6,sm=6,md=6,lg=6,xl=6,xxl=6),
			dbc.Col([
				dbc.Tabs(
				[
					dbc.Tab(label="History", tab_id="tab-1", tab_style={"marginLeft": "auto"}),
					dbc.Tab(label="Summary", tab_id="tab-2"),
				],
				id="tabs",
				active_tab="tab-1",
				),
				html.Div(id="content"),

#				dcc.Graph(id='mag',config= {'displaylogo': False}),

				dash_table.DataTable(
#					style_data={'lineHeight': '15px','whiteSpace': 'normal','height': 'auto'},
					id = 'tbl',
					data = dataPref.drop(['longitude','latitude'], axis='columns').to_dict('records'),
					sort_action='native',
					columns = [{'name': i, 'id': i} for i in tableColumns],
					export_format="csv",
#					editable=True,
					style_as_list_view=True,
					row_selectable="single",
#					fixed_rows={'headers': True},
#					page_size=20,
					page_action='none',
					style_table={'height':'400px', 'overflowY': 'auto'},
					# style_data={'whiteSpace': 'normal','height': 'auto'},
					selected_rows=[],
#					fill_width=True,
					style_cell={'minWidth': '5px', 'width': '10px', 'maxWidth': '180px','textAlign': 'center','whiteSpace': 'pre-line'},
					style_header={
						'backgroundColor': 'rgb(210, 210, 210)',
						'fontWeight': 'bold',
						'color': 'black',
						'textAlign': 'left'
					},
					active_cell=initial_active_cell
				),
			],xs=6,sm=6,md=6,lg=6,xl=6,xxl=6),
#		],no_gutters=True,className="g-0"),
		],className="g-0"),


#style={'display': 'inline-block', 'justify-content': 'center', 'width': '49%'}), 
#    ], style={'display': 'flex', 'justify-content': 'center'}), 
#html.Div(id='events-content'),
#html.Br(),
		dbc.Row(
		[
			dbc.Col(
			dcc.Link('Go back to home', href='/'),
			),
			dbc.Col(
			dcc.Link('Go to selected event', href='/event'),
			)
		])
	])

#Output('pageContent', 'children'),
@callback(Output("storeEventID", "data"),
		[Input('tbl', "derived_virtual_data"),
		Input('tbl', 'derived_virtual_selected_rows')])
def goEvent(data, selected_rows):
	if selected_rows:
		selected_data=data[selected_rows[0]]
		eventID = selected_data["eventID"]
		return eventID

@callback(Output("content", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-1":
        return tab1_content
    elif at == "tab-2":
        return tab2_content
    return html.P("This shouldn't ever be displayed...")


@callback(
    Output('tbl', 'style_data_conditional'),
    Input('tbl', 'active_cell')
)
def select_row(active_cell):
    return [{
        'if': { 'row_index': active_cell["row"] },
        'background_color': '#D2F3FF'},
          {
              'if': {
                'column_id': ['OriginTime', 'Magnitude'],
                'filter_query': '{EvalEve} = Fn'
              },
             'backgroundColor': '#ff9c9c',
             'color': 'white'
          },
          {
              'if': {
                'column_id': ['OriginTime', 'Magnitude'],
                'filter_query': '{EvalEve} = Fp'
              },
             'backgroundColor': '#fadc9b',
             'color': 'white'
          },
    ]


@callback(
    Output('tbl', 'data'),
    Input("date-range", 'start_date'),
    Input('date-range', 'end_date'),
    Input("mag-range", 'value')
    )
def update_table(start_date, end_date, magValue):
	startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	startTime = startTime.date()
	endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	endTime = endTime.date()
	try:
		dataPref, dataPlot, Fp_vect, Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)
	except:
		print("No data in selected period")
	data = dataPref.drop(['longitude','latitude'], axis='columns')
	for index, row in data.iterrows():
		if row["checkExt"] == 1:
			magMod = str(row["Magnitude"])+str(super(fdsnwsName))
			# magMod = str(row["Magnitude"])+'[%s](https://earthquake.usgs.gov/earthquakes/map/)'%fdsnwsName
			data.at[index, "Magnitude"] = magMod
	return data.to_dict('records')


@callback(
    Output('map', 'figure'),
    Input("date-range", 'start_date'),
    Input('date-range', 'end_date'),
    Input("mag-range", 'value'),
    Input("tbl", "derived_virtual_row_ids"),
#    Input("tbl", "derivedselected_row_ids"),
    Input("tbl", "active_cell"))
#    Input('year-slider', 'value'))
def update_graph(start_date, end_date, magValue, row_ids, active_cell):
##    dff = df[df['year'] == year_value]
    mapText="<b>Events chronological and geographical distribution from %s to %s </b><br> Agency: <b>%s</b>. Reference agency: <b>%s</b> and <b>%s</b>. <br> Dashboard creation time:%s"%(start_date,end_date,agencia,agencia,fdsnwsName,today)
    startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    startTime = startTime.date()
    endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    endTime = endTime.date()
    try:
        dataPref, dataPlot, Fp_vect, Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)
    except:
        print("No data in selected period")
#    row = dataPref.index[active_cell["row"]]
    size = []
    colors = [] 
    for i in range(len(dataPref['Magnitude'])):
       mag = dataPref['Magnitude'][i].split(" ")
       mag = abs(float(mag[1]))
       if 'row_id' in active_cell:
          if dataPref['eventID'][i] == active_cell['row_id']:
             size.append(500)
             colors.append('crimson')
          elif math.isnan(mag):
             size.append(10)
             colors.append('orangered')
          else:
             size.append(mag*40)
             colors.append('orangered')
       else:
          if i == 0:
             size.append(500)
             colors.append('crimson')
          elif math.isnan(mag):
             size.append(10)
             colors.append('orangered')
          else:
             size.append(mag*40)
             colors.append('orangered')
    lon = dataPref['longitude'].tolist()
    lat = dataPref['latitude'].tolist()
    fig = go.Figure(
        data = [
#        go.Scattergeo(
        #locationmode = 'USA-states',
        go.Scattermapbox(
        lon = lon,
        lat = lat,
        mode = 'markers',
#        zoom=3,
        marker = dict(
            opacity=0.5,
            color = colors,
#            line_color='rgb(40,40,40)',
            symbol="circle",
            size = size,
#            line_width=0.5,
            sizemode = 'area')
        )])
        
    fig.update_layout(
        #title_text='title',
        height=800,
        #width=200,
        #autosize=True,
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox = dict(
        accesstoken=mapbox_access_token,
        center = {'lat':cmaplat,'lon':cmaplon},
        zoom=zoomap,
#        style="carto-positron"
        style="mapbox://styles/olimac/cl30nl1kz003r14pp2jy20vrx",
#mapbox://styles/olimac/cl144ojyu004l16s236ersrko"
        ),
        modebar_add=['drawline',
            'drawopenpath',
            'drawclosedpath',
            'drawcircle',
            'drawrect',
            'eraseshape'],
#        title = 'Events selected',
#        geo = dict(
##            fitbounds="geojson",
#            center = {'lat':13,'lon':-89},
#            showland = True,
##            landcolor = "rgb(212, 212, 212)",
##            subunitcolor = "rgb(255, 255, 255)",
##            countrycolor = "rgb(255, 255, 255)",
#            landcolor = "rgb(230, 145, 56)",
#            subunitcolor = "rgb(255, 255, 255)",
#            countrycolor = "rgb(255, 255, 255)",
#            oceancolor = "rgb(0, 255, 255)",
#            showlakes = True,
##            lakecolor = "rgb(255, 255, 255)",
#            lakecolor = "rgb(0, 255, 255)",
#            showsubunits = True,
#            showcountries = True,
#            countrywidth = 0.5,
#            subunitwidth = 0.5,
#            projection = dict(
#            type = 'azimuthal equal area',
#            scale=4,
##            type = 'conic conformal',
#            rotation_lon = -100
#            ),
#            lonaxis = dict(
#            showgrid = True,
#            gridwidth = 0.5,
#            range= [ -140.0, -55.0 ],
#            dtick = 5
#            ),
#            lataxis = dict (
#            showgrid = True,
#            gridwidth = 0.5,
#            range= [ 20.0, 60.0 ],
#            dtick = 5
#            ),
#        ),
         )
    fig.add_annotation(x=0.5, y=0.03,showarrow=False,text=mapText,font=dict(size=15,color="black"),)

#    fig = px.scatter_geo(dff.loc[[row]], locations="iso_alpha", color="continent",
#                     hover_name="continent", size="pop",
#                     projection="natural earth")
#    fig = px.scatter_geo(dff, locations="iso_alpha",
#                     hover_name="continent", size="pop",
#                     projection="natural earth")
    return fig


def create_time_series(df,Fp_vect,Fn_vect,title):

#    fig = px.scatter(dff, x='Year', y='Value')
#    fig.update_traces(mode='lines+markers')
#    fig.update_xaxes(showgrid=False)
#    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')
#    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
#                       xref='paper', yref='paper', showarrow=False, align='left',
#                       text=title)
#    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})
    #print(dff)

#    print(df)


#    fig = go.Figure()
#    tpVec = []
#    for tp in df["type"]:
#        if tp not in tpVec:
#            tpVec.append(tp)
#            dff = df[df['type'] == tp]
#            dff['prefOriTime']=pd.to_datetime(dff['prefOriTime'])
##            print(type(dff['prefOriTime'][0]))
#            dff.sort_values(by='prefOriTime',inplace=True)
#            fig.add_trace(go.Scatter(
#            x = dff['prefOriTime'],
#            y = dff['difTime'],
##            marginal_y="histogram",
##            text=dff['']
##            fill='tonexty',
##            fill='tozeroy',
##            mode = 'lines+markers',
#            mode = 'markers',
#            name = tp,
#            marker = dict(size=5))
#            )

#    fig = px.scatter(df, x='prefOriTime', y='difTime', color='type',marginal_y="box",template="presentation")
	df["symbol"]="triangle-up"
	for index, row in df.iterrows():
		if row["type"] == "4th P":
			df.at[index, "symbol"] = "triangle-up"
		else:
			df.at[index, "symbol"] = "triangle-down"
	fig = px.scatter(df, x='prefOriTime', y='difTime', color='type',symbol='symbol',symbol_map='identity',template="presentation")
	dmin = df["difTime"].values.min()
	dmax = df["difTime"].values.max()
	div = dmax/abs(dmin)
	step = abs(dmin)/(5-round(div))
	tickvals1 = np.arange(dmin,0,step)
	ticktext1 = np.arange(-dmin,0,-step)
	tickvals2 = np.arange(0,dmax,step)
	ticktext = np.concatenate((ticktext1.astype(int), tickvals2.astype(int)))
	tickvals = np.concatenate((tickvals1.astype(int), tickvals2.astype(int)))
	dfg = df.groupby("prefOriTime")
	dfg = [dfg.get_group(x) for x in dfg.groups]
	for dfO in dfg:
		time = dfO["prefOriTime"].values[0]
		pts = dfO["difTime"].values
		try:
			fig.add_trace(go.Scatter(x=[time,time],y=[pts[0],pts[1]],mode='lines',line=dict(color="black", width=1),showlegend=False))
		except:
			pass
	for xi in Fp_vect:
		if xi == Fp_vect[len(Fp_vect)-1]:
			fig.add_trace(go.Scatter(x=[xi,xi],y=[dmin,dmax],mode='lines',line=dict(color="#fadc9b", width=2, dash='dash'), name='False +'))
		else:
			fig.add_trace(go.Scatter(x=[xi,xi],y=[dmin,dmax],mode='lines',line=dict(color="#fadc9b", width=2, dash='dash'),showlegend=False))
#			fig.add_vline(x = xi, line_width=3, line_dash="dash", line_color="#fadc9b", opacity=0.7)
	for xi in Fn_vect:
		if xi == Fn_vect[len(Fn_vect)-1]:
			fig.add_trace(go.Scatter(x=[xi,xi],y=[dmin,dmax],mode='lines',line=dict(color="#ff9c9c", width=2, dash='dash'), name='False -'))
		else:
			fig.add_trace(go.Scatter(x=[xi,xi],y=[dmin,dmax],mode='lines',line=dict(color="#ff9c9c", width=2, dash='dash'),showlegend=False))
#        fig.add_vline(x = xi, line_width=3, line_dash="dash", line_color="#ff9c9c", opacity=0.7)
#    print(df.loc[df['']==])

#    fig.add_bar(df,x='prefOriTime',y='difTime',color='type')
#    fig1.update_traces(mode='lines+markers')
#    fig.update_traces(mode='markers', marker=dict(size=10))
	fig.update_traces(marker=dict(size=10))
	fig.update_xaxes(showgrid=False)
#    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')
#    fig1.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
#                       xref='paper', yref='paper', showarrow=False, align='left',
#                       text=title)

#    fig2 = px.area(df, x='prefOriTime', y='difTime', color='type')

#    fig2 = px.line(df, x='prefOriTime')
#    fig = go.Figure(data=fig2.data+fig1.data)
##    fig = go.Figure(data=fig1.data)
	config = {'displaylogo': False}
	fig.update_layout(
		margin={'l': 10, 'b': 50, 'r': 0, 't': 0},
		xaxis=dict(showgrid=False, linecolor="dimgrey", linewidth=2, zeroline=False,title=None,ticklabelposition="outside right"),
		yaxis=dict(showgrid=False, linecolor="dimgrey", linewidth=2, zeroline=True,title=None,ticklabelposition="inside top",tickmode="array",ticktext=ticktext,tickvals=tickvals),
		legend=dict(title="True +:",bordercolor="dimgrey",borderwidth=1,x=1.0,y=0.93),
		modebar_add=['drawline',
			'drawopenpath',
			'drawclosedpath',
			'drawcircle',
			'drawrect',
			'eraseshape']
		)

#    fig.update_layout(
#        title={'text': "1st origin and EEW mag delay",'y':0.95,'x':0.5,'xanchor': 'center','yanchor': 'top'},
#        xaxis=dict(title="Origin Time"),
#        yaxis=dict(title="Time after Ot (s)"),
#        legend_title="Delay Type",
#        height=500)
#        margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

#    fig = px.scatter(df, x='prefOriTime', y='difTime', color='type')
##    fig.add_bar(df,x='prefOriTime',y='difTime',color='type')
#    fig.update_traces(mode='lines+markers')
#    fig.update_xaxes(showgrid=False)
##    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')
#    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
#                       xref='paper', yref='paper', showarrow=False, align='left',
#                       text=title)

	return fig

def create_histo(dataPlot):
	delayAll = []
	group_labels = []
	data = dataPlot.groupby(['MMI'])
	data = [data.get_group(x) for x in data.groups]
	for df in data:
		delay = []
		group_labels.append(df['MMI'].unique()[0])
		for index, row in df.iterrows():
			if row["type"] in validMagTypes:
				delay.append(row["difTime"])
		delayAll.append(delay)
	fig = ff.create_distplot(delayAll, group_labels, curve_type='normal', show_hist=False, show_rug=False)
	return fig

@callback(
    Output('histogram', 'figure'),
    Input("date-range", 'start_date'),
    Input('date-range', 'end_date'),
    Input("mag-range", 'value'),
    )
def update_graph(start_date, end_date, magValue):
    startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    startTime = startTime.date()
    endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    endTime = endTime.date()
    try:
        dataPref, dataPlot, Fp_vect, Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)
    except:
        print("No data in selected period")
    return create_histo(dataPlot)


def create_pie(Tp_vect,Fp_vect,Fn_vect):
#	colors = ['blue','blue','blue','#fadc9b','#fadc9b','#fadc9b','#ff9c9c']
	subeval = ["VS","FD","VS&FD","VS","FD","VS&FD",None]
	eval_types = ["T+","T+","T+","F+","F+","F+","F-"]
	eve_conunt = [len(Tp_vect)/3,len(Tp_vect)/3,len(Tp_vect)/3,len(Fp_vect)/3,len(Fp_vect)/3,len(Fp_vect)/3,len(Fn_vect)]
	df = pd.DataFrame(dict(eval_types=eval_types,subeval=subeval,eve_conunt=eve_conunt))
	fig = px.sunburst(df, path=['eval_types','subeval'], values='eve_conunt', color='eval_types',color_discrete_map={'(?)':'black','T+':'blue', 'F+':'#fadc9b', 'F-':'#ff9c9c'})
#	fig.update_traces(textfont_size=20,marker=dict(colors=colors, line=dict(color='#000000', width=2)))
	return fig

@callback(
    Output('pie', 'figure'),
    Input('map', 'clickData'),
    Input("date-range", 'start_date'),
    Input('date-range', 'end_date'),
    Input("mag-range", 'value'),
    )
def update_graph(clickData, start_date, end_date, magValue):
    startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    startTime = startTime.date()
    endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    endTime = endTime.date()
    try:
        dataPref, dataPlot, Fp_vect, Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)
    except:
        print("No data in selected period")
    return create_pie(Tp_vect, Fp_vect, Fn_vect)


@callback(
    Output('mag', 'figure'),
    Input('map', 'clickData'),
    Input("date-range", 'start_date'),
    Input('date-range', 'end_date'),
    Input("mag-range", 'value'),
    )
def update_graph(clickData, start_date, end_date, magValue):
#    print(clickData)
#    index = clickData['points'][0]['pointIndex']
#    #print(index)
#    #print(str(df.loc[[index]]['name']))
#    city_name = df.loc[[index]]['name']
#    city_name = str(city_name.to_string(index=False))
#    dff = df[df['name'] == city_name[1:]]
#    print(dff)
##    dff = dff[dff['Indicator Name'] == xaxis_column_name]
#    value = "pop"
    startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    startTime = startTime.date()
    endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    endTime = endTime.date()
    try:
        dataPref, dataPlot, Fp_vect, Fn_vect,Tp_vect = prepare_data(startTime, endTime, magValue)
    except:
        print("No data in selected period")
    title = '<b>TimeSpan</b>'
    return create_time_series(dataPlot.drop(['MMI'], axis=1), Fp_vect, Fn_vect, title)


#@callback(
#    Output('mag', 'figure'),
#    Input('map', 'clickData'))
##    Input('crossfilter-xaxis-column', 'value'),
##    Input('crossfilter-xaxis-type', 'value'))
#def update_pop(clickData):
#    print(clickData)
#    index = clickData['points'][0]['pointIndex']
#    #print(index)
#    #print(str(df.loc[[index]]['name']))
#    city_name = df.loc[[index]]['name']
#    city_name = str(city_name.to_string(index=False))
#    dff = df[df['name'] == city_name[1:]]
#    print(dff)
##    dff = dff[dff['Indicator Name'] == xaxis_column_name]
#    value = "pop"
#    title = '<b>{}</b>'.format(city_name)
#    return create_time_series(dff, value, title)


#@callback(
#    Output('lifeExp', 'figure'),
#    Input('map', 'clickData'))
##    Input('crossfilter-yaxis-column', 'value'),
##    Input('crossfilter-yaxis-type', 'value'))
#def update_lifeExp(clickData):
#    dff = df[df['continent'] == clickData['points'][0]['hovertext']]
##    dff = dff[dff['Indicator Name'] == yaxis_column_name]
#    value = "lifeExp"
#    return create_time_series(dff, value, value)


#if __name__ == '__main__':
#    app.run_server(debug=False)
