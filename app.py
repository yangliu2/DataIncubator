from flask import Flask, render_template, request, redirect
import quandl
import bokeh.io, bokeh.plotting, bokeh.models
from bokeh.plotting import figure
from bokeh.embed import components 
import datetime

app = Flask(__name__)

quandl.ApiConfig.api_key = 'xomvruK1ZNabrSwxkJkW'
quandl.ApiConfig.api_version = '2015-04-09'

# shift exactly one month according to month of the year and leap year
def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m: m = 12
    d = min(date.day, [31,
        29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
    return date.replace(day=d,month=m, year=y)


def get_graph(symbol):
	data = quandl.get('WIKI/'+symbol)

	# get current date and last month from current date
	now = datetime.datetime.now()
	last_month = monthdelta(now, -1)
	now_str = now.strftime("%Y-%m-%d")
	last_month_str = last_month.strftime("%Y-%m-%d")

	previous = data.loc[data.index > last_month_str]

	# bokeh.io.output_notebook()

	# plot last month closing price
	p = figure(x_axis_type="datetime")
	p.line(previous.index, previous.Close)
	p.title = 'Stock price for '+symbol
	p.xaxis.axis_label = 'Date'
	p.yaxis.axis_label = 'Price ($)'

	#graph = bokeh.plotting.show(p)

	print previous['Close'][0]
	script,div = components(p)
	return script,div

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index', methods=['GET','POST'])
def index():
	if request.method == 'GET':
		return render_template('index.html')
	else:
		#request
		symbol = request.form['ticker'].upper()
		print symbol
		script,div = get_graph(symbol)
		return render_template('graph.html', name=symbol, script=script, div=div)
  
if __name__ == '__main__':
  app.run(port=33507)
