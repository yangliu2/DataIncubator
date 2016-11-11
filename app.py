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
from bs4 import BeautifulSoup

app = Flask(__name__)

address = pd.read_csv('address_book.csv')

cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)
    
@checkpoint(key=string.Template('stride.csv'), work_dir=cache_dir, refresh=True)
def update_zillow(selected_address):
    '''
    fucntion used to get zillow API data for the filtered address, funciton will exit when requeted 1000 per zillow's API limit
    information got:
    zillow ID
    zillow link
    latittude
    longitude

    -------
    parameters:
    selected_address - the filtered address that will be searched, include address and zipcode of homes

    return:
    None - modify the 'address_book.csv' file 
    '''

    # zillow API function, have 1000 request per day limit
    # only use after getting small number of interested properties

    from pyzillow.pyzillow import ZillowWrapper, GetDeepSearchResults, GetUpdatedPropertyDetails
    
    # pyzillow 
    # https://github.com/hanneshapke/pyzillow

    YOUR_ZILLOW_API_KEY = 'X1-ZWz1fcz57zvjt7_6jziz'
    
    counter = 0
    for i in range(len(selected_address)):

        # print selected_address.BBLE.iloc[i]
        BBLE = selected_address.BBLE.iloc[i]
        index = selected_address[selected_address['BBLE'] == BBLE].index.values[0]
        

        print index, counter
        if pd.isnull(address.iloc[index].ZILLOW_ID) and address.iloc[index].ZILLOW_ID != 'ERROR':
            
            # sometimes zillow API wrapper dones't accept address/zipcode, even though they are strings
            try:
                # convert process street numbers for zillow API wrapper
                street_num = selected_address.iloc[i]['STREET_NUM']
                street_name = selected_address.iloc[i]['STREET_NAME']

                # assing address and zipcode
                address_Z = str(street_num) + ' ' + str(street_name)
                zipcode_Z = str(selected_address.iloc[i]['ZIP'])

                #use zillow API wrapper to get website link for this property
                zillow_data = ZillowWrapper(YOUR_ZILLOW_API_KEY)
                deep_search_response = zillow_data.get_deep_search_results(address_Z, zipcode_Z)
                result = GetDeepSearchResults(deep_search_response)

                # find the index of the current address
                BBLE = selected_address.BBLE.iloc[i]
                index = selected_address[selected_address['BBLE'] == BBLE].index.values[0]

                address['ZILLOW_LINK'].iloc[index] = result.home_detail_link
                address['ZILLOW_ID'].iloc[index] = int(result.zillow_id)
                address['LATITUDE'].iloc[index] = result.latitude
                address['LONGITUTDE'].iloc[index] = result.longitude
                
                # check if querried Zillow 1000 times, quit if exceeded limit
                counter += 1
                if counter > 1000:

                    # save zillow data to database
                    filename = 'address_book.csv'
                    address.to_csv(filename, index=False)
                    return
            except:
                print "error on line", i
                address['ZILLOW_ID'].iloc[index] = 'ERROR'
                pass

    # save zillow data to database
    filename = 'address_book.csv'
    address.to_csv(filename, index=False)


@checkpoint(key=string.Template('stride.csv'), work_dir=cache_dir, refresh=True)
def scrape_zillow(selected_address):
    '''
    fucntion used to scrape zillow website for sale info and school grade
    -------
    parameters:
    selected_address - the filtered address that will be scraped

    return:
    None - modify the 'address_book.csv' file 
    '''

    # print selected_address.head(10)
    if len(selected_address) > 1000:
        search_length = 1000
    else:
        search_length = len(selected_address)
    for i in range(len(selected_address)):

        BBLE = selected_address.BBLE.iloc[i]
        index = selected_address[selected_address['BBLE'] == BBLE].index.values[0]

        print address.iloc[index].ZILLOW_STATUS, address.iloc[index].ZILLOW_ID
        # print address.iloc[index].ZILLOW_LINK

        if pd.isnull(address.iloc[index].ZILLOW_STATUS) \
            and pd.notnull(address.iloc[index].ZILLOW_ID) \
            and address.iloc[index].ZILLOW_ID != 'ERROR':
            
            try: 
                # scrapying zillow page for school rating
                r = requests.get(selected_address['ZILLOW_LINK'].iloc[i])

                # parse with BeautifulSoup

                soup = BeautifulSoup(r.text, "html.parser")

                #check if selling
                sale_tag = soup.find(id = 'home-value-wrapper')

                status = ''

                if ('For Sale' in sale_tag.text):
                    status = 'For Sale'
                elif ('Off Market' in sale_tag.text):
                    status = 'Off Market'
                elif ('Sold' in sale_tag.text):
                    status = 'Sold'
                elif ('PENDING' in sale_tag.text):
                    status = 'Pending'
                else:
                    status = 'Unknown'

                # find id='nearbySchools'
                rating = soup.find(id = 'nearbySchools')

                # find 'li' in the table
                rows = rating.find_all('li')

                # find each row by 'div', first char of each striped value is grade
                # get a list of all three, pk-5, 6-8, 9-12 in random order
                rate=[]
                for row in rows[1:4]:
                    score = row.find_all('div')[0].text.strip()
                    rate.append(int(score[0:2]))
                
                address.SCHOOL_RATING.iloc[index] = str(rate)
                address.ZILLOW_STATUS.iloc[index] = status

                print address.SCHOOL_RATING.iloc[index], address.ZILLOW_STATUS.iloc[index]
            except:
                print "error on line", i
                pass

    # save zillow data to database
    filename = 'address_book.csv'
    address.to_csv(filename, index=False)
        

@checkpoint(key=string.Template('stride.csv'), work_dir=cache_dir, refresh=True)
def selectHouse(budget, built, cusine, food_section, grade):
    '''
    filter the request and generate suggestions for home buyer
    ------
    param:
    budget - the budget, string
    built - year of building, string
    cusine - favor of food, string
    food_section - importance of food selection, string
    grade - grade of school, stringy 
    ------
    return:
    script - the java script generated for displaying google map. it's an array of marker positions, string
    np.median(latitudes): 
    np.median(longitudes): the median lat and long of the position marker for google map
    '''

    # set home searching parameters
    budget_max = int(budget)
    budget_min = int(budget) - 100000
    built_year = int(built) #built year cutoff
    grade = int(grade) #average school grade needed
    #cusine = 'Chinese'
    food_section = int(food_section) #number of zipcode areas with top restuarant
    #interest = 'biking'

    # Filter by budget, set as 20% above and below budget
    budget = address.loc[address['VALUE'] < budget_max]
    budget = budget.loc[budget['VALUE'] > budget_min]

    # Find places built after specified year
    after_built_year = budget.loc[budget['YEAR_BUILT'] >= built_year]

    # imported the NYC restaurant inspection data to look at nearby restaurants
    food = pd.read_csv('food.csv')

    if cusine == 'no':
        # find preference
        selected_address = after_built_year
    else:
        food_pref = food.loc[food['CUISINE DESCRIPTION'] == cusine]

        # group places by zip code
        food_by_zip = food_pref.groupby(by=['ZIPCODE'])['GRADE'].count()

        # only take the top food_section number of zipcodes
        short_list = food_by_zip.sort_values(ascending=False).head(food_section)

        selected_address = after_built_year.loc[after_built_year['ZIP'].isin(list(short_list.index))]

    # look at zillow API and update database
    update_zillow(selected_address)

    scrape_zillow(selected_address)
    
    links_sale = selected_address.loc[selected_address['ZILLOW_STATUS'] == 'For Sale']
    
    # this is the lat,long array going to be ploted
    latitudes, longitudes = links_sale['LATITUDE'].tolist(), links_sale['LONGITUTDE'].tolist()

    # convert location from string to float
    latitudes = [float(i) for i in latitudes]
    longitudes = [float(i) for i in longitudes]

    # need to generate javascripts for the output html file
    script = "var markers = ["

    for i in range(len(latitudes)):
        if i < len(latitudes) - 1:
            script += "[ '"+ str(links_sale['ZILLOW_ID'].iloc[i]) + "', " + str(latitudes[i]) + ", " + str(longitudes[i]) + ", '" + links_sale['ZILLOW_LINK'].iloc[i] + "' ],"
        else:
            script += "[ '"+ str(links_sale['ZILLOW_ID'].iloc[i]) + "', " + str(latitudes[i]) + ", " + str(longitudes[i]) + ", '" + links_sale['ZILLOW_LINK'].iloc[i] + "' ]"
    #close bracket
    script += "];"
    # print script
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
        
        script, lat, long = selectHouse(budget, built, cusine, food_section, grade)
        # script, lat, long = backup()

        return render_template('index.html', script=script, latitude=lat, longitude=long)
  
if __name__ == '__main__':
    app.run(host="104.131.11.39", port=33507)

# injust some changes
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)