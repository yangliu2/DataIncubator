from flask import Flask, render_template, request, redirect
import bokeh.io, bokeh.plotting, bokeh.models
from bokeh.plotting import figure
from bokeh.embed import components 

app = Flask(__name__)

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

# injust some changes