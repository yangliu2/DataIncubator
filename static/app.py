from flask import Flask, render_template, request, redirect, jsonify, Response
import json
import pandas as pd
import requests
import numpy as np
import dill as pickle
from bokeh.layouts import gridplot, row, column
from bokeh.plotting import figure, save, output_file, gridplot, vplot, show
from bokeh.palettes import Spectral4
from bokeh.models import BoxSelectTool, LassoSelectTool, Spacer, PrintfTickFormatter, layouts
from bokeh.embed import components
import bokeh.palettes as palette
from bokeh.models import Range1d
import copy
from plots import *

app = Flask(__name__)

dft = pickle.load(open("static/data/dft.dill", "r"))
cfr = pickle.load(open("static/data/ada.dill", "r"))
#cfr_audit = pickle.load(open("static/data/audit_ada.dill", "r"))
cfr_audit = cfr
isos = pickle.load(open("static/data/isos.p", "r"))
data = pickle.load(open("static/data/all_data.p", "r"))
fis = pickle.load(open("static/data/fi.p", "r"))
val = pickle.load(open("static/data/validation.p", "r"))
fi_isos = pickle.load(open("static/data/fi_isos.p", "r"))
fi_state = pickle.load(open("static/data/fi_state.p", "r"))
fi_title = pickle.load(open("static/data/fi_title.p", "r"))
fi_visa = pickle.load(open("static/data/fi_visa.p", "r"))
#countries = requests.get('https://rawgit.com/johan/world.geo.json/master/countries.geo.json').json()

range_record = {'wage':[np.log1p(5000.0), np.log1p(500000.0)], 'isos':fi_isos.index.tolist(),
                'state':fi_state.index.tolist(),'esize':[np.log1p(1.0), np.log1p(100000.0)],
                'visa':fi_visa.index.tolist(), 'no_lawyer': [0., 1.],
                'degree': ['High School', 'PhD'], 'foreign_ed': [0., 1.],
                'title': fi_title.index.tolist(), 'year': [0.0, 0.0],
                'online': [0., 1.]}

##Calculate probabilities for all countries
countrydata = [{'wage':np.log1p(30000.0), 'isos':c, 'state':'NY','esize':np.log1p(10000.0),
               'visa':'Not in USA', 'no_lawyer': 1.0, 'degree': 'High School',
               'foreign_ed': 1.0, 'title': 'Engineering',
               'year': 0.0, 'online': 1.0} for c in isos['ISO'].tolist() if c != 'USA']
indices = [c for c in isos['ISO'] if c != 'USA']
countryval = pd.DataFrame(data = countrydata)
X = dft.transform(countryval)
countryprobs = cfr.predict_proba(X)[:,1]
countrypdf = pd.DataFrame(data = countryprobs, index = indices)

##Read in acceptance rate for all countries
countrydata = pickle.load(open("static/data/country_full_ar.p", "r"))
countrydata.columns = [0]

## Categorical plot for countries
#cscript, cdiv = new_world_map(countrydata, countries)

##Histogram of data points
cascript, cadiv = double_cat(data, 'wage', 'esize', np.log1p(500000.0), np.log1p(10000.0), 'Expected Wage', 'Employer Size');

##Hard coded feature importances
fi_sub = fis[fis['Importance'] > 0.0]
fi_sub = fi_sub.sort_values(by='Importance',ascending=False)
factors = fi_sub['name'].tolist()
x = fi_sub['Importance'].tolist()
feats = figure(title="", tools="", toolbar_location=None, x_axis_label="Permutation Importance",
                    y_range=factors, x_range=[0,0.5], plot_width=700, plot_height=500, webgl=True)
        
feats.segment(0, factors, x, factors, line_width=20, line_color="blue", line_alpha=0.5)
fscript, fdiv = components(feats)

##Hard coded validation plot of AUCs
valplot = figure(title="", tools="", toolbar_location=None, x_axis_label="FPR", y_axis_label="TPR",
                 y_range=[0,1.0], x_range=[0,1.0], plot_width=700, plot_height=500, webgl=True)
val['color'] = Spectral4
for name in val.index:
    valplot.line(val.loc[name,'FPR'], val.loc[name,'TPR'], legend=name, color=val.loc[name,'color'],
                 line_width=3, line_alpha=0.5)

valplot.legend.location = "top_left"
vscript, vdiv = components(valplot)

##Calculate probabilities for this selection
#singleval = {'wage':100000, 'isos':'AUS', 'JOB_INFO_WORK_STATE':'NY',
#'EMPLOYER_NUM_EMPLOYEES':100, 'CLASS_OF_ADMISSION':'F-1',
#'PREPARER_INFO_EMP_COMPLETED': 'Y', 'FOREIGN_WORKER_INFO_EDUCATION': 'PhD',
#'JOB_INFO_FOREIGN_ED': 'N'}
#script, div, prob, prob_audit = prob_widget_plot(singleval, dft, cfr, cfr_audit)

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index')
def index():
  return render_template('index.html')

@app.route('/works',methods=['GET','POST'])
def works():
    return render_template('works.html', fscript=fscript, fdiv=fdiv, vscript=vscript, vdiv=vdiv)

@app.route('/dummy')
def dummy():
    return render_template('dummy.html')

@app.route('/survey',methods=['GET','POST'])
def survey():
    return render_template('survey.html', prob = '50', aud='0')

@app.route('/countryplot',methods=['GET','POST'])
def countryplot():
    if request.method == 'GET':
        return render_template('image.html', script = cscript, div = cdiv)
    else:
        return render_template('image.html', script = cscript, div = cdiv)

@app.route('/dataplot',methods=['GET','POST'])
def dataplot():
    if request.method == 'GET':
        return render_template('image.html', script = cascript, div = cadiv)
    else:
        return render_template('image.html', script = cascript, div = cadiv)

@app.route('/visasuccess',methods=['GET','POST'])
def visasuccess():
    if request.method == 'GET':
        return render_template('image.html', script = script, div = div)
    else:
        return render_template('image.html', script = script, div = div)

@app.route('/appplot',methods=['GET','POST'])
def appplot():
    if request.method == 'GET':
        return render_template('survey.html')
    else:
        divlist = []
        country = request.form.getlist('country')[0]
        state = request.form.getlist('state')[0]
        visa = request.form.getlist('visa')[0]
        degree = request.form.getlist('education')[0]
        wage = np.log1p(float(request.form.getlist('wage')[0]) * 5000.0)
        size = np.log1p(float(request.form.getlist('esize')[0]) * 500.0)
        fed_flag = request.form.getlist('foreign_ed')[0]
        l_flag = request.form.getlist('lawyer')[0]
        jtitle = request.form.getlist('jtitle')[0]
        on_flag = request.form.getlist('online')[0]
        dyear = pd.to_datetime('now')
        year = (365.25 * (dyear.year - 2012) + dyear.dayofyear) / 365.25
        
        ##Calculate probabilities for this selection
        singleval = {'wage':wage, 'isos':country, 'state':state,'esize':size,
                    'visa':visa, 'no_lawyer': l_flag, 'degree': degree,
                    'foreign_ed': fed_flag, 'title': jtitle,
                    'year': year, 'online': on_flag}
        print singleval
        script, div, prob, prob_audit = prob_plot(singleval, dft, cfr, cfr_audit)
        print prob, prob_audit

        prob = int(prob*100.0)
        prob_audit = int(prob_audit*100.0)
        return render_template('survey.html', prob=prob, aud=prob_audit, script = script, div = div, cascript = cascript, cadiv = cadiv, fscript = fscript, fdiv = fdiv, cscript = cscript, cdiv = cdiv)

@app.route('/background_process')
def background_process():
    try:
        country = request.args.get('country', 0, type=str)
        state = request.args.get('state', 0, type=str)
        visa = request.args.get('visa', 0, type=str)
        degree = request.args.get('degree', 0, type=str)
        wagemin = np.log1p(5000.0)
        delwage = np.log1p(500000.0) - wagemin
        wage = float(request.args.get('wage', 0, type=str)) * delwage / 100.0 + wagemin
        sizemin = np.log1p(1.0)
        delsize = np.log1p(100000.0) - sizemin
        size = float(request.args.get('size', 0, type=str)) * delsize / 100.0 + sizemin
        fed_flag = float(request.args.get('fed_flag', 0, type=str))
        l_flag = float(request.args.get('l_flag', 0, type=str))
        title = request.args.get('title', 0, type=str)
        on_flag = float(request.args.get('on_flag', 0, type=str))
        dyear = pd.to_datetime('now')
        year = (365.25 * (dyear.year - 2012) + dyear.dayofyear) / 365.25
        
        singleval = {'wage':wage, 'isos':country, 'state':state,'esize':size,
                    'visa':visa, 'no_lawyer': l_flag, 'degree': degree,
                    'foreign_ed': fed_flag, 'title': title,
                    'year': year, 'online': on_flag}
        prob = prob_calc(singleval, dft, cfr)
        
        probrange, maxkey, maxprob = prob_feat_calc(singleval, range_record, dft, cfr, prob)
        
        prob = int(100.0*prob)
        output = {"result":prob, "wage":int(np.exp(wage)), "size":int(np.exp(size)),
            "rec":maxkey, "frec":"Here we show the relative importance of different features to your application."}
        for k,v in probrange.iteritems():
            output["feat_" + k] = v
        
        #print output
        
        return jsonify(**output)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
  app.run(port=33507)
