from flask import render_template
from app import app
import pandas as pd
import scripts.main


df_data = pd.read_pickle("df_data.pkl")
performance = df_data["Total_Confirmed"].dropna().tolist()
prog_limit = max(performance[:-1])+50
objects = df_data["State"].dropna().tolist()
cured = df_data["Cured"].dropna().tolist()
total = sum(performance)
death = df_data["Death"].dropna().tolist()
slno = df_data["SNo"].dropna().tolist()

@app.route('/')
@app.route('/charts')
def charts():
	return render_template('chartjs.html')

@app.route('/tables')
def tables():
    return render_template('basic-table.html',performance=performance,objects=objects,len=len(performance),cured=cured,death=death,slno=slno, prog_limit=prog_limit)
