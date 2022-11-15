#!/usr/bin/python
 # -*- coding: utf-8 -*-

#from seiscomp3.fdsnws.availability import AvailabilityExtent, AvailabilityQuery
#print AvailabilityQuery()
import MySQLdb
import os, sys, traceback
from seiscomp3.Client import Application, Inventory
from seiscomp3 import Core, DataModel, IO, Logging, System
from obspy import UTCDateTime
#repoName = Application.Instance()._daRepositoryName
#db = IO.DatabaseInterface.Open(Application.Instance().databaseURI())
#db = IO.DatabaseInterface.Open(Application.Instance().databaseURI())

################################################################################
class DataAvailabilityCache(object):

	#---------------------------------------------------------------------------
	def __init__(self, app, da, validUntil):
		self._da            = da
		self._validUntil    = validUntil
		self._extents       = {}
		self._extentsSorted = []
		self._extentsOID    = {}

		for i in xrange(self._da.dataExtentCount()):
			ext = self._da.dataExtent(i)
			wid = ext.waveformID()
			sid = "%s.%s.%s.%s" % (wid.networkCode(), wid.stationCode(),
			                       wid.locationCode(), wid.channelCode())
			restricted = app._openStreams is None or sid not in app._openStreams
			if restricted and not app._allowRestricted:
				continue
			self._extents[sid] = (ext, restricted)
			#Logging.debug("%s: %s ~ %s" % (sid, ext.start().iso(),
			#                               ext.end().iso()))

		if app._serveAvailability:
			# load data attribute extents if availability is served
			for i in xrange(da.dataExtentCount()):
				extent = da.dataExtent(i)
				app.query().loadDataAttributeExtents(extent)

			# create a list of (extent, oid, restricted) tuples sorted by stream
			self._extentsSorted = [ (e, app.query().getCachedId(e), res) \
			        for wid, (e, res) in sorted(self._extents.iteritems(),
			                                    key=lambda t: t[0]) ]

			# create a dictionary of object ID to extents
			self._extentsOID = dict((oid, (e, res)) \
			        for (e, oid, res) in self._extentsSorted)

		Logging.info("loaded %i extents" % len(self._extents))

	#---------------------------------------------------------------------------
	def extentsOID(self):
		return self._extentsOID

	#---------------------------------------------------------------------------
	def extentsSorted(self):
		return self._extentsSorted

	#---------------------------------------------------------------------------
	def validUntil(self):
		return self._validUntil

	#---------------------------------------------------------------------------
	def extent(self, net, sta, loc, cha):
		wid = "%s.%s.%s.%s" % (net, sta, loc, cha)
		if wid in self._extents:
			return self._extents[wid][0]

		return None

################################################################################
class avail(Application):
	def __init__(self, start, end, period):
		Application.__init__(self, len(sys.argv), sys.argv)
		self.setMessagingEnabled(True)
		self.setDatabaseEnabled(True, True)
		self.setRecordStreamEnabled(True)
		self.setLoadInventoryEnabled(True)
		self.period = period
		self.start = start
		self.end = end
		self._daEnabled         = True
		self._daCacheDuration   = 300
		self._daCache           = None
#		self._openStreams       = None
		self._serveAvailability = True
		self._serveDataSelect   = True
		self._allowRestricted   = True
#		self._userdb        = UserDB()
#		self._access        = Access()
		# Leave signal handling to us
		Application.HandleSignals(False, False)

	#---------------------------------------------------------------------------
	def getDACache(self):
		now = Core.Time.GMT()
		# check if cache is still valid
		if self._daCache is None or now > self._daCache.validUntil():

			if self.query() is None or \
			   not self.query().driver().isConnected():
				dbInt = IO.DatabaseInterface.Open(self.databaseURI())
				if dbInt is None:
					Logging.error('failed to connect to database')
					return self._daCache
				else:
					self.setDatabase(dbInt)

			da = DataModel.DataAvailability()
			self.query().loadDataExtents(da)
			validUntil = now + Core.TimeSpan(self._daCacheDuration, 0)
			self._daCache = DataAvailabilityCache(self, da, validUntil)

		return self._daCache

	#---------------------------------------------------------------------------
	def extentIter(self, dac):
		# tupel: extent, oid, restricted
		for e in dac.extentsSorted():
			ext = e[0]
			restricted = e[2]
			yield e

	#---------------------------------------------------------------------------
	def _formatTime(self, time, ms=False):
		if ms:
			return '{0}.{1:06d}Z'.format(time.toString('%FT%T'),
			                             time.microseconds())
		return time.toString('%FT%TZ')

	#---------------------------------------------------------------------------
	def run(self):
		dataSelectInv = None
		dataSelectInv = Inventory.Instance().inventory()
		# availability
		if self._serveAvailability:

			# create a set of waveformIDs which represent open channels
			if self._serveDataSelect:
				openStreams = set()
				for iNet in xrange(dataSelectInv.networkCount()):
					net = dataSelectInv.network(iNet)
#					if utils.isRestricted(net): continue
					for iSta in xrange(net.stationCount()):
						sta = net.station(iSta)
#						if utils.isRestricted(sta): continue
						for iLoc in xrange(sta.sensorLocationCount()):
							loc = sta.sensorLocation(iLoc)
							for iCha in xrange(loc.streamCount()):
								cha = loc.stream(iCha)
#								if utils.isRestricted(cha): continue
								openStreams.add("{0}.{1}.{2}.{3}".format(
								                net.code(), sta.code(),
								                loc.code(), cha.code()))
				self._openStreams = openStreams
			else:
				self._openStreams = None
#			print self._openStreams

			dac = self.getDACache()
			i = 0
			idList = []
			parentOIDs = []
			for ext, objID, restricted in self.extentIter(dac):
				if i < 1000:
					idList.append(objID)
					i += 1
				else:
					parentOIDs.append(idList)
					idList = [ objID ]
					i = 1
			if len(idList) > 0:
				parentOIDs.append(idList)

			db = IO.DatabaseInterface.Open(self.databaseURI())
			lines = self._lineIter(db, parentOIDs, dac.extentsOID())
			self.d = {}
			self.d_avail = {}
			thr = 4


			nslc        = '{0: <2} {1: <5} {2: <2} {3: <3}'
			time        = ' {0: >27} {1: >27}'
			for line in lines:
				wid = line[0].waveformID()
				e   = line[1]
				loc = wid.locationCode() if wid.locationCode() else "--"
				mseedid = wid.networkCode()+"."+wid.stationCode()+"."+loc+"."+wid.channelCode()

				if len(self.d) == 0:
					self.d = {mseedid: {'e':[e]}}
				elif mseedid in self.d:
					self.d[mseedid]['e'].append(e)
				else:
					self.d[mseedid] = {'e':[e]}

				data = nslc.format(wid.networkCode(), wid.stationCode(),
				                   loc, wid.channelCode())
				data += time.format(self._formatTime(e.start(), True),
				                    self._formatTime(e.end(), True))
				data += '\n'

			for ID, values in self.d.items():
				avail = 0
				for i in range(len(values['e'])):
					s = UTCDateTime(values['e'][i].start())
					e = UTCDateTime(values['e'][i].end())
					s_period = UTCDateTime(self.start)
					e_period = UTCDateTime(self.end)
					if s < s_period and e > e_period:
						avail += e_period-s_period
					elif s > s_period and e > e_period:
						avail += e_period-s
					elif s < s_period and e < e_period:
						avail += e-s_period
					else:
						avail += e-s
				porc = (avail*100)/self.period
				if porc < thr:
					if len(self.d_avail) == 0:
						self.d_avail = {ID:{"avail_value":avail,"porc":round(porc,1)}}
					else:
						self.d_avail[ID]={"avail_value":avail,"porc":round(porc,1)}
			print self.d_avail
		return True

	#---------------------------------------------------------------------------
	def _lineIter(self, db, parentOIDs, oIDs):
		def _T(name):
			return db.convertColumnName(name)

		dba = DataModel.DatabaseArchive(db)
		for idList in parentOIDs:
			IDS = ','.join(str(x) for x in idList)
			# build SQL query
			q = 'SELECT * from DataSegment ' \
			    'WHERE _parent_oid IN ({0}) ' \
			    .format(IDS)
#			q = 'SELECT * from DataSegment ' \
#			    'WHERE _parent_oid IN (10060384, 10060918, 10060961) ' \
#			    .format(ID)
			q += "AND {0} >= '{1}' " \
				.format(_T('end'), self.start)
			q += "AND {0} < '{1}' " \
				.format(_T('start'), self.end)
			q += 'ORDER BY _parent_oid, {0}, {1}' \
				.format(_T('start'), _T('start_ms'))
			segIt = dba.getObjectIterator(q, DataModel.DataSegment.TypeInfo())
			seg = None
			ext = None
			lines = 0
			while seg is None or segIt.next():
				s = DataModel.DataSegment.Cast(segIt.get())
				if s is None:
					break
				try:
					e, restricted = oIDs[segIt.parentOid()]
				except KeyError:
					Logging.warning("parent object id not found: %i",
							      segIt.parentOid())
					continue
				# first segment, no merge test required
				if seg is None:
					seg = s
					ext = e
					jitter = 1 / (2 * s.sampleRate())
					continue

				# merge test
				diff = float(s.start() - seg.end())
				if e is ext and \
					s.quality() == seg.quality() and \
					s.sampleRate() == seg.sampleRate() and \
					diff <= jitter and \
					-diff <= jitter:

					seg.setEnd(s.end())
					if s.updated() > seg.updated():
						seg.setUpdated(s.updated())

				# merge was not possible, yield previous segment
				else:
					yield (ext, seg, restricted)
					lines += 1
					seg = s
					ext = e
					if seg.sampleRate() != s.sampleRate():
						jitter = 1 / (2 * s.sampleRate())

			if seg is not None:
				yield (ext, seg, restricted)
			return

start = "2019-05-20T15:30:00"
end = "2019-05-21T00:00:00"

#start = "2018-01-01T00:00:00"
#end = "2022-01-01T00:00:00"

startUTC = UTCDateTime(start)
endUTC = UTCDateTime(end)
period = endUTC-startUTC

app = avail(start, end, period)
sys.exit(app())


##		dccName = seiscomp3.Client.Application.Instance()._daDCCName
#		db = IO.DatabaseInterface.Open(seiscomp3.Client.Application.Instance().databaseURI())
#		test = seiscomp3.Client.Application.Instance()._daRepositoryName

#def availQuery(host,usr,pss,db):
#	db = MySQLdb.connect(host=host,    # your host, usually localhost
#		                user=usr,         # your username
#		                passwd=pss,  # your password
#		                db=db)        # name of the data base
#	cur = db.cursor()
#	#cur.execute("show databases")
#	cur.execute("\
#			SELECT * \
#			FROM DataSegment \
#			WHERE _parent_oid IN ({0})\
#				AND {1} >= '{2}' \
#				AND {3} < '{4}' \
#				ORDER BY _parent_oid, {5}, {6}".format(','.join(str(x) for x in idList),_T('end'),start,_T('start'),end,_T('start'),_T('start_ms')))
#	i=0
#	for fila in cur.fetchall():


#				chan = {'stream':mseedid,'e':[e]}
#					self.d.append(chan)
#				elif mseedid in self.d['stream']:
#					cond0 = 0
#					for i in range(len(self.d)):
#						if mseedid == self.d[i]["stream"]:
#							cond0 = 1
#							self.d[i]['e'].append(e)
#					if cond0 == 0:
#						self.d.append(chan)
