# -*- coding: utf-8 -*-
"""
@author: Christian Kiss
"""

################################### DISCLAIMER #############################################
# USE ONLY AT YOUR OWN RISK AND ONLY IF YOU KNOW WHAT YOU ARE DOING!!!!!
# IMPORTANT: after changing your profile, check your profile data in nightscout or AAPS
#            BEFORE activating your profile!!!! There's no guarantee changes are correct!!!!
############################################################################################


##### NOTE: enter your nightscout login data here and save this script before running ######
API_SECRET = '<API_SECRET>'
URL = 'https://<YOUR_NIGHTSCOUT_URL>' # should look like 'https://yoursite.herokuapp.com'
############################################################################################

if not API_SECRET or not URL:
	print("Enter your Nightscout data and run again!")
	exit()


############################################################################################
# gui wrapper
############################################################################################
import matplotlib.pyplot as plt
import numpy
from matplotlib.widgets import Slider, Button
from functools import partial

class factor_controls_wrapper:
	multiplier_slider_height = 0.015
	multiplier_slider_spacing = 0.02

	# data must be an array of tuplets [(timeAsSeconds, value)]:
	def __init__(self, title, fig, data, precision, total_width,
		total_height, left_offset, bottom_offset,
		show_weighted_average=False, show_sum=False, show_rotate=False):
		self.title = title
		self.data_current = data.copy() # !
		self.IGNORE_CALLBACK = False
		self.precision = precision
		self.show_sum = show_sum
		self.show_weighted_average = show_weighted_average

		self.text_y_pos = bottom_offset + self.multiplier_slider_height + self.multiplier_slider_spacing + total_height
		self.title = fig.text(0.5, self.text_y_pos, title, fontsize=12, horizontalalignment='center')
		
		num = len(data)
		times = [sec for (sec, val) in data]
		times.append(times[0]+(24*60*60)) # time length of last entry is diff between last entry and (first entry + 24h):
		max_val = max([val for (sec, val) in data])

		offset = 0
		self.factor_sliders = []
		for i, (sec, val) in zip(range(num), data):
			width = total_width * (times[i+1] - times[i])  / (24*60*60)
			p = plt.axes([left_offset+offset, bottom_offset + self.multiplier_slider_height + self.multiplier_slider_spacing, width, total_height*0.85])
			offset += width
			s = Slider(p, self.timeAsSec2Str(sec), 0, max_val*1.5, orientation='vertical', valinit=val)
			s.on_changed(partial(self.factor_sliders_callback, entry=i))
			self.factor_sliders.append(s)

		self.multiplier = 1
		text_space = 0.1
		p = plt.axes([left_offset + text_space / 2, bottom_offset, total_width - text_space, self.multiplier_slider_height])
		self.multiplier_slider = Slider(p, '', 0, 2, valinit=self.multiplier, orientation='horizontal', valstep=0.001)
		self.multiplier_slider.on_changed(self.multiplier_slider_callback)

		if show_sum:
			self.sum = fig.text(left_offset + total_width, # x pos from which we align right (most right point)
				self.text_y_pos,"",	#fontsize=10,
				horizontalalignment='right')
			self.update_sum_view()
		if show_weighted_average:
			self.weighted_avg = fig.text(left_offset + total_width, # x pos from which we align right (most right point)
				self.text_y_pos,"",
				#fontsize=10,
				horizontalalignment='right')
			self.update_avg_view()
		if show_rotate:
			self.button_rotate_left = Button(plt.axes([left_offset+0.3,self.text_y_pos, 0.02, 0.02]), label = "<-")
			self.button_rotate_left.on_clicked(self.button_rotate_left_callback)
			self.button_rotate_right = Button(plt.axes([left_offset+0.35,self.text_y_pos, 0.02, 0.02]), label = "->")
			self.button_rotate_right.on_clicked(self.button_rotate_right_callback)

		
	def get_weighted_avg(self):
		v = self.get_data_multiplied()
		num = len(v)
		times = [sec for (sec, val) in v]
		times.append(times[0]+(24*60*60)) # time length of last entry is diff between last entry and (first entry + 24h):
		sum = 0
		for i, (sec,val) in zip(range(num), v):
			weight = (times[i+1] - times[i]) / (24*60*60)
			val_weighted = val*weight
			sum += val_weighted
		return sum
	def button_rotate_left_callback(self, event):
		self.rotate_slider_val(True)
	def button_rotate_right_callback(self, event):
		self.rotate_slider_val(False)
	def rotate_slider_val(self, left):
		#for i in range(len(self.data_current)):
		#	self.data_current[i][1] = 

		v = [val for sec,val in self.data_current]
		if left:
			v = self.rotate(v, 1)
		else: # means right
			v = self.rotate(v, -1)

		self.IGNORE_CALLBACK = True
		for slider,new_val,data_current_item in zip(self.factor_sliders, v, self.data_current):
			slider.set_val(new_val)
			data_current_item[1] = new_val
		self.IGNORE_CALLBACK = False
	def rotate(self, l, n):
		return l[n:] + l[:n]

	def factor_sliders_callback(self, slider_val, entry=None):
		if self.IGNORE_CALLBACK:
			return 0
		print("slider " + str(entry) + " value: " + str(slider_val))
		self.data_current[entry][1] = slider_val / self.multiplier # IMPORTANT!!!! save without multiplier by dividing through it
		
		if self.show_sum:
			self.update_sum_view()
		if self.show_weighted_average:
			self.update_avg_view()

	def multiplier_slider_callback(self, slider_val):
		print("multplier value: " + str(slider_val))
		self.multiplier = slider_val

		self.IGNORE_CALLBACK = True
		sum = 0
		for s, (sec, val) in zip(self.factor_sliders, self.data_current):
			new_val = val * self.multiplier
			sum += new_val
			s.set_val(new_val)
		if self.show_sum:
			self.update_sum_view()
		if self.show_weighted_average:
			self.update_avg_view()
		self.IGNORE_CALLBACK = False

	def update_sum_view(self):
		s = sum([val for (time,val) in self.get_data_multiplied()])
		self.sum.set_text("Sum: " + str(round(s, 2)) + " IE")
	def update_avg_view(self):
		avg = self.get_weighted_avg()
		self.weighted_avg.set_text("Avg: " + str(round(self.get_weighted_avg(), 2)))

	def get_data_multiplied(self): # returns data_current with multiplication
		return [(time, val * self.multiplier) for time,val in self.data_current]
	def get_data_multiplied_rounded(self): # returns data_current with multiplication and rounded according to precision
		return [(time, round(val * self.multiplier, self.precision)) for time,val in self.data_current]

	def timeAsSec2Str(self, timeAsSec):
		m, s = divmod(timeAsSec, 60)
		h, m = divmod(m, 60)
		return "{:d}:{:02d}".format(h, m)



#########################################################################################################
# nightscout interface
#########################################################################################################
# -*- coding: utf-8 -*-
"""
@author: Christian Kiss
"""

import requests
import json
import urllib
import time
from urllib.parse import urlparse
import hashlib

class ns_interface:
	def __init__(self, api_secret, basic_url):
		self.api_secret = api_secret
		self.basic_url = basic_url # looks like https://blabla.herokuapp.com
		self.profile_json_url = basic_url + '/api/v1/profile.json'
		try:
			r = requests.get(self.profile_json_url)
			r.raise_for_status()
		except requests.exceptions.HTTPError as err:
			raise SystemExit(err)
		self.data = r.json()
		print("Got profile.json data from Nightscout")

		self.sel_record = []
		self.sel_profile = []

	def get_profiles_json(self):
		return self.data
	def get_first_db_record(self):
		for database_record in self.data:
			print("Found first database record from " + database_record['startDate'] + " with id " + database_record['_id'])
			return database_record

	def select_record(self, record):
		self.sel_record = record

	def select_profile(self, profile):
		self.sel_profile = profile

	def get_default_profile_from_record(self, record=None):
		record = self.sel_record if record is None else record
		print("Found default profile " + record['defaultProfile'])
		return record['store'][record['defaultProfile']] # store can hold many profiles, pick default profile in store
	def get_default_profile_name_from_record(self, record=None):
		record = self.sel_record if record is None else record
		return record['defaultProfile']
	def get_record_date(self, record=None):
		record = self.sel_record if record is None else record
		return record['startDate']

	def time2sec(self, time): # time is sth. like "06:00"
		(h, m) = time.split(':')
		return (int(h)*60*60) + (int(m)*60)

	# gives back (timeAsSeconds, basal rate):
	def get_basal_list(self, profile=None):
		profile = self.sel_profile if profile is None else profile
		return [list((self.time2sec(basal['time']), float(basal['value']))) for basal in profile['basal']]

	def get_sens_list(self, profile=None):
		profile = self.sel_profile if profile is None else profile
		return [list((self.time2sec(sens['time']), float(sens['value']))) for sens in profile['sens']]

	def get_carbratio_list(self, profile=None):
		profile = self.sel_profile if profile is None else profile
		return [list((self.time2sec(carbratio['time']), float(carbratio['value']))) for carbratio in profile['carbratio']]

	def update_basal(self, new_basals, record=None, profile=None): # new basals is a list of tuples (timeAsSeconds, basal rate)
		print("Task: Updating Basal Rate data...")
		record = self.sel_record if record is None else record
		profile = self.sel_profile if profile is None else profile # note: we assume profile is in record...

		for basal_in_profile, (time, val) in zip(profile['basal'], new_basals):
			# basal_in_profile['time'] = time # not necessary since we don't change times... 
			basal_in_profile['value'] = val # CAVE: don't just set basal = new basals since it will delete the time and value keys and just copy the tuplet.
		self.update_record(record)

	def update_sens(self, new_senss, record=None, profile=None): # new basals is a list of tuples (timeAsSeconds, basal rate)
		print("Task: Updating ISF data...")
		record = self.sel_record if record is None else record
		profile = self.sel_profile if profile is None else profile # note: we assume profile is in record...

		for sens_in_profile, (time, val) in zip(profile['sens'], new_senss):
			sens_in_profile['value'] = val
		self.update_record(record)

	def update_carbratio(self, new_carbratios, record=None, profile=None): # new basals is a list of tuples (timeAsSeconds, basal rate)
		print("Task: Updating IC data...")
		record = self.sel_record if record is None else record
		profile = self.sel_profile if profile is None else profile # note: we assume profile is in record...

		for carbratio_in_profile, (time, val) in zip(profile['carbratio'], new_carbratios):
			carbratio_in_profile['value'] = val
		self.update_record(record)

	def authenticate_as_admin(self):
		referer_url = self.basic_url + '/profile' # don't think this is necessary...
		auth_url = self.basic_url + '/api/v1/verifyauth'
		self.api_secret_hash = hashlib.sha1(self.api_secret).hexdigest()
		headers = {
			'Content-Type':'application/json',
			'Accept':'application/json',
			'api-secret':self.api_secret_hash,
			'Referer':referer_url,
			'X-Requested-With':'XMLHttpRequest'
		}
		query_string_params = {
			't':int(round(time.time() * 1000))
		}

		print("Authenticating...")
		self.session = requests.Session()
		r = self.session.get(auth_url, headers=headers, params=query_string_params)
		if r.status_code != 200:
			print("Authentication failed with code: " + str(r.status_code))
			return 0

	def issue_profile_switch(self, profile_name):
		if not self.session:
			self.authenticate_as_admin()
		treatments_url = self.basic_url + '/api/v1/treatments/'

		headers = {
			'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', # important!!!
			'api-secret':self.api_secret_hash,
			'X-Requested-With':'XMLHttpRequest'
		}

		form_data = {
			'eventType':'Profile Switch',
			'profile':profile_name,
		}
		print("Issuing profile switch to updated profile...")
		r = self.session.post(treatments_url, headers=headers, data=urllib.parse.urlencode(form_data))
		if r.status_code != 200:
			print("POST failed with code: " + str(r.status_code))
			return 0
		print("POST SUCCESS ... done profile switch to updated profile with name " + profile_name)

	def update_record(self, record): # write new record to nightscout
		self.authenticate_as_admin()

		record_flattened = self.flatten_json(record) # flatten record, otherwise NS won't accept
		referer_url = self.basic_url + '/profile' # don't think this is necessary...

		########################### update startDate ... no need to do so
		#import datetime
		#dateTimeObj = datetime.now()
		#timestampStr = dateTimeObj.strftime("%Y-%m-%dT%H:%M:%S.000Z")
		#first_record['startDate'] = timestampStr
		###########################

		headers = {
			'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', # important!!!
			'api-secret':self.api_secret_hash,
			'Referer':referer_url,
			'X-Requested-With':'XMLHttpRequest'
		}

		print("Sending data...")

		r = self.session.put(self.profile_json_url, headers=headers,
					data=urllib.parse.urlencode(record_flattened)) # [debug: for restoring: data=Chrome string]
		if r.status_code != 200:
			print("Send failed with code: " + str(r.status_code))
			return 0
		print("Send SUCCESS ... check your profile if data is correct")

	def flatten_json(self, y):	# inspired by https://towardsdatascience.com/flattening-json-objects-in-python-f5343c794b10
		out = {}
		def flatten(out, x, name=''):
			if type(x) is dict:
				for a in x:
					if name == '':
						flatten(out, x[a], a)
					else:
						flatten(out, x[a], name + '[' + a + ']')
			elif type(x) is list:
				i = 0
				for a in x:
					flatten(out, a, name + '[' + str(i) + ']')
					i += 1
			else:
				out[name] = x

		flatten(out, y)
		return out

#########################################################################################################
# main program
#########################################################################################################

import matplotlib.pyplot as plt
import matplotlib.ticker

font = {'size':9}
matplotlib.rc('font', **font)
plt.rcParams['toolbar'] = 'None' 
save_button_height = 0.03
save_button_width = 0.1

ns = ns_interface(bytes(API_SECRET, 'utf-8'), URL)
ns.select_record(ns.get_first_db_record())
ns.select_profile(ns.get_default_profile_from_record())

default_profile_name = ns.get_default_profile_name_from_record()
# ISF
fig = plt.figure("Edit your Nightscout profile {0} from {1} - (c) Christian Kiss 2020"
	.format(default_profile_name, ns.get_record_date()),
	figsize=(11, 10))
#fig.canvas.window().statusBar().setVisible(False) # Remove status bar (bottom bar)

isf_gui = factor_controls_wrapper("ISF", fig, ns.get_sens_list(), 1,
	0.95, # width in %
	1 / 4, # height in %
	0.02, # left offset
	0.02, # bottom offset
	show_weighted_average=True, show_rotate=True)
save_isf_button = Button(plt.axes([0.0, 1 - save_button_height - 2/3, save_button_width, save_button_height]), label = "Save ISF")
# IC
ic_gui = factor_controls_wrapper("IC", fig, ns.get_carbratio_list(), 1, 0.95, 1 / 4, 0.02, 0.02 + 1/3, show_weighted_average=True, show_rotate=True)
save_ic_button = Button(plt.axes([0.0, 1 - save_button_height - 1/3, save_button_width, save_button_height]), label = "Save IC")

# Basal Rate
br_gui = factor_controls_wrapper("Basal Rate", fig, ns.get_basal_list(), 2, 0.95, 1 / 4, 0.02, 0.02 + 2/3, show_sum=True, show_rotate=True)
save_br_button = Button(plt.axes([0.0, 1 - save_button_height, save_button_width, save_button_height]), label = "Save BR")

# profile switch Button
profile_switch_button = Button(plt.axes([save_button_width + 0.02, 1 - save_button_height, save_button_width, save_button_height]), label = "Activate Profile")

def save_br_button_callback(event):
    ns.update_basal(br_gui.get_data_multiplied_rounded())
def save_isf_button_callback(event):
    ns.update_sens(isf_gui.get_data_multiplied_rounded())
def save_ic_button_callback(event):
    ns.update_carbratio(ic_gui.get_data_multiplied_rounded())
def profile_switch_button_callback(event):
	ns.issue_profile_switch(default_profile_name)

save_isf_button.on_clicked(save_isf_button_callback)
save_br_button.on_clicked(save_br_button_callback)
save_ic_button.on_clicked(save_ic_button_callback)
profile_switch_button.on_clicked(profile_switch_button_callback)

plt.show()







#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

"""
structure of nightscout database record:
database_record
	ID
	startDate
	store
		$profile1
			dia
			carbratio
				<unlabeled>
					time
					timeAsSeconds
					value
				<unabeled>
					...
				...
			sens
				<unlabeled>
					time
					timeAsSeconds
					value
				<unlabeled
					..

			basal
				....
			target_low
				time
				timeAsSeconds
				value
			target_high
				...
			timezone
			carbs_hr
			delay
			startDate
			units
		$profile2
			....


database_record
"""
