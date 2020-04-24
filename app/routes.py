from flask import render_template
from app import app
from scripts.main import main
from scripts.main import main1
from bokeh.embed import components

performance,objects,cured,death,slno,bar,pie,total= main()
prog_limit = max(performance[:-1])+50

maps = main1()
confirmed = maps[0]
cured_map = maps[1]
death_map = maps[2]

@app.route('/')
@app.route('/charts')
def charts():
	script_bar, div_bar = components(bar)
	script_pie, div_pie = components(pie)

	return render_template('chartjs.html',div_bar=div_bar, script_bar=script_bar, script_pie=script_pie, div_pie=div_pie, confirmed=confirmed,cured_map=cured_map,death_map=death_map)
@app.route('/tables')
def tables():
    return render_template('basic-table.html',performance=performance,objects=objects,len=len(performance),cured=cured,death=death,slno=slno, prog_limit=prog_limit, total=total)
