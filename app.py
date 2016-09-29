from flask import Flask, render_template, request, redirect
import bokeh.io, bokeh.plotting, bokeh.models
from bokeh.plotting import figure
from bokeh.embed import components 
from ediblepickle import checkpoint
import string
import logging

import numpy as np
import pandas as pd
import requests
import os.path
import io
import re
import time
import sys
import json

app = Flask(__name__)

cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

@checkpoint(key=string.Template('stride.csv'), work_dir=cache_dir, refresh=True)

def selectHouse(budget, built, cusine, food_section, interests, grade):
	# set home searching parameters
	budget_max = int(budget)
	budget_min = int(budget) - 100000
	built_year = int(built) #built year cutoff
	grade = int(grade) #average school grade needed
	#cusine = 'Chinese'
	food_section = int(food_section) #number of zipcode areas with top restuarant
	#interest = 'biking'

	# import data from NYC Property Valuation and Assessment data 
	data = pd.read_csv('TC1.txt')

	# Filter by budget, set as 20% above and below budget
	budget = data.loc[data['CUR_FV_T'] < budget_max]
	budget = budget.loc[budget['CUR_FV_T'] > budget_min]

	# Find places built after specified year
	after_built_year = budget.loc[budget['YRB'] >= built_year]
	valid_address = after_built_year[pd.notnull(after_built_year['HNUM_LO'])] # filter valid address for Zillow search
	price_by_zip = valid_address.groupby(by=['ZIP'])['CUR_FV_T'].mean()

	# imported the NYC restaurant inspection data to look at nearby restaurants
	food = pd.read_csv('NYC_Restaurant_inspection.csv')

	# find unique places by last inspection
	unique_food = food
	unique_food.drop_duplicates(subset = 'DBA', inplace = True)

	# find clean Chinese places
	clean_food=unique_food.loc[unique_food['GRADE'] == 'A']
	chinese_food = clean_food.loc[unique_food['CUISINE DESCRIPTION'] == cusine]

	# group places by zip code
	food_by_zip=chinese_food.groupby(by=['ZIPCODE'])['GRADE'].count()

	#combine food and mean price into one dataframe
	food_and_price = pd.concat([food_by_zip, price_by_zip], axis=1)

	# take out invalid prices
	short_list= food_and_price[pd.notnull(food_and_price['CUR_FV_T'])]
	short_list= short_list.sort('GRADE', ascending=False)

	home_with_food = valid_address.loc[valid_address['ZIP'].isin(short_list.head(food_section).index)]

	# zillow API function, have 1000 request per day limit
	# only use after getting small number of interested properties

	from pyzillow.pyzillow import ZillowWrapper, GetDeepSearchResults, GetUpdatedPropertyDetails
	# pyzillow 
	# https://github.com/hanneshapke/pyzillow

	YOUR_ZILLOW_API_KEY = 'X1-ZWz1fcz57zvjt7_6jziz'

	zillow_link = []
	zillow_link_ID = []
	zillow_lat = []
	zillow_long = []

	for i in range(len(home_with_food)):
	    # sometimes zillow API wrapper dones't accept address/zipcode, even though they are strings
	    try:
	        # convert process street numbers for zillow API wrapper
	        street_num = home_with_food.iloc[i]['HNUM_LO']

	        if (street_num.isdigit() is False):
	            street_num = ''.join(c for c in street_num if c.isdigit())
	        number = int(street_num)

	        # assing address and zipcode
	        address = str(number) + ' ' + str(home_with_food.iloc[i]['STR_NAME'])
	        zipcode = str(int(home_with_food.iloc[i]['ZIP']))

	        #use zillow API wrapper to get website link for this property
	        zillow_data = ZillowWrapper(YOUR_ZILLOW_API_KEY)
	        deep_search_response = zillow_data.get_deep_search_results(address, zipcode)
	        result = GetDeepSearchResults(deep_search_response)

	        zillow_link.append(result.home_detail_link)
	        zillow_link_ID.append(result.zillow_id)
	        zillow_lat.append(result.latitude)
	        zillow_long.append(result.longitude)
	    except:
	        print "error on line", i
	        pass

	# put list into dataframe
	links = pd.DataFrame(list(zillow_link))
	links.columns=['Zillow Links']
	links['Zillow ID'] = zillow_link_ID
	links['Latitude'] = zillow_lat
	links['Longitude'] = zillow_long

	# scrap from zillow website
	from bs4 import BeautifulSoup

	ratings = []
	status = []

	for i in range(len(links)):

	    rate = []

	    #scrapying zillow page for school rating
	    r = requests.get(links['Zillow Links'][i])

	    #parse with BeautifulSoup

	    soup = BeautifulSoup(r.text, "html.parser")

	    #check if selling
	    sale_tag = soup.find(id = 'home-value-wrapper')

	    if ('For Sale' in sale_tag.text):
	        status.append('For Sale')
	    elif ('Off Market' in sale_tag.text):
	        status.append('Off Market')
	    elif ('Sold' in sale_tag.text):
	        status.append('Sold')
	    elif ('PENDING' in sale_tag.text):
	        status.append('Pending')
	    else:
	        status.append('Unknown')

	    #find id='nearbySchools'
	    rating = soup.find(id = 'nearbySchools')

	    #find 'li' in the table
	    rows = rating.find_all('li')

	    #find each row by 'div', first char of each striped value is grade
	    #get a list of all three, pk-5, 6-8, 9-12 in random order
	    rate=[]
	    for row in rows[1:4]:
	        score = row.find_all('div')[0].text.strip()
	        rate.append(int(score[0:2]))
	    # print rate
	    ratings.append(rate)

	links['School Rating'] = ratings
	links['Status'] = status
	
	#save the zillow results in a csv
	today_date = time.strftime("%d_%m_%Y_%H_%M_%S")
	filename = 'ZillowFiles/Zillow' + today_date + '.csv'
	links.to_csv(filename)
	
	links_sale = links.loc[links['Status'] == 'For Sale']
	
	# this is the lat,long array going to be ploted
	latitudes, longitudes = links_sale['Latitude'].tolist(), links_sale['Longitude'].tolist()

	# convert location from string to float
	latitudes = [float(i) for i in latitudes]
	longitudes = [float(i) for i in longitudes]

	#need to generate javascripts for the output html file
	script = "var markers = ["

	for i in range(len(latitudes)):
	    if i < len(latitudes) - 1:
	        script += "[ '"+ links_sale['Zillow ID'].iloc[i] + "', " + str(latitudes[i]) + ", " + str(longitudes[i]) + ", '" + links_sale['Zillow Links'].iloc[i] + "' ],"
	    else:
	        script += "[ '"+ links_sale['Zillow ID'].iloc[i] + "', " + str(latitudes[i]) + ", " + str(longitudes[i]) + ", '" + links_sale['Zillow Links'].iloc[i] + "' ]"
	#close bracket
	script += "];"
	print script
	return script, np.median(latitudes), np.median(longitudes)

def backup():
	'''
	This function is used when the main function doesn't geneate proper results
	'''
	script = """var markers = [
				['2102152090',40.5922,-73.9887,'http://www.zillow.com/homedetails/162-Bay-43-St-1A-Brooklyn-NY-11214/2102152090_zpid/'], 
				['112078252',40.58796,-73.984478,'http://www.zillow.com/homedetails/26-Bay-50th-St-3B-Brooklyn-NY-11214/112078252_zpid/'],
				['2099301632',40.583672,-73.986096,'http://www.zillow.com/homedetails/171-Bay-52-St-Brooklyn-NY-11214/2099301632_zpid/'],
				['30715080',40.60208,-74.007655,'http://www.zillow.com/homedetails/8849-18th-Ave-Brooklyn-NY-11214/30715080_zpid/'],
				['68314328',40.599535,-73.994709,'http://www.zillow.com/homedetails/2232-Benson-Ave-3B-Brooklyn-NY-11214/68314328_zpid/']];
			"""
	lat = 40.58796
	long = -73.984478
	return script, lat, long

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index', methods=['GET','POST'])
def index():
	if request.method == 'GET':
		return render_template('index.html')
	else:
		budget = request.form['budget_upper']
		built = request.form['built']
		cusine = request.form['food']
		food_section = request.form['food_selection']
		# interests = request.form['interests']
		grade = request.form['school']
		#print budget, built, cusine, food_section, interests, grade
		
		# script, lat, long = selectHouse(budget, built, cusine, food_section, interests, grade)
		script, lat, long = backup()

		return render_template('index.html', script=script, latitude=lat, longitude=long)
  
if __name__ == '__main__':
	app.run(host="104.131.11.39", port=33507)

# injust some changes
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)