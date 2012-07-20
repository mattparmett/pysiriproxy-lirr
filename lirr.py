import re
import mechanize
from bs4 import BeautifulSoup
import csv
from datetime import datetime, date, time
import dateutil.parser
import time
import sys


class TrainTime():
 	def __init__(self, t):
		self.t = t

	@classmethod
	def round(self, seconds = 60):
		return time((self.t / seconds).round * seconds)
  
	@classmethod
	def floor(self, seconds = 60):
		return time((self.t / seconds).floor * seconds)
  
	@classmethod
	def ceiling(self, seconds = 60):
		a = self.floor(seconds)
		return a + seconds
  
class StationError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Station:
	#args = [name/id, stations_csv_file]
	def __init__(self, *args):
		if isinstance(args[1], basestring):
			data = csv.reader(open(args[1], "rb"))
		else:
			data = csv.reader(open("stations.csv", "rb"))
		
		#If argument passed is name, assign name and get id. If id, assign id and get name.
		if isinstance(args[0], basestring):
			for row in data:
				if row[1] == args[0]:
					self.id = row[0]
					self.name = args[0]
				elif row[0] == args[0]:
					self.name = row[1]
					self.id = args[0]
		else:
			raise StationError, "Station not found."

class Train:
	
	def __init__(self, dep_time, from_station, arr_time, to_station, trans_station, trans_time, duration, peak):
		#from, to, and trans_station should all be Station objects.  Therefore, need to catch StationError.
		try:
			self.dep_time = dep_time
			self.from_station = from_station
			self.from_station_name = self.from_station.name
			self.from_station_id = self.from_station.id
			self.arr_time = arr_time
			self.to_station = to_station
			self.to_station_name = self.to_station.name
			self.to_station_id = self.to_station.id
			if isinstance(trans_station, basestring):
				self.trans_station = trans_station
				self.trans_station_name = self.trans_station.name
				self.trans_station_id = self.trans_station.id
			
			self.trans_time = trans_time
			self.duration = duration
			self.peak = peak
		except StationError:
			print "Station invalid."
	
	def has_transfer():
		if self.trans_station_name is None and self.trans_time is None: #changed from length to nil
			return false
		else:
			return true
	
	def peak():
		if self.peak == "Peak":
			return true
		else:
			return false

	def to_siri():
		if self.has_transfer() == true:
			return "The next train from " + self.from_station_name + " to " + self.to_station_name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + ", with a transfer at " + self.trans_station_name + " at " + self.trans_time + "."

		else:
			return "The next train from " + self.from_station_name + " to " + self.to_station_name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + "."
		

	def to_timetable():
		if self.has_transfer() == true:
			return self.dep_time + " - " + self.trans_time + " - " + self.arr_time
		else:
			return self.dep_time + " - " + self.arr_time

#End Classes
###

###
#Begin methods

#Takes station name and converts it to numerical ID, returned as a string
def convertStationToID(station_name, station_csv_file = "stations.csv"):
	data = csv.reader(open(station_csv_file, "rb"))
	try:
		for row in data:
			if row[1] == station_name:
				return row[0]
	except StationError:
		print "Station not found."

def getTodaysDate():
	time = datetime.now()
	
	#Get correctly formatted month string
	if time.month < 10:
		month_string = "0" + str(time.month)
	else:
		month_string = str(time.month)
	
	#Get correctly formatted day string
	if time.day < 10:
		day_string = "0" + str(time.day)
	else:
		day_string = str(time.day)
	
	#Combine into one super date string
	date_string = month_string + "/" + day_string + "/" + str(time.year)
	
	return date_string

def getTime():
	t = datetime.time(datetime.now())
	return time.strftime("%I:%M", time.localtime())

def getAMPM():
	t = datetime.time(datetime.now())
	return time.strftime("%p", time.localtime())

#Takes search parameters and writes search result timetable to 'results.csv'
#Returns an array of 5 Trains, each of which represents an individual train result.
#args = [from_station, to_station, request_time_value, request_am_pm_value, request_date, station_csv_file]
def getTrainTimes(*args):
	#Assign more useful variable names to args
	if isinstance(args[5], basestring):
		station_csv_file = args[5]
	else:
		station_csv_file = "stations.csv"
	
	try:
		from_station_id = args[0].id
	except StationError:
		print("Invalid departure station: " + args[0] + ".")
	
	try:
		to_station_id = args[1].id
	except StationError:
		abort("Invalid destination station: " + args[1] + ".")
	
	if args[2] != 0:
		request_time_value = args[2]
	else:
		request_time_value = getTime()
	
	if args[3] != 0:
		request_am_pm_value = args[3]
	else:
		request_am_pm_value = getAMPM()
	
	if args[4] != 0:
		request_date_value = args[4]
	else:
		request_date_value = getTodaysDate()
	
	#Create mechanize agent
	a = mechanize.Browser()
	
	#Get lirr schedule search page
	a.open("http://lirr42.mta.info/")
	
	#Select search form
	a.select_form(name="index")
	
	#Set search form parameters
	#Make sure stations are valid!
	a['FromStation'] = [from_station_id]
	a['ToStation'] = [to_station_id]
	a['RequestTime'] = ['10:00']
	a['RequestAMPM'] = ['PM']	
	#a['RequestTime'] = [request_time_value]
	#a['RequestAMPM'] = [request_am_pm_value]
	a['RequestDate'] = request_date_value

	#Select submit button for schedules
	#button = search_form.button_with(:name => 'schedules')

	#Submit search form
	r = a.submit()
	
	#Select table elements in the results page, and put the html and inner text into an array
	assert a.viewing_html()
	results = BeautifulSoup(r.read())
	elements = []
	print results.find_all('td', attrs={'class' : "schedulesTD"})
	for tag in results.find_all('td', attrs={'class' : "schedulesTD"}):
		elements.append(tag.string)

	#Loop to iterate through results and extract and write the inner text elements to the csv file
	i = 1
	trains = []
	train_info = []
	for t in elements:
		if i<= 1 or i == 4 or i == 8:
			i = i + 1
		elif i < 9:
			train_info.append(t.string)
			i = i + 1
		elif i == 9:
			train_info.append(t.string)
			try:
				train = Train(train_info[0], Station(from_station_id, station_csv_file), train_info[1], Station(to_station_id, station_csv_file), Station(train_info[2], station_csv_file), train_info[3], train_info[4], train_info[5])
			except StationError:
				print("Station invalid.")
			trains.append(train)
			train_info = []
			i = 1
	
	#Return array of relevant trains 
	return trains


#Takes a pair of stations and returns the next Train object that makes the specified trip.
#args = [from_station, to_station, station_csv_file]
def getNextTrain(*args):
	#Set args
	if isinstance(args[0], Station) and isinstance(args[1], Station):
		from_station = args[0]
		to_station = args[1]
	else:
		print("Invalid station specified for getNextTrain.")
	
	if isinstance(args[2], basestring):
		station_csv_file = args[2]
		#puts station_csv_file
	else:
		station_csv_file = "stations.csv"
	
	#Get current time, rounded to the next 15 mins for search purposes
	#t = TrainTime(int(round(time.localtime())))
	#t = t.ceiling(15*60)
	t = time.strftime("%I:%M", time.localtime())
	#time = Time.now.ceiling(15*60).strftime("%I:%M")
	
	#Run train search to find 5 trains around the current rounded time
	try:
		trains = getTrainTimes(from_station, to_station, t, getAMPM(), getTodaysDate(), station_csv_file)
	except StationError:
		print("Stationerror right after time and search")
	
	#Get and return the next train!
	for train in trains:
		departure_time = dateutil.parser.parse(train.dep_time)
		if departure_time > datetime.now():
			return train

	#trains.each do |train|
	#	departure_time = Time.parse(train.dep_time)
	#	if departure_time > Time.now
	#		return train #Returns the first train with departure time after current time
	#	end
	#end
	
	return [] #No trains found
	

#End Methods
###

###
#Begin code body

stations_csv_file = "stations.csv"

from_station = Station("Penn Station", stations_csv_file)
to_station = Station("Deer Park", stations_csv_file)
train = getNextTrain(from_station, to_station, stations_csv_file)
if train == []:
	print("No trains found.")
else:
	print(train.to_siri())

#End code body
###
