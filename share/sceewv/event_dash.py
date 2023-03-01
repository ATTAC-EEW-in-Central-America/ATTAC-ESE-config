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

from dash import Dash, dcc, html, Input, Output, callback, dash_table, no_update, State
import json, glob, os, datetime
import dash_bootstrap_components as dbc
import pandas as pd
from pandas import json_normalize
from operator import itemgetter
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.io as pio
import numpy as np
from obspy import read, read_inventory
from obspy.clients.fdsn import Client
from obspy.geodetics.base import locations2degrees
from obspy.taup import TauPyModel
from obspy import UTCDateTime
import operator
import functools
from plotly.validators.scatter.marker import SymbolValidator
from matplotlib.cm import get_cmap
import geopandas as gpd
import pandas_read_xml as pdx
import requests, io
import shapely.geometry
import svgpath2mpl
from seiscomp import system
import configparser
from copy import deepcopy

ei = system.Environment.Instance()

external_stylesheets=[dbc.themes.BOOTSTRAP]
config = configparser.RawConfigParser()
config.read(ei.shareDir()+"/sceewv/apps.cfg")
cfg = dict(config.items('event'))
mapbox_access_token = open(cfg['mapboxtoken']).read()
eventsJsonPath = cfg['jsonpath']
eventJsonPath = cfg['evejsonpath']
phases = cfg['phases'].split(",")
colors = cfg['colors'].split(",")
color = {}
for i in range(len(phases)):
	color[phases[i]]=colors[i]
MODEL = cfg['model']
model = TauPyModel(model=MODEL)
magtypes = cfg['magtypes'].split(",")
lat_min = float(cfg['latmin'])
lat_max = float(cfg['latmax'])
lon_min = float(cfg['lonmin'])
lon_max = float(cfg['lonmax'])
fdsnwsData = cfg['fdsnwsclientwf']
eveminmag = float(cfg['eveminmag'])
evemaxmag = float(cfg['evemaxmag'])
deltadays = int(cfg['evedeltadays'])
timebefore = int(cfg['timebefore'])
timeafter = int(cfg['timeafter'])

fmt = '%Y-%m-%d %H:%M:%S'


distint = 100
tabsVect = []

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

def ipe_allen2012_hyp(m, # magnitude (float)
					a = 2.085,
					b = 1.428,
					c = -1.402,
					d = 0.078,
					s = 1,
					m1=-0.209,
					m2=2.042):
	rm = m1+(m2*np.exp(m-5))
	MMIint=None
	MMIfloat=None
	for I in np.arange(1,10,0.5):
		phi = (I-a-(b*m)-s)/c
		r = np.sqrt((np.exp(phi)**2)-(rm**2))
		if math.isnan(r)==False:
			if r > 50:
				if I.is_integer()==True:
					if MMIint:
						MMIint["I"].append(I)
						MMIint["r"].append(round(r))
					else:
						MMIint={'I':[I],'r':[round(r)]}
				else:
					if MMIfloat:
						MMIfloat["I"].append(I)
						MMIfloat["r"].append(round(r))
					else:
						MMIfloat={'I':[I],'r':[round(r)]}
	return MMIint, MMIfloat

def ipe_allen2012_hyp2(r, # hypocentral distance (km, float)
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
    return I


def getEvents(startTime, endTime, magValue):
	events = []
	for root, dirs, files in os.walk(eventsJsonPath):
		length = len(root)
		try:
			dayPath = datetime.datetime.strptime(root[-11:length],'/%Y/%m/%d')
			dayPath = dayPath.date()
		except:
			continue
		if dayPath >= startTime and dayPath <= endTime:
			for item in files:
				mag = None
				regEval = 0
				magEval = 0
				fil = os.path.join(root, item)
				f = open(os.path.join(os.getcwd(), fil), 'r')
				dat = json.load(f)
				for iOri in range(len(dat["origins"])):
					if dat["prefOrigin"] == dat["origins"][iOri]["ID"]:
						lat = dat["origins"][iOri]["latitude"]
						lon = dat["origins"][iOri]["longitude"]
						if lat > lat_max or lat < lat_min or lon > lon_max or lon < lon_min:
							regEval = 1
							break
						prefOriTime = dat["origins"][iOri]["OriginTime"]
						eventID = dat["eventID"]
						try:
							for iMag in range(len(dat["origins"][iOri]["mags"])):
								if dat["prefMag"] == dat["origins"][iOri]["mags"][iMag]["ID"]:
									mag = dat["origins"][iOri]["mags"][iMag]["value"]
									if mag < magValue[0] or mag > magValue[1]:
										magEval = 1
										break
						except:
							pass
				if regEval == 1 or magEval ==1:
					continue
				else:
					pass
				if mag:
					event = {"Time":prefOriTime, "Mag":round(mag,2), "ID":eventID}
				else:
					event = {"Time":prefOriTime, "Mag":"None", "ID":eventID}
				events.append(event)
	events = json_normalize(events)
	return events

def getWave(stream,iniTime,endTime):
	trace = stream.split(".")
	try:
		clientWf = Client(fdsnwsData)
		#print("Connection established to %s for waveforms" % fdsnwsData)
	except Exception as e:
		#print(e)
		return None
	try:
		st = clientWf.get_waveforms(trace[0], trace[1], trace[2], trace[3][0:2]+"?", UTCDateTime(iniTime), UTCDateTime(endTime))
		print("Obtained waveform for:")
		print(stream)
		return st
	except Exception as e:
		print("no waveform for:")
		print(stream)
		print(e)
		return None

def prepare_data(eventID):
	for root, dirs, files in os.walk(eventsJsonPath):
		for item in files:
			magPref = None
			if item == eventID:
				magPrefType = None
				frstDif = None
				dMag = []
				dPick = []
				vectOri=[]
				fil = os.path.join(root, item)
				f = open(os.path.join(os.getcwd(), fil), 'r')
				data = json.load(f)
				for iOri in range(len(data["origins"])):
					plot=False
					vectPick=[]
					if data["prefOrigin"] == data["origins"][iOri]["ID"]:
						prefOriTime = data["origins"][iOri]["OriginTime"]
						data["origins"][iOri]["eventID"] = data["eventID"]
						latPref = data["origins"][iOri]["latitude"]
						lonPref = data["origins"][iOri]["longitude"]
						depthPref = data["origins"][iOri]["depth"]
						for iPick in range(len(data["origins"][iOri]["picks"])):
							pickID = data["origins"][iOri]["picks"][iPick]["ID"]
							pCreaTime = data["origins"][iOri]["picks"][iPick]["CreationTime"]
							pTime = data["origins"][iOri]["picks"][iPick]["time"]
							pSta = data["origins"][iOri]["picks"][iPick]["station"]
							pStaLat = data["origins"][iOri]["picks"][iPick]["staLat"]
							pStaLon = data["origins"][iOri]["picks"][iPick]["staLon"]
							dPick.append({"pickID":pickID,"station":pSta,"staLat":pStaLat,"staLon":pStaLon,"pCreaTime":pCreaTime,"pTime":pTime})
					else:
						OriTime = data["origins"][iOri]["OriginTime"]
						latOri = data["origins"][iOri]["latitude"]
						lonOri = data["origins"][iOri]["longitude"]
						Ori = {"lat":float(latOri), "lon":float(lonOri), "oTime":OriTime}
						try:
							for iPick in range(len(data["origins"][iOri]["picks"])):
								pickID = data["origins"][iOri]["picks"][iPick]["ID"]
								pCreaTime = data["origins"][iOri]["picks"][iPick]["CreationTime"]
								pTime = data["origins"][iOri]["picks"][iPick]["time"]
								pSta = data["origins"][iOri]["picks"][iPick]["station"]
								vectPick.append({"pickID":pickID,"station":pSta,"pCreaTime":pCreaTime,"pTime":pTime})
						except:
							pass
							#print("No picks for %s"%data["origins"][iOri]["ID"])
					try:
						for iMag in range(len(data["origins"][iOri]["mags"])):
							latOri = data["origins"][iOri]["latitude"]
							lonOri = data["origins"][iOri]["longitude"]
							magStaNum = data["origins"][iOri]["mags"][iMag]["StaCount"]
							likelihood = None
							if "comments" in data["origins"][iOri]["mags"][iMag]:
								for icomm in range(len(data["origins"][iOri]["mags"][iMag]["comments"])):
									commentID = data["origins"][iOri]["mags"][iMag]["comments"][icomm]["ID"]
									commentText = data["origins"][iOri]["mags"][iMag]["comments"][icomm]["text"]
									if commentID == "likelihood":
										likelihood = round(float(commentText),2)
							if data["prefMag"] == data["origins"][iOri]["mags"][iMag]["ID"]:
								magPref = data["origins"][iOri]["mags"][iMag]["value"]
								magPrefType = data["origins"][iOri]["mags"][iMag]["type"].split(' ')[0]
								magPrefAuth = data["origins"][iOri]["mags"][iMag]["type"].split(' ')[1]
								magTime = data["origins"][iOri]["mags"][iMag]["CreationTime"]
								inten = ipe_allen2012_hyp2(distint,magPref)
								dpref = {"author":magPrefAuth,"type":magPrefType,"value":magPref,"magTime":magTime, "lat":latOri, "lon":lonOri, "staCount":magStaNum, "intensity":inten, "like":likelihood}
								# dMag.append(d)
							if data["origins"][iOri]["EvaluationMode"] == 1:
								magTime = data["origins"][iOri]["mags"][iMag]["CreationTime"]
								magType = data["origins"][iOri]["mags"][iMag]["type"].split(' ')[0]
								magAuth = data["origins"][iOri]["mags"][iMag]["type"].split(' ')[1]
								magVal = data["origins"][iOri]["mags"][iMag]["value"]
								inten = ipe_allen2012_hyp2(distint,magVal)
								OriTime = data["origins"][iOri]["OriginTime"]
								d = {"author":magAuth, "type":magType,"value":magVal,"magTime":magTime, "lat":latOri, "lon":lonOri, "staCount":magStaNum, "intensity":inten, "like":likelihood}
								# if d["type"] in magtypes or d["type"] == magPrefType:
								if d["type"].split(' ')[0] in magtypes:
									dMag.append(d)
								#	magtypes.append(d["type"])
								if magType.split(' ')[0] in magtypes and not plot:
									vectOri.append({"lat":float(latOri), "lon":float(lonOri), "oTime":OriTime, "magVal":magVal})
									plot = True
					except:
						pass
						#print("No mag in file %s origin %s" % (fil,data["origins"][iOri]["ID"]))
				if magPref:
					prefEvent = {"lat":float(latPref), "lon":float(lonPref), "depth":float(depthPref), "mag":float(magPref), "magPrefType":magPrefType, "oTime":prefOriTime}
				else:
					prefEvent = {"lat":float(latPref), "lon":float(lonPref), "depth":float(depthPref), "mag":float(0), "magPrefType":magPrefType, "oTime":prefOriTime}
				# timeVect = []
				for i in range(len(dMag)):
					oTime = datetime.datetime.strptime(prefOriTime, fmt)
					mTime = datetime.datetime.strptime(dMag[i]["magTime"], fmt)
					if dMag[i]["type"] in magtypes:
						difTime = (mTime-oTime).total_seconds()
					# elif dMag[i]["type"] == magPrefType:
						# # if not frstDif:
							# # frstDif = (mTime-oTime).total_seconds()
						# difTime = (mTime-oTime).total_seconds()
					locPref = np.array((float(latPref),float(lonPref)))
					locOri = np.array((float(dMag[i]["lat"]),float(dMag[i]["lon"])))
					locErr = np.linalg.norm(locPref-locOri)*111.1
					dMag[i]["difTime"] = difTime
					dMag[i]["locErr"] = locErr
					dpref["difTime"]=difTime
					dMag.append(deepcopy(dpref))
					# timeVect.append(difTime)
				# for i in range(len(timeVect)):
					
				# dpref["difTime"]=max(timeVect)
				# print(dpref)
				# dMag.append(dpref)

#				for i in range(len(dPick)):
##					If want to use creation timne use dPick[i]["pCreaTime"] if you want to use pick time dPick[i]["pTime"]
#					pTime = datetime.datetime.strptime(dPick[i]["pTime"], fmt)
#					difpTime = (pTime-oTime).total_seconds()
#					dPick[i]["difpTime"] = difpTime
				dPickSort = sorted(dPick, key=itemgetter("pTime"))
#				pool = Pool(numPools)
#				try:
#					pool.map(getWave, selectedStreams)
#				except Exception as e:
#					print e
#				pool.close()
#				pool.join()


#				pIDvec = []
#				count = 0
#				for i in range(len(dPickSort)):
#					if dPickSort[i]["pickID"] not in pIDvec:
#						pIDvec.append(dPickSort[i]["pickID"])
#						count += 1
#					if count == 5:
#						break
	dataMag = json_normalize(dMag)
	# dMagPref = dataMag.loc[dataMag['type'] == magPrefType]
	# dMagEEW = dataMag.loc[dataMag['type'].isin(magtypes)]
	# minMag = min(dMagPref["difTime"])
	# maxMag = max(dMagEEW["difTime"])
	# for index, row in dataMag.iterrows():
		# if row["type"]==magPrefType:
			# dataMag.at[index, "difTime"] = row["difTime"]-minMag
	# dataMag=dataMag.loc[(dataMag['difTime'] <= maxMag)]

#	dataPref.dropna(inplace=True)
#	dataPref.reset_index(drop=True, inplace=True)
	return dataMag, prefEvent, dPickSort, vectOri

#initial_active_cell = {"row": 0, "column": 0, "column_id":'Time'}
endTime = date.today()
startTime = endTime - relativedelta(days=deltadays)
magValue = [eveminmag, evemaxmag]

events = getEvents(startTime, endTime, magValue)

#eventID = events["ID"][0]
#dataMag = prepare_data(eventID)

tab1_content = dcc.Graph(id='shaking',config= {'displaylogo': False})
tab2_content = dcc.Graph(id='magnitude',config= {'displaylogo': False})
tab3_content = dcc.Graph(id='locErr',config= {'displaylogo': False})
tab4_content = dcc.Graph(id='like',config= {'displaylogo': False})
tab5_content = dcc.Graph(id='staCount',config= {'displaylogo': False})

layout = html.Div(
	[
	html.Div(id='pageContent'),
		dbc.Row(
		[
			dbc.Col(
				html.Div([
				dbc.Button("Events", id="open-offcanvas", n_clicks=0),
					dbc.Offcanvas(
					html.P([
						dcc.DatePickerRange(
						id='date',
						minimum_nights=5,
						clearable=True,
						with_portal=True,
						start_date=startTime,
						end_date=endTime,
						calendar_orientation='vertical',
						),
						dcc.RangeSlider(
						id='mag-range',
						min=0,
						max=10,
#						step=1,
						value=magValue,
						tooltip={"placement": "bottom", "always_visible": True}
						),
						dash_table.DataTable(
						id = 'tabla',
						data = events.to_dict('records'),
#						active_cell=initial_active_cell
						)
					]),
					id="offcanvas",
					title="Events",
#					is_open=True,
					)
				]),
			)
		]),

		dbc.Row(
		[
			dbc.Col([
				dcc.Graph(
					# id='waveform',
					id='envelope',
					config= {'displaylogo': False},
				),
			],width=6),

			dbc.Col(
					id = 'container',
					width=6
					),
		],className="g-0"),

		dbc.Row(
		[
			dbc.Col(
			dcc.Link('Go back to home', href='/'),
			),
			dbc.Col(
			dcc.Link('Go to events', href='/events'),
			)
		])
	])

@callback(
	Output('container', 'children'),
	[Input("date", 'start_date')],
	# [State('container', 'children')],
	[State("storeEventID", "data")]
	)
def updateTABS(start_day,storeID):
	_,_,_,vectOri=prepare_data(storeID)
	numEEW = len(vectOri)
#	maptab2_content = dcc.Graph(id='eventMap1',config= {'displaylogo': False})
	tabsVect = []
	for tab in range(numEEW):
		tabsVect.append(dbc.Tab(label='EEW{0}'.format(tab), tab_id=str(tab), tab_style={"width": "10%", 'height': '10%',"display": "inline-block"}))
	# print(numEEW)
	# print(tabsVect)
	content = [
				dbc.Tabs(
					[
						dbc.Tab(label="Shaking", tab_id="tab-1", tab_style={"marginLeft": "auto"}),
						dbc.Tab(label="Magnitude", tab_id="tab-2"),
						dbc.Tab(label="Location", tab_id="tab-3"),
						dbc.Tab(label="Likelihood", tab_id="tab-4"),
						dbc.Tab(label="Stations", tab_id="tab-5")
					],
					id="EventTabs",
					active_tab="tab-1",
					),
					html.Div(id="tabContent"),
				dbc.Tabs(
					tabsVect,
					id="eventMapstabs",
					active_tab="0",
					),
					html.Div(id="tabContentMaps"),
				]
	# div_children.append(new_child)
	return content

@callback(
	Output("offcanvas", "is_open"),
	Input("open-offcanvas", "n_clicks"),
	State("offcanvas", "is_open"),
	State("storeEventID", "data")
)
def toggle_offcanvas(n1, is_open, storeID):
	if storeID == None:
		return not is_open
	if n1:
		return not is_open
	return is_open

@callback(
	Output('waveform', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data"),
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
	wfIni = datetime.timedelta(seconds=timebefore)
	wfLng = datetime.timedelta(seconds=timeafter)
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
#	print(dPickSort[0:5])
	fig = make_subplots(rows=5, cols=1)
	row = 0
	for pick in dPickSort[0:5]:
		row += 1
		sTime = datetime.datetime.strptime(pick["pTime"], fmt)-wfIni
		eTime = sTime+wfLng
		st = getWave(pick["station"],sTime,eTime)
		tr = st[0]
		x = []
		for xi in tr.times("utcdatetime"):
			x.append(xi.datetime)
		fig.add_trace(go.Scatter(x=x,y=tr.data,name=tr.stats.station),
		row=row, col=1)
	return fig

@callback(
	Output('envelope', 'figure'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data"),
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
	iniTimeWF = datetime.timedelta(seconds=timebefore)
	endTimeWF = datetime.timedelta(seconds=timeafter)
	fdsnwsClientWF = fdsnwsData
	fmt = '%Y-%m-%d %H:%M:%S'
	#read event info
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	evTime = datetime.datetime.strptime(prefEvent["oTime"], fmt)
	evLat = [prefEvent["lat"]]
	evLon = [prefEvent["lon"]]
	evDepth = prefEvent["depth"]

	dataMag.sort_values(by='difTime',inplace=True)
	mag = dataMag.loc[dataMag['type'].isin(magtypes)]
	firstMag = mag.iloc[0]["difTime"]
	magTime = evTime+datetime.timedelta(seconds=float(firstMag))

	#read json for event if found
	year = evTime.year
	month = evTime.month
	day = evTime.day
	new_folder = "%s/%s/%s/" % (year,month,day)
	dayRoute = os.path.join(eventJsonPath, new_folder)
	evFile = os.path.join(dayRoute, eventID)
	if not os.path.exists(evFile):
		if not os.path.exists(dayRoute):
			os.makedirs(dayRoute)
		fmt = '%Y-%m-%d %H:%M:%S'
		# all_figures = []
		Tim = []
		Dst = []
		Acc = []
		for pick in dPickSort:
			tr = None
			# sTime = datetime.datetime.strptime(pick["pTime"], fmt)-wfIni
			sTime = evTime-iniTimeWF
			eTime = sTime+endTimeWF
			try:
				# os.system('wget -O '+dayRoute+'inv.fdsn "http://190.151.176.124:8080/fdsnws/station/1/query?station='+pick["station"].split(".")[1]+'&level=response&nodata=404"')
				# os.system('/home/cam/EEW/SEISCOMP/seiscomp/bin/seiscomp exec import_inv  fdsnxml '+dayRoute+'inv.fdsn '+dayRoute+'inv.xml')
				st = getWave(pick["station"],sTime,eTime)
				st.write(dayRoute+eventID+".mseed",format='MSEED')
				os.system(ei.installDir()+"/bin/seiscomp exec scmssort "+dayRoute+eventID+".mseed > "+dayRoute+eventID+"_s.mseed")
				os.system(ei.installDir()+"/bin/seiscomp exec sceewvenv -u eewv --offline -I "+dayRoute+eventID+"_s.mseed --dump --debug > "+dayRoute+eventID+"_env.mseed")
				st = read(dayRoute+eventID+"_env.mseed")
				# inv = read_inventory(dayRoute+"inv.fdsn")
				staLat = pick["staLat"]
				staLon = pick["staLon"]
				distDeg = locations2degrees(evLat, evLon, staLat, staLon)*111.1
				dist = np.round(distDeg)
				for trace in st:
					if trace.stats.location == 'EA':
						tr = trace
				# tr = st[0]
				x = []
				y = []
				for xi in tr.times("utcdatetime"):
					x.append(xi.datetime)
					y.append(int(dist[0]))
				# fig.add_trace(go.Scatter(x=x,y=y,marker=dict(color=tr.data,colorscale="Viridis"),mode='markers'))
				# fig.add_trace(go.Scatter(x=x,y=y,marker=dict(color=tr.data,colorscale="Viridis",colorbar=dict(title="Colorbar")),mode='markers'))
				if len(Acc)==0 and len(Tim)==0 and len(Dst)==0:
					Tim = x
					Dst = y
					Acc = tr.data
				else:
					Tim = Tim+x
					Dst = Dst+y
					Acc = np.append(Acc,tr.data)
				# dic = {'x':x, 'y':tr.data}
				# dic = {'x':x, 'y':dist[0], 'color':tr.data}
				# df = pd.DataFrame(dic)
				# fig_temp = px.scatter(df, x="x", y="y", color="color", range_color=[0, 0.005])
				# all_figures.append(fig_temp)
			except Exception as e:
				print("Station: %s"%pick)
				print("Error: %s"%e)
				continue
		os.system('rm -f %s%s.mseed %s%s_s.mseed %s%s_env.mseed'%(dayRoute,eventID,dayRoute,eventID,dayRoute,eventID))
		Acc = Acc.tolist()
		envDict = {'Tim':Tim, 'Dst':Dst, 'Acc':Acc}
		###save dataframe with envelope acceleration results
		try:
			f = open(evFile,'w+')
		except Exception as e:
			logging.error("error when writing in file:\n %s" % fullName)
		#	return
	#		print self.eve
		json.dump(envDict, f, indent=4, default=str)
		f.flush()
		f.close()
	else:
		f = open(os.path.join(os.getcwd(), evFile), 'r')
		data = json.load(f)
		Tim = data['Tim']
		Dst = data['Dst']
		Acc = data['Acc']

	#plot
	fig = go.Figure()
	#print theoric phases
	for j, phase in enumerate(phases):
		x=[]
		y=[]
		phaseName=[]
		# print(Dst)
		for dist in np.arange(min(Dst)/111.1, max(Dst)/111.1, 0.1): # calculate and plot one point for each range
			arrivals = model.get_travel_times(source_depth_in_km=evDepth,distance_in_degree=dist, phase_list=[phase])
			printed = False
			for i in range(len(arrivals)):
				instring = str(arrivals[i])
				phaseline = instring.split(" ")
				if phaseline[0] == phase and printed == False:
					x.append(evTime+datetime.timedelta(seconds=float(phaseline[4])))
					y.append(dist*111.1)
					phaseName.append(phaseline[0])
					printed = True
		if len(x) != 0 and len(y) != 0:
			phasePrint = color[phaseline[0]]
			fig.add_trace(go.Scatter(
							text=phaseName,
							x=x,
							y=y,
							mode='lines',
							line=dict(
								color=phasePrint,
								width=2, dash='dash'),
							showlegend=False,
							hovertemplate=
							"%{text}"+
							"<extra></extra>"
							# marker=dict(
								# symbol='line-ns',
								# line_width=1,
								# ),
							# mode='markers'
							)
						)
	#plot eew MVS
	fig.add_trace(go.Scatter(x=[magTime,magTime],y=[min(Dst)-10,max(Dst)+10],mode='lines',line=dict(color="brown", width=3),showlegend=False))
	#plot env accelearation values
	cmax = np.percentile(Acc, 75)
	fig.add_trace(go.Scatter(
					x=Tim,
					y=Dst,
					marker=dict(
						color=Acc,
						line_color=Acc,
						line_colorscale="Viridis",
						# line_colorscale=px.colors.sequential.Rainbow,
						# colorscale=px.colors.sequential.Rainbow,
						colorscale="Viridis",
						line_cmin=0,
						line_cmax=cmax,
						cmin=0,
						cmax=cmax,
						symbol=41,
						line_width=3,
						colorbar=dict(title="Acceleration")),
					showlegend=False,
					mode='markers',
					hovertemplate=
					"<i>Date</i>: %{x}<br>"+
					"<i>Accel</i>: %{marker.line.color:.5f}<br>"+
					"<i>Dist</i>: %{y}"+
					"<extra></extra>"
					)
				)

	fig['layout']['yaxis']['autorange'] = "reversed"
	# fig = go.Figure(data=functools.reduce(operator.add, [_.data for _ in all_figures]))
	
	fig.update_layout(
		height=800,
		)

	# fig.update_layout(coloraxis_colorbar=dict(
	# title="Number of Bills per Cell",
	# thicknessmode="pixels", thickness=50,
	# lenmode="pixels", len=200,
	# yanchor="top", y=1,
	# ticks="outside", ticksuffix=" bills",
	# dtick=5
	# ))
	return fig

@callback(Output("tabContent", "children"), [Input("EventTabs", "active_tab")])
def switch_tab(at):
	if at == "tab-1":
		return tab1_content
	elif at == "tab-2":
		return tab2_content
	elif at == "tab-3":
		return tab3_content
	elif at == "tab-4":
		return tab4_content
	elif at == "tab-5":
		return tab5_content
	return html.P("This shouldn't ever be displayed...")

@callback(
	Output("tabContentMaps", "children"),
	[Input("eventMapstabs", "active_tab")],
	[State("storeEventID", "data")]
	)
def switch_tab(at,storeID):
	_,_,_,vectOri=prepare_data(storeID)
	numEEW = len(vectOri)
	mapTabs={}
	for tab in range(numEEW):
		mapTabs["content{0}".format(tab)] = dcc.Graph(id='eventMap',config= {'displaylogo': False})
	for tab in range(numEEW):
		if at == str(tab):
			return mapTabs["content{0}".format(tab)]
		elif at == "0":
			return mapTabs["content0"]
	return html.P("This shouldn't ever be displayed...")

@callback(
    Output('tabla', 'style_data_conditional'),
    Input('tabla', 'active_cell')
)
def select_row(active_cell):
    if active_cell:
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
	Output('tabla', 'data'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value')
	)
def update_table(start_date, end_date, magValue):
	startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	startTime = startTime.date()
	endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	endTime = endTime.date()
	events = getEvents(startTime, endTime, magValue)
	return events.to_dict('records')

def create_time_series(df,x,y):
	df.sort_values(by='difTime',inplace=True)
#	fig = px.area(df, x='difTime', y='value', color='type')
	fig = px.scatter(df, x=x, y=y, color='author')
	fig.update_traces(mode='lines+markers')
	return fig

@callback(
	Output('like', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data"),
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
#	eventID = events.iat[active_cell['row'], active_cell['column']]
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
#	events = events.to_dict('records')
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	return create_time_series(dataMag, "difTime", "like")

@callback(
	Output('shaking', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data"),
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
#	eventID = events.iat[active_cell['row'], active_cell['column']]
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
#	events = events.to_dict('records')
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	return create_time_series(dataMag, "difTime", "intensity")

@callback(
	Output('magnitude', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data"),
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
#	eventID = events.iat[active_cell['row'], active_cell['column']]
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
#	events = events.to_dict('records')
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	# print(dataMag)
	return create_time_series(dataMag, "difTime", "value")

@callback(
	Output('locErr', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data")
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	return create_time_series(dataMag, "difTime", "locErr")

@callback(
	Output('staCount', 'figure'),
#	Input('my-input', 'value'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	State("storeEventID", "data")
	)
def update_graph(start_date, end_date, magValue, active_cell,storeID):
	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	return create_time_series(dataMag, "difTime", "staCount")

# create shapely multi-polygon from maki or font-awesome SVG path
def marker(name="star", source="fa"):
	def to_shapely(mpl, simplify=0):
		p = shapely.geometry.MultiPolygon(
			[shapely.geometry.Polygon(a).simplify(simplify) for a in mpl])
		p = shapely.affinity.affine_transform(p,[1, 0, 0, -1, 0, 0],)
		scale = 1 if source == "maki" else 10 ** -2
		p = shapely.affinity.affine_transform(p,[1, 0, 0, 1, -p.centroid.x, -p.centroid.y],)
		return shapely.affinity.affine_transform(p,[scale, 0, 0, scale, -p.centroid.x, -p.centroid.y],)
	if source == "maki":
		url = f"https://raw.githubusercontent.com/mapbox/maki/main/icons/{name}.svg"
	elif source == "fa":
		url = f"https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/{name}.svg"
	svgpath = pdx.read_xml(requests.get(url).text).loc[0].loc["svg"]["path"]["@d"]
	return to_shapely(svgpath2mpl.parse_path(svgpath).to_polygons())

# create mapbox layers for markers.  icon defines layer and color
def marker_mapbox(mark,df,size=0.01,color="blue",lat="lat",lon="lon",typ="fill",outlinecolor="white",opacity=1):
	layers = []
	m = marker(mark, "maki")
	geoms = [
		shapely.affinity.affine_transform(m, [size, 0, 0, size, r[lon], r[lat]])
		for _, r in df.iterrows()
	]
	layers.append(
		{
			"source": gpd.GeoSeries(geoms).__geo_interface__,
			"type": typ,
			"color": color,
			"fill_outlinecolor": outlinecolor,
			"opacity":opacity,
		}
	)
	return layers


@callback(
	Output('eventMap', 'figure'),
	Input("date", 'start_date'),
	Input('date', 'end_date'),
	Input("mag-range", 'value'),
	Input("tabla", "active_cell"),
	Input("eventMapstabs", "active_tab"),
	State("storeEventID", "data")
	)
def update_map(start_date, end_date, magValue,active_cell,active_tab,storeID):
	fmt = '%Y-%m-%d %H:%M:%S'
	txtLat,txtLon,txtAnot =[],[],[]
	txt2Lat,txt2Lon,txt2Anot =[],[],[]
	active_tab=int(active_tab)

	if active_cell:
		startTime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		startTime = startTime.date()
		endTime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		endTime = endTime.date()
		events = getEvents(startTime, endTime, magValue)
		eventID = events.iat[active_cell['row'], 2]
	else:
		eventID = storeID
	dataMag, prefEvent, dPickSort,vectOri = prepare_data(eventID)
	evTime = datetime.datetime.strptime(prefEvent["oTime"], fmt)

	# Origins information
	lat = [prefEvent["lat"]]
	lon = [prefEvent["lon"]]
	depth = prefEvent["depth"]
	latOris=[]
	lonOris=[]
	oriInfo=[]
	for ori in vectOri:
		latOris.append(ori["lat"])
		lonOris.append(ori["lon"])
		oriInfo.append(str(ori["oTime"]))

	evtInfo = [str(round(prefEvent["mag"],2))+"  "+str(prefEvent["oTime"])]
	if prefEvent["mag"] != 0:
		size = prefEvent["mag"]*50
	else:
		size = 10

	dOris = {'Lat': latOris, 'Lon': lonOris}
	dfOris = pd.DataFrame(data=dOris)
	dOri = {'Lat': [latOris[active_tab]], 'Lon': [lonOris[active_tab]]}
	dfOri = pd.DataFrame(data=dOri)

	d = {'Longitude': lon, 'Latitude': lat}
	df = pd.DataFrame(data=d)
	dEve = {'Lat': lat, 'Lon': lon}
	dfEve = pd.DataFrame(data=dEve)

	#EEW time
	dataMag.sort_values(by='difTime',inplace=True)
	mag = dataMag.loc[dataMag['type'].isin(magtypes)]
	firstMag = mag.iloc[0]["difTime"]
	magTime = evTime+datetime.timedelta(seconds=float(firstMag))

	sDist = []
	sEEWtime = []
	# Compute S time after EEW
	for dist in np.arange(0, 2.5, 0.5): # calculate and plot one point for each range
		arrivals = model.get_travel_times(source_depth_in_km=depth,distance_in_degree=dist, phase_list=["S"])
		printed = False
		for i in range(len(arrivals)):
			instring = str(arrivals[i])
			phaseline = instring.split(" ")
			if phaseline[0] == "S" and printed == False:
				sTime = evTime+datetime.timedelta(seconds=float(phaseline[4]))
				diff = (sTime - magTime).total_seconds()
				sEEWtime.append(diff)
				txtLat.append(lat[0]-dist)
				txtLon.append(lon[0])
				txtAnot.append(str(round(diff,1))+"s EEW")
				sDist.append(dist*111.1)
				printed = True
	sDict = {"sEEWtime":sEEWtime,"sDist":sDist}

	gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
	gdf = gdf.join(gdf["geometry"].centroid.apply(lambda g: pd.Series({"lon": g.x, "lat": g.y})))
	gdf2 = gpd.GeoDataFrame(dfOri, geometry=gpd.points_from_xy(dfOri.Lon, dfOri.Lat))
	gdf2 = gdf2.join(gdf["geometry"].centroid.apply(lambda g: pd.Series({"lon": g.x, "lat": g.y})))


	latSts = []
	lonSts = []
	latStsN = []
	lonStsN = []
	stasNameN = []
	stasName = []
	for pick in dPickSort:
		try:
			# inv = client.get_stations(station=pick["station"].split(".")[1])
			staType = pick["station"].split(".")[3][1]
			if staType == "N":
				# latStsN.append(inv.networks[0].stations[0].latitude)
				# lonStsN.append(inv.networks[0].stations[0].longitude)
				latStsN.append(pick["staLat"])
				lonStsN.append(pick["staLon"])
				stasNameN.append(pick["station"])
			else:
				# latSts.append(inv.networks[0].stations[0].latitude)
				# lonSts.append(inv.networks[0].stations[0].longitude)
				latSts.append(pick["staLat"])
				lonSts.append(pick["staLon"])
				stasName.append(pick["station"])
		except:
			stasName.append("None")
			pass

	dSts = {'Lat': latSts, 'Lon': lonSts}
	dfSts = pd.DataFrame(data=dSts)
	dStsN = {'Lat': latStsN, 'Lon': lonStsN}
	dfStsN = pd.DataFrame(data=dStsN)

	fig = go.Figure()

	fig.add_trace(go.Scattermapbox(
		lon = lonOris,
		lat = latOris,
		text = oriInfo,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		mode = 'markers',
		marker = dict(
			# opacity=0.5,
			color = "orangered",
#			line_color='rgb(40,40,40)',
			symbol="star",
			# symbol='',
			size = 20,
#			line_width=0.5,
			sizemode = 'area')
		))

	fig.add_trace(go.Scattermapbox(
		lon = [lonOris[active_tab]],
		lat = [latOris[active_tab]],
		text = [oriInfo[active_tab]],
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		mode = 'markers',
		marker = dict(
			# opacity=0.5,
			color = "green",
#			line_color='rgb(40,40,40)',
			symbol="star",
			# symbol='',
			size = 20,
#			line_width=0.5,
			sizemode = 'area')
		))

	fig.add_trace(go.Scattermapbox(
		lon = lon,
		lat = lat,
		text = evtInfo,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		mode = 'markers',
		marker = dict(
			# opacity=0.5,
			color = "black",
#			line_color='rgb(40,40,40)',
			symbol="star",
			# symbol='',
			size = size,
#			line_width=0.5,
			sizemode = 'area')
		))

# add the markers as geojson layer...
	layerStaN = marker_mapbox("triangle",dfStsN,size=0.01,lat="Lat",lon="Lon",color="DarkSlateBlue",typ="fill",outlinecolor="white",opacity=0.75)
	layerSta = marker_mapbox("circle",dfSts,size=0.01,lat="Lat",lon="Lon",color="DarkSlateBlue",typ="fill",outlinecolor="white",opacity=0.75)
	layerEve = marker_mapbox("star",dfEve,size=0.02,lat="Lat",lon="Lon",color="black",typ="fill",outlinecolor="white",opacity=1)
	layerOris = marker_mapbox("star",dfOris,size=0.01,lat="Lat",lon="Lon",color="orange",typ="fill",outlinecolor=None,opacity=0.5)
	layerOri = marker_mapbox("star",dfOri,size=0.01,lat="Lat",lon="Lon",color="green",typ="fill",outlinecolor="black",opacity=1)
	# layers = layerEve + layerOris + layerOri + layerStaN + layerSta
	# fig.update_layout(mapbox_layers=layers)
	# fig = fig.update_layout(mapbox={"layers": marker_mapbox("star-stroked",dfEve,size=0.03,lat="Lat",lon="Lon",color="black")})
	# fig = fig.update_layout(mapbox={"layers": marker_mapbox("triangle",dfSts,size=0.01,lat="Lat",lon="Lon",color="green")})

	fig.add_trace(go.Scattermapbox(
		lon = lonSts,
		lat = latSts,
		mode = 'markers',
		text = stasName,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		marker = dict(
			opacity=0.5,
			color = "DarkSlateBlue",
			symbol="triangle-up",
			size = size,
			sizemode = 'area')
		))

	fig.add_trace(go.Scattermapbox(
		lon = lonStsN,
		lat = latStsN,
		mode = 'markers',
		text = stasNameN,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		marker = dict(
			opacity=0.5,
			color = "DarkSlateBlue",
			symbol="triangle-up",
			size = size,
			sizemode = 'area')
		))

	MMIint,MMIfloat=ipe_allen2012_hyp(prefEvent["mag"])
	MMIintOri,MMIfloatOri=ipe_allen2012_hyp(vectOri[0]["magVal"])

	layers1,layers2,layers3=[],[],[]
	if MMIint is not None:
		for i in range(len(MMIint["r"])):
			if MMIint["r"][i] < (2.5*111.1):
				txtLat.append(lat[0]-(MMIint["r"][i]/111.1))
				txtLon.append(lon[0])
				txtAnot.append(str(roman(int(MMIint["I"][i])))+" Intensity")
				layers1.append(
				{
					"source": (gdf.set_crs("epsg:4326")
						.sample(1)
						.pipe(lambda d: d.to_crs(d.estimate_utm_crs()))["geometry"]
						.centroid.buffer(MMIint["r"][i]*1000, cap_style=1)
						.to_crs("epsg:4326")
						.__geo_interface__),
					"type": "line",
					"color": "black",
					"line": {"width": 1.5},
				})
	for j in sDict["sDist"]:
		if j < (2.5*111.1):
			layers2.append(
			{
				"source": (gdf.set_crs("epsg:4326")
					.sample(1)
					.pipe(lambda d: d.to_crs(d.estimate_utm_crs()))["geometry"]
					.centroid.buffer(j*1000, cap_style=1)
					.to_crs("epsg:4326")
					.__geo_interface__),
				"type": "line",
				"color": "black",
				"line": {"width": 1.5,"dash":[1.0,1.5]},
			})
	if MMIintOri is not None:
		for k in range(len(MMIintOri["r"])):
			if MMIintOri["r"][k] < (2.5*111.1):
				txt2Lat.append(latOris[active_tab]-(MMIintOri["r"][k]/111.1))
				txt2Lon.append(lonOris[active_tab])
				txt2Anot.append(str(roman(int(MMIintOri["I"][k])))+" Intensity")
				layers3.append(
					{
						"source": (gdf2.set_crs("epsg:4326")
							.sample(1)
							.pipe(lambda d: d.to_crs(d.estimate_utm_crs()))["geometry"]
							.centroid.buffer(MMIintOri["r"][k]*1000, cap_style=1)
							.to_crs("epsg:4326")
							.__geo_interface__),
						"type": "line",
						"color": "green",
						"line": {"width": 1.5},
					})
	layers = layers3 + layers2 + layers1 + layerStaN + layerSta + layerOris + layerOri + layerEve 

	#Add symbols with circles information
	fig.add_trace(go.Scattermapbox(
		lat = txtLat,
		lon = txtLon,
		text = txtAnot,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		mode = 'markers',
		marker = dict(
			# opacity=0.5,
			color = "black",
#			line_color='rgb(40,40,40)',
			# symbol="star",
			# symbol='',
			size = 5,
#			line_width=0.5,
			sizemode = 'area')
		))

	#Add symbols with circles information
	fig.add_trace(go.Scattermapbox(
		lat = txt2Lat,
		lon = txt2Lon,
		text = txt2Anot,
		showlegend=False,
		hovertemplate=
			"%{text}"+
			"<extra></extra>",
		mode = 'markers',
		marker = dict(
			# opacity=0.5,
			color = "green",
#			line_color='rgb(40,40,40)',
			# symbol="star",
			# symbol='',
			size = 5,
#			line_width=0.5,
			sizemode = 'area')
		))

	fig.update_layout(mapbox_layers=layers)
	# fig = fig.update_layout(mapbox_layers=list(layers.values()))
	# fig = fig.update_layout(mapbox_layers=layers_int)

	fig.update_layout(
		# height=800,
		margin={"r":0,"t":0,"l":0,"b":0},
		mapbox = dict(
			accesstoken=mapbox_access_token,
			center = {'lat':lat[0],'lon':lon[0]},
			zoom=6,
#			style="carto-positron"
			style="mapbox://styles/olimac/cl30nl1kz003r14pp2jy20vrx",
#mapbox://styles/olimac/cl144ojyu004l16s236ersrko"
			),
		modebar_add=['drawline',
			'drawopenpath',
			'drawclosedpath',
			'drawcircle',
			'drawrect',
			'eraseshape'],
	)
	return fig


#		dbc.Row(
#		[
#			dbc.Col(
#				html.Div([
#				"Input: ",
#				dcc.Input(id='my-input', value='initial value', type='text')
#				]),
#			)
#		]),

