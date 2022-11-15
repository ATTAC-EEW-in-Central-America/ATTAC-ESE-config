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

from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
try:
    import events_dash
    import event_dash
except:
    print('No event(s) dashboards')

import sys
import configparser

external_stylesheets=[dbc.themes.BOOTSTRAP]
config = configparser.RawConfigParser()
config.read("/opt/seiscomp/share/sceewv/apps.cfg")
cfg = dict(config.items('index'))
alert = cfg['alert']
alert = False if alert == 'False' else alert
alert = True if alert == 'True' else alert
if alert:
	alertPath = cfg['alertpath']
	sys.path.append(alertPath)
	import dashboard
host = cfg['host']
port = cfg['port']

external_stylesheets=[dbc.themes.BOOTSTRAP]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Store(id="storeEventID", data=None)
])

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

@callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
	if pathname == '/scqcalert':
		return dashboard.scqcalert_layout
	elif pathname == '/event':
		return event_dash.layout
	elif pathname == '/events':
		return events_dash.layout
	elif pathname == '/stations':
		return stations.layout
	elif pathname == '/networks':
		return networks.layout
	elif pathname == '/eewd':
		return eewd.layout
	else:
		return index_page

if __name__ == '__main__':
#    app.run_server(debug=True)
    app.run_server(debug=False, use_reloader=False, host=host, port=port)

