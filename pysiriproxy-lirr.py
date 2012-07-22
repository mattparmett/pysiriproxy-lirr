#pysiriproxy plugin for searching LIRR timetables
from lirr import *
import time
from pysiriproxy.plugins import BasePlugin, SpeechPacket, StartRequest, matches, regex, ResponseList


###Some methods to make the code cleaner within speech rules.
def nextTrain(from_station_name, to_station_name, stations_csv_file = "stations.csv"):
	from_station = Station(name=from_station_name, stations_csv_file = stations_csv_file)
	to_station = Station(name=to_station_name, stations_csv_file = stations_csv_file)
	train = getNextTrain(from_station, to_station, stations_csv_file)
	return train

def trainSchedule(from_station_name, to_station_name, stations_csv_file = "stations.csv"):
	from_station = Station(name=from_station_name, stations_csv_file = stations_csv_file)
	to_station = Station(name=to_station_name, stations_csv_file = stations_csv_file)
	trains = getTrainTimes(from_station = from_station, to_station = to_station, request_time = getTimeCeiling(15*60), request_am_pm = getAMPM(), request_date = getTodaysDate(), stations_csv_file = stations_csv_file)
	return trains

def trainSearch(from_station_name, to_station_name, train_time = getTimeCeiling(15*60), am_pm = getAMPM(), date = getTodaysDate(), stations_csv_file = "stations.csv"):
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

class Plugin(BasePlugin):
	name = "lirr"
	stations_csv_file = "stations.csv" #Edit to make user-configurable
	

	@regex(".*train search.*")
	def testRegex(self, text):
		try:	
			train = nextTrain("Deer Park", "Penn Station", stations_csv_file)
		except StationError as e:
			raise StationError(e.value)
		self.say(train.to_siri())
		self.completeRequest()

