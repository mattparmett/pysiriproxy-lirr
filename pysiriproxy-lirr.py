#pysiriproxy plugin for searching LIRR timetables
import mechanize
import html5lib
from html5lib import treebuilders
import csv
import time
import datetime
import math

from pysiriproxy.plugins import BasePlugin, SpeechPacket, StartRequest, matches, regex, ResponseList


class Plugin(BasePlugin):
	name = "lirr"
	stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv" #Edit to make user-configurable
	

	@regex("(when is|when's) the next train from ([a-z ]*) to ([a-z ]*) ")
	def nextTrainRegex(self, text):
		text = text.replace("When is the next train from ","")
		text = text.replace(" to ",",")
		stations = text.split(",")
		stations[0] = stations[0].split(" ")
		from_station_name = ""
		for a in reversed(stations[0]):
			if a != "from":
				from_station_name = a + " " + from_station_name
			if a == "from":
				break
		to_station_name = stations[1]
		print from_station_name[0:-1].title() + "."
		print to_station_name.title() + "."
		try:	
			train = nextTrain(from_station_name[0:-1].title(), to_station_name.title(), self.stations_csv_file)
		except StationError as e:
			raise StationError(e.value)
		self.say(train.to_siri())
		self.completeRequest()

	@regex("(when is|when's) the next train from ([a-z ]*) to ([a-z]*)")
	def nextTrainRegex2(self, text):
		text = text.replace("When is the next train from ","")
		text = text.replace(" to ",",")
		stations = text.split(",")
		stations[0] = stations[0].split(" ")
		from_station_name = ""
		for a in reversed(stations[0]):
			if a != "from":
				from_station_name = a + " " + from_station_name
			if a == "from":
				break
		from_station_name = from_station_name[0:-1].title()
		to_station_name = stations[1].title()
		try:	
			train = nextTrain(from_station_name, to_station_name, self.stations_csv_file)
		except StationError as e:
			raise StationError(e.value)
		self.say(train.to_siri())
		self.completeRequest()

	@regex("get the train times for ([a-z ]*) to ([a-z ]*) ")
	def timetableRegex(self, text):
		text = text.replace("get the train times for ","")
		text = text.replace(" to ",",")
		stations = text.split(",")
		stations[0] = stations[0].split(" ")
		from_station_name = ""
		for a in reversed(stations[0]):
			if a != "for":
				from_station_name = a + " " + from_station_name
			if a == "for":
				break
		from_station_name = from_station_name[0:-1].title()
		to_station_name = stations[1].title()
		print from_station_name
		print to_station_name
		trains = trainSchedule(from_station_name, to_station_name)
		timetable = ""
		for train in reversed(trains):
			timetable = train.to_timetable() + "\n" + timetable
		self.say("Here are the train times for " + from_station_name + " to " + to_station_name + ":\n\n" + timetable, spoken="Here are the train times for " + from_station_name + " to " + to_station_name + ".")
		self.completeRequest()

	@regex("get the train times for ([a-z ]*) to ([a-z]*)")
	def timetableRegex2(self, text):
		text = text.replace("get the train times for ","")
		text = text.replace(" to ",",")
		stations = text.split(",")
		stations[0] = stations[0].split(" ")
		from_station_name = ""
		for a in reversed(stations[0]):
			if a != "for":
				from_station_name = a + " " + from_station_name
			if a == "for":
				break
		from_station_name = from_station_name[0:-1].title()
		to_station_name = stations[1].title()
		print from_station_name
		print to_station_name
		trains = trainSchedule(from_station_name, to_station_name)
		timetable = ""
		for train in reversed(trains):
			timetable = train.to_timetable() + "\n" + timetable
		self.say("Here are the train times for " + from_station_name + " to " + to_station_name + ":\n\n" + timetable, spoken="Here are the train times for " + from_station_name + " to " + to_station_name + ".")
		self.completeRequest()

###Other classes
class TrainTime():
	def __init__(self, t):
		self.t = t
	
	def floor(self, seconds = 60):
		self.t = math.floor(self.t / seconds) * seconds
		return self.t

	def ceiling(self, seconds = 60):
		self.t = self.floor(seconds) + seconds
		return self.t
	
	def to_time(self):
		return time.strftime("%I:%M", time.localtime(self.t))

class StationError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Station():
	def __init__(self, **args):
		#Set up csv parser		
		try:
			if isinstance(args['stations_csv_file'], basestring):
				reader = csv.reader(open(args['stations_csv_file'], 'rb'))
			else:
				reader = csv.reader(open("/home/matt/.pysiriproxy/plugins/stations.csv", 'rb'))
		except KeyError:
			reader = csv.reader(open("/home/matt/.pysiriproxy/plugins/stations.csv", 'rb'))
		
		#Check if we have both name and id, if so just assign them
		try:
			self.name = args['name']
			self.has_name = True
		except KeyError:
			self.has_name = False
		try:
			self.id = args['id']
			self.has_id = True
		except KeyError:
			self.has_id = False

		#If we have name, look up id
		if self.has_name == True and self.has_id == False:
			self.name = args['name']
			for row in reader:
				if row[1] == args['name']:
					self.id = row[0]
			#Name not in csv file
			if not hasattr(self, 'id'):
				raise StationError("Invalid station name specified.")
		
		#We have id, so look up name
		if self.has_name == False and self.has_id == True:
			self.id = args['id']
			for row in reader:
				if row[0] == args['id']:
					self.name = row[1]
			#ID not in csv file
			if not hasattr(self, 'name'):
				raise StationError("Invalid station id specified.")

		#We have neither, so throw an error
		if self.has_name == False and self.has_id == False:		
			raise StationError('Error: no station specified.  Must pass station name or id.')

class Train():
	#args: dep_time, from_station, arr_time, to_station, trans_station, trans_time, duration, peak
	def __init__(self, **args):
		#Assign instance vars
		#from, to, and trans_station are all Stations, so need to catch StationError
		try:
			self.dep_time = args['dep_time']
			self.from_station = args['from_station']
			#self.from_station.name = args['from_station'].name
			#self.from_station.id = args['from_station'].id
			self.arr_time = args['arr_time']
			self.to_station = args['to_station']
			#self.to_station.name = args['to_station'].name
			#self.to_station.id = args['to_station'].id
			self.duration = args['duration']
			self.peak = args['peak']
		except KeyError as e:
			raise KeyError("Error: " + str(e) + " not specified.")
		except AttributeError as e:
			raise AttributeError(e.value)
		except StationError as e:
			raise StationError(e.value)
		#Transfer info, is optional because only some trains have transfers
		try:
			self.trans_station = args['trans_station']
			#self.trans_station.name = args['trans_station'].name
			#self.trans_station.id = args['trans_station'].id
			self.trans_time = args['trans_time']
		except KeyError as e:
			self.has_transfer = False
		else:
			self.has_transfer = True


	def peak(self):
		if self.peak == "Peak":
			return True
		else:
			return False

	def to_siri(self):
		if self.has_transfer == True:
			return "The next train from " + self.from_station.name + " to " + self.to_station.name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + ", with a transfer at " + self.trans_station.name + " at " + self.trans_time + "."

		else:
			return "The next train from " + self.from_station.name + " to " + self.to_station.name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + "."

	def to_timetable(self):
		if self.has_transfer == True:
			return self.dep_time + " - " + self.trans_time + " - " + self.arr_time
		else:
			return self.dep_time + " - " + self.arr_time

###End classes

###Begin lib methods
def convertStationToID(station_name, stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	try:	
		reader = csv.reader(open(stations_csv_file, 'rb'))
	except IOError as e:
		raise StationError("File " + stations_csv_file + " not found.")
	for row in reader:
		if row[1] == station_name:
			return row[0]
	raise StationError("Error: station name \"" + station_name + "\" not found in " + stations_csv_file)

def convertIDToStation(station_id, stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	try:
		reader = csv.reader(open(stations_csv_file, 'rb'))
	except IOError as e:
		raise StationError("File " + stations_csv_file + " not found.")

	for row in reader:
		if row[0] == str(station_id):
			return row[1]

	raise StationError("Error: station id " + str(station_id) + " not found in " + stations_csv_file)


def getTime():
	t = time.time()
	return time.strftime("%I:%M", time.localtime(t))

def getTimeCeiling(sec, s = time.time()):
	t = TrainTime(s)
	t.ceiling(sec)
	return t.to_time()

def getTimeFloor(sec):
	t = TrainTime(time.time())
	t.floor(sec)
	return t.to_time()

def getAMPM():
	t = time.time()
	return time.strftime("%P", time.localtime(t))

def getTodaysDate():
	now = datetime.datetime.now()
	
	#Get correctly formatted month string
	if now.month < 10:
		month_string = "0" + str(now.month)
	else:
		month_string = str(now.month)

	#Get correctly formatted day string
	if now.day < 10:
		day_string = "0" + str(now.month)
	else:
		day_string = str(now.day)

	#Combine into one super date string
	date_string = month_string + "/" + day_string + "/" + str(now.year)
	return date_string

#args: from_station, to_station, request_time, request_am_pm, request_date, stations_csv_file
def getTrainTimes(**args):
	#Assign useful names to args
	try:
		stations_csv_file = args['stations_csv_file']
	except KeyError as e:
		stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"

	try:
		from_station = args['from_station']
	except KeyError as e:
		raise StationError("Error: no from_station specified")
	try:
		to_station = args['to_station']
	except KeyError as e:
		raise StationError("Error: no to_station specified")
	
	try:
		request_time = args['request_time']
	except KeyError as e:
		request_time = getTimeCeiling(15*60)
		
	
	try:
		request_am_pm = args['request_am_pm']
	except KeyError as e:
		request_am_pm = getAMPM()

	try:
		request_date = args['request_date']
	except KeyError as e:
		request_date = getTodaysDate()

	#Create Mechanize agent
	br = mechanize.Browser()

	#Get lirr schedule search page
	br.open("http://lirr42.mta.info")

	#Select search form
	br.select_form(name="index")

	#Set search form parameters
	#Need to catch if stations aren't Station objects -- TODO
	br['FromStation'] = [from_station.id]
	br['ToStation'] = [to_station.id]
	br['RequestTime'] = [request_time]
	br['RequestAMPM'] = [request_am_pm.upper()]	
	br['RequestDate'] = request_date

	#Submit search form
	r = br.submit()

	#Select table elements in the results page
	html = r.read()	
	parser = html5lib.HTMLParser(tree = treebuilders.getTreeBuilder("beautifulsoup"))
	tree = parser.parse(html)
	results = tree.findAll('td', {'class': 'schedulesTD'})

	#Add all relevant elements to master list
	elements = []
	for t in results:
		elements.append(t)

	#Sort master list into Trains
	i = 1
	trains = []
	train_info = []
	for e in elements:
		if i <= 1 or i == 4 or i == 8:
			i = i + 1
		elif i < 9:
			train_info.append(e)
			i = i + 1
		elif i == 9:
			train_info.append(e)
			#Finished with info for this Train, so add it to result array & reset train info array
			dep_time = str(train_info[0].string)
			arr_time = str(train_info[1].string)
			from_station = Station(id = from_station.id, stations_csv_file = stations_csv_file)
			to_station = Station(id = to_station.id, stations_csv_file = stations_csv_file)
			duration = str(train_info[4].string)
			peak = str(train_info[5].string)

			try: #Check if there is a transfer station
				#Remove asterisk from station name
				name = str(train_info[2].string).replace("*","")
				trans_station = Station(name = name, stations_csv_file = stations_csv_file)
			except StationError as e: #No transfer, so create Train accordingly
				train = Train(dep_time = dep_time, from_station = from_station, arr_time = arr_time, to_station = to_station, duration = duration, peak = peak)
			
			else: #There is a transfer
				trans_time = str(train_info[3].string)
				train = Train(dep_time = dep_time, from_station = from_station, arr_time = arr_time, to_station = to_station, trans_station = trans_station, trans_time = trans_time, duration = duration, peak = peak)

			
			trains.append(train)
			train_info = []
			i = 1
	return trains

def getNextTrain(from_station, to_station, stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	#Get current time, rounded to the next 15 min for search purposes
	t = getTimeCeiling(15*60)

	#Run train search to find 5 trains around the current rounded time
	try:
		trains = getTrainTimes(to_station = to_station, from_station = from_station)
	except StationError as e:
		print e.value
	
	#Get and return next train
	for train in trains:
		train_time = time.strptime(train.dep_time + " " + str(datetime.datetime.now().month) + " " + str(datetime.datetime.now().day) + " " + str(datetime.datetime.now().year), "%I:%M %p %m %d %Y")

		if train_time > time.localtime():
			return train

	#Else, return nothing
	return None

### End lib methods

###Some methods to make the code cleaner within speech rules.
def nextTrain(from_station_name, to_station_name, stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	from_station = Station(name=from_station_name, stations_csv_file = stations_csv_file)
	to_station = Station(name=to_station_name, stations_csv_file = stations_csv_file)
	train = getNextTrain(from_station, to_station, stations_csv_file)
	return train

def trainSchedule(from_station_name, to_station_name, stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	from_station = Station(name=from_station_name, stations_csv_file = stations_csv_file)
	to_station = Station(name=to_station_name, stations_csv_file = stations_csv_file)
	trains = getTrainTimes(from_station = from_station, to_station = to_station, request_time = getTimeCeiling(15*60), request_am_pm = getAMPM(), request_date = getTodaysDate(), stations_csv_file = stations_csv_file)
	return trains

def trainSearch(from_station_name, to_station_name, train_time = getTimeCeiling(15*60), am_pm = getAMPM(), date = getTodaysDate(), stations_csv_file = "/home/matt/.pysiriproxy/plugins/stations.csv"):
	from_station = Station(name=from_station_name, stations_csv_file = stations_csv_file)
	to_station = Station(name=to_station_name, stations_csv_file = stations_csv_file)
	
	#Correct AM/PM
	if am_pm != "AM" and am_pm != "PM":
		am_pm = getAMPM()
	
	#Get time ceiling
	tm = time.strptime(train_time + " " + date, "%I:%M %m/%d/%Y")
	t = getTimeCeiling(15*60, time.mktime(tm))

	trains = getTrainTimes(from_station = from_station, to_station = to_station, request_time = t, request_am_pm = am_pm, request_date = date, stations_csv_file = stations_csv_file)
	return trains
###



