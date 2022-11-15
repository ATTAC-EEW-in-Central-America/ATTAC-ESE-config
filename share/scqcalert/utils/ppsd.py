#!/usr/bin/env seiscomp-python

#obspy
from obspy import read
from obspy.io.xseed import Parser
from obspy.signal import PPSD
from obspy.core import inventory
from obspy.imaging.cm import pqlx

#FDSNWS client
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

#system
import os,sys,re
import time
import datetime
#
from multiprocessing import Pool

#Forcing to not use DISPLAY environment
import matplotlib
matplotlib.use('Agg')

#Search stations
def stas_query():
    today = UTCDateTime()
    fdsnws = "http://localhost:8080" 
    client_stas = Client(fdsnws)
    inv = client_stas.get_stations(endafter=today,level="channel",format="text",network="SV,OV,NU,GI,MX,TC,AM",channel="HN?,EN?,SN?,HH?,EH?,SH?")
    for key, v in sorted(inv.get_contents().items()):
        if key == "channels":
            stas = v
    return stas


###############################
# User's configuration values #
###############################

#num of Pools - It does not exceed the number of cores
numPools = max([1,int(os.cpu_count()/2)])

#route to seiscomp config
SCfolder="/opt/seiscomp"

#main route to store the png files
PPSDfolder="/home/insivumeh/PSD/PNG" # YEAR/NETWORK/STATION/CHANNEL/

#FDSNWS address:port to retrieve miniseed wf
fdsnwsData = "http://172.20.9.20:8080"
#FDSNWS address:port to retrieve fdsn XML response info
fdsnwsResp = "http://172.20.9.20:8080"

#Network, Station and location, channel streams
# Only for channels are accepted wildcards:
# * or ? which means Z,E,N (see channels array below)
# for example: HN? means HNZ, HNE, HNN or HH* means HHZ, HHN, HHE

streams = stas_query()
#streams = ["OV.SARO.00.HN?","OV.TOAL.00.HN?","OV.CRUC.00.HN?","OV.EART.00.HN?"]

black_loc = ["99"]

# Standard Last Char for channel code Z, E, N
#Rename in case you have something different

channels= ["Z","N","E"]

#End user's configuration
###################################


#unix timestamp for today and yesterday
todayUnix = int(time.time()) #rightnow
yesterdayUnix = todayUnix - 86400

today = datetime.datetime.fromtimestamp(todayUnix)#.strftime('%Y-%m-%d')
t = UTCDateTime(today)

yesterday = datetime.datetime.fromtimestamp(todayUnix).strftime('%Y-%m-%d')#yesterdayUnix).strftime('%Y-%m-%d')
ty= UTCDateTime(yesterday)

#Client objects - None at the beginning
clientWf = None
clientResp = None

#Empty array for appending stations and channels that will be used to obtain PPSD
selectedStreams = []

#For naming purposes
year = datetime.datetime.fromtimestamp(yesterdayUnix).strftime('%Y')
julian = datetime.datetime.fromtimestamp(yesterdayUnix).strftime('%j')

#~Unix grep in python
def grep(p,f):
    if not os.path.exists(f):
        return False
    with open(f,"r") as file_one:
        for line in file_one:
            if re.search(p, line):
                return True
    return False

#Connection to FDSNWS for Waveforms
def client_fdsnws_wf():
    try:
        clientWf = Client(fdsnwsData)
        print("Connection established to %s for waveforms" % fdsnwsData)
        return clientWf
    except Exception as e:
        print(e)
        return False

#Connection to FDSNWS for Response information
def client_fdsnws_resp():
    try:
        clientResp = Client(fdsnwsResp)
        print("connection established to %s for response" % fdsnwsResp)
        return clientResp
    except Exception as e:
        print(e)
        return False


#Request waveform data for specific stream NET.STA.LOC.CHAN
def get_miniseed(stream,begin,end):
    print("Getting waveform for:")
    print(stream+[begin, end])
    try:
        st = clientWf.get_waveforms(stream[0], stream[1], stream[2], stream[3], begin, end )
        return st
    except Exception as e:
        print("no waveform for:")
        print(stream+[begin, end ])
        print(e)
        return None

#Request the response information for specific stream NET.STA.LOC.CHAN
def get_response(stream,begin,end):
    print("Getting response for:")
    print(stream+[begin, end])
    try:
        inventory = clientResp.get_stations(network= stream[0], station= stream[1],location= stream[2], channel = stream[3], level="response" , starttime=begin, endtime=end)
        return inventory
    except Exception as e:
        print("no inventory for:")
        print(stream+[begin, end ])
        print(e)
        return None


def ppsd(stream):

    begin = ty
    end =  t

    idVal = "%s.%s.%s.%s" % (stream[0], stream[1], stream[2], stream[3])
    outname = PPSDfolder+"/"+year+"/"+stream[0]+ "/" + stream[1]+ "/"+ stream[3]+".D/"
    png = '%s/%s.%s.%s.%s.D.%s.%s.png' % ( outname,stream[0],stream[1],stream[2],stream[3],year,julian)
    npz = '%s/%s.%s.%s.%s.D.%s.%s.npz' % ( outname,stream[0],stream[1],stream[2],stream[3],year,julian)    
    
    loaded = False
    if os.path.exists(npz):
        print('Loading',npz)
        ppsd = PPSD.load_npz(npz)
        loaded = True
        if len(ppsd.times_processed):
            print('Processed:',ppsd.times_processed)
            begin = ppsd.times_processed[-1] + ppsd.step
            print('Will add:',begin,end)
        else:
            print(npz,'is empty')
            print('Will do:',begin,end)

    st = get_miniseed(stream,begin,end)
    if st == None:
        return

    inv = get_response(stream,begin,end)
    if inv == None:
        return

    tr = st.select(id=idVal)[0]
    
    if not loaded:
        ppsd = PPSD(tr.stats, metadata=inv)

    try:
        ppsd.add(st)
        print("created %s" % outname)
    except Exception as e:
        print("Error producing ppsd for {}. Error: {}".format(idVal, e))
    
    #PQLX plot, ObsPy backup
    print("plotting: %s" % outname)
    #Default output style for PPSD in ObsPy - Uncomment if needed
    #ppsd.plot(outname)
    os.makedirs(outname, exist_ok=True)
    ppsd.plot(png,cmap=pqlx,show_mode=True,show_mean=True)
    ppsd.save_npz(npz)
    
    del ppsd

    return

########################################################################

if __name__ == "__main__":

    for stream in streams:
        streamArr =  stream.split(".")
        net = streamArr[0]
        sta = streamArr[1]
        loc = streamArr[2]
        chan = streamArr[3]
        #if grep("global:", "%s/station_%s_%s" % ( SCfolder, net, sta)):
        if chan[2] == "*" or  chan[2] == "?":
        #three channels wildcard
            if loc not in black_loc:
                for c in channels:
                    selectedStreams.append([net,sta,loc,chan[:2]+c])
        else:
            if loc not in black_loc:
                selectedStreams.append([net,sta,loc,chan])
        #else:
        #    print("Station %s.%s is not configured with global binding" % (net, sta))

    #FDSNWS connection Waveforms
    clientWf=client_fdsnws_wf()
    if not clientWf:
        print("Connection not established to FDSNWS : %s for waveforms" % fdsnwsData)
        exit
    
    if fdsnwsData == fdsnwsResp:
        clientResp = clientWf
        print("Using the same fdsnws for waveforms and response")
    else:
        clientResp = client_fdsnws_resp()
        if not clientResp:
            print("Connection not established to FDSNWS : %s for response information" % fdsnwsResp)
            exit

    now = int(time.time()) #rightnow
    now = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
    print("starting the multiprocessing task at %s" % now)

    pool = Pool(numPools)
    pool.map(ppsd, selectedStreams)
    pool.close()
    pool.join()

    now = int(time.time())
    now = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
    print("ending the multithread task at %s" % now)

