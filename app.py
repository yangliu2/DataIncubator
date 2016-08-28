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
		budget = request.form['budget_upper']
		built = request.form['built']
		cusine = request.form['food']
		food_section = request.form['food_level']
		interests = request.form['interests']
		grade = request.form['school']

		print budege, built, cusine, food_section, interests, grade


		return render_template('googlemap.html')
  
if __name__ == '__main__':
	app.run(host='104.131.11.39', port=33507)

# injust some changes