import mechanize
from bs4 import BeautifulSoup
import csv
import time
import math
import sys

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
			if isinstance(args['csv_file'], basestring):
				reader = csv.reader(open(args['csv_file'], 'rb'))
			else:
				reader = csv.reader(open("stations.csv", 'rb'))
		except KeyError:
			reader = csv.reader(open("stations.csv", 'rb'))
		
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

	def transfer(self):
		return self.has_transfer

	def peak(self):
		if self.peak == "Peak":
			return True
		else:
			return False

	def to_siri(self):
		if self.transfer() == True:
			return "The next train from " + self.from_station.name + " to " + self.to_station.name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + ", with a transfer at " + self.trans_station.name + " at " + self.trans_time + "."

		else:
			return "The next train from " + self.from_station.name + " to " + self.to_station.name + " leaves at " + self.dep_time + " and arrives at " + self.arr_time + "."

	def to_timetable(self):
		if self.transfer() == True:
			return self.dep_time + " - " + self.trans_time + " - " + self.arr_time
		else:
			return self.dep_time + " - " + self.arr_time



try:
	to = Station(name='Deer Park')
	frm = Station(name='Penn Station')
	train = Train(dep_time='12:45', from_station=frm, arr_time='1:45', to_station=to, trans_station=to, trans_time='1:15', duration='60 min', peak=True)
except StationError as e:
	print e.value
except KeyError as e:
	print str(e)
except AttributeError as e:
	print e.value
else:
	try:
		print train.to_timetable()
	except AttributeError as e:
		print "Error: " + str(e)
