# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response
from werkzeug import secure_filename
import os
import cv2
from utils import *
import pandas as pd
from playsound import playsound
from sms import *
import random
import csv

fname=''
lname=''
adhar=''
voter=''
name=''
contact = ''
otp=''
idx = 0

app = Flask(__name__)

app.secret_key = '1234'
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return render_template('home.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
	return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	global name
	global adhar
	global voter
	global contact
	error = ""

	if request.method=='POST':
		name = request.form['name']
		adhar = request.form['adhar']
		voter = request.form['voter']
		contact = request.form['contact']
		#fp = request.form['fingerprint']
		#print(fp)


		if(len(adhar)!=12):
			error += "Adhar number Invalid  "
		if(len(voter)!=10 or voter[0:3].isalpha()==False):
			error += "Voter ID Invalid"
		if(error == ""):	
			df = pd.read_csv('aadhar DB.csv')
			#print(df)
			df1 = pd.read_csv('Voter DB.csv')
			#print(df1)
			count=df.iloc[:,0].astype(str).str.contains(adhar).any()
			count1=df1.iloc[:,0].astype(str).str.contains(voter).any()
			print(count,count1)

			df2 = pd.read_csv('viis.csv')
			count2 = df2.iloc[:,2].astype(str).str.contains(adhar).any()

			if(count and count1 and count2==0):		
				return redirect(url_for('register1'))
			elif(count2!=0):
				error += "This Record is Already Present in VIIS"
			else:
				error += "Adhar/Voter is not in Database"
		
	return render_template('register.html',error=error)

@app.route('/register1', methods=['GET', 'POST'])
def register1():
	global name
	global adhar
	global voter
	global contact	
	if request.method=='POST':

		img = cv2.imread('static/images/test_image.jpg')
		cv2.imwrite('dataset/'+name+'.jpg', img)

		data_list = {'name':name,'adhar':adhar,'voter':voter,'vote':0,'contact':contact,'approve':0}
		df = pd.DataFrame(data_list,index=[0])
		df.to_csv('viis.csv', mode='a',header=False)

		return redirect(url_for('register'))

	return render_template('register1.html',name=name,adhar= adhar,voter=voter,contact=contact)


@app.route('/input', methods=['GET', 'POST'])
def input():
	global fname
	global lname
	global adhar
	global voter
	global otp

	df = pd.read_csv('viis.csv')
		
	if request.method=='POST':
		code = int(request.form['otp'])
		face = faceRecognition()
		print(face)
		print(code)
		print(fname)
		if len(face)>0:	
			if (face[0] == fname) and code == otp:
				for i in range(len(df)):
					if(df.values[i][1]==fname):
						df.iloc[i,4] = 1
						df.to_csv('viis.csv',index=False)
						return redirect(url_for('vote'))
		else:
			return redirect(url_for('video')) 

	return render_template('input.html',fname=fname,lname=lname,adhar= adhar,voter=voter)

@app.route('/video', methods=['GET', 'POST'])
def video():
	global fname
	global lname
	global adhar
	global voter
	global contact
	global otp
	f=0
	
	df = pd.read_csv('viis.csv')
	print(df)
	print(df.values[0][0])
	print(df.iloc[:,3])
	

	if request.method == 'POST':
		fname = request.form['fname']
		lname = request.form['lname']
		adhar = request.form['adhar']
		voter = request.form['voter']

		for i in range(len(df)):
			if(df.values[i][1]==fname and df.iloc[i,4]==0 and df.iloc[i,6]==1):
				print(df.values[i][1],df.iloc[i,4],df.iloc[i,6])
				f=1
				break
		if(f==1):
			otp = random.randrange(1000,9999)
			print(otp)
			contact = df.iloc[i,5]
			sendSMS('+12762658980', '+91'+str(contact), 'OTP for Voting:'+str(otp))
			return redirect(url_for('input'))
		else:
			return render_template('video.html',error="No record Found / You have voted already / Your Profile is not Approved")
	return render_template('video.html')

@app.route('/video_stream')
def video_stream():

	return Response(video_feed(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
	df = pd.read_csv('candidate.csv')
	c1 = df._get_value(0,'candidate')
	p1 = df._get_value(0,'Party')
	c2 = df._get_value(1,'candidate')
	p2 = df._get_value(1,'Party')
	c3 = df._get_value(2,'candidate')
	p3 = df._get_value(2,'Party')
	c4 = df._get_value(3,'candidate')
	p4 = df._get_value(3,'Party')
	if request.method == 'POST':
		df = pd.read_csv('candidate.csv')
		vote_id = int(request.form['can'])
		vote = df._get_value(vote_id,'votes')
		df._set_value(vote_id,'votes',vote+1)
		df.to_csv('candidate.csv',index=False)
		print(df)
		playsound('vote.wav')
		return redirect(url_for('video'))

	return render_template('vote.html',c1=c1,c2=c2,c3=c3,c4=c4,p1=p1,p2=p2,p3=p3,p4=p4)

@app.route('/result', methods=['GET', 'POST'])
def result():
	error = None
	if request.method == 'POST':
		if request.form['username'] != 'admin' or request.form['password'] != 'admin':
			error = 'Invalid Credentials. Please try again.'
		else:
			df = pd.read_csv('candidate.csv')
			df.sort_values(by=['votes'], inplace=True,ascending=False)
			df.to_html('templates/vote_count.html',index=False)
			return render_template('result.html',tables=[df.to_html(classes='data')], titles=df.columns.values,index=False)

	return render_template('result.html', error=error)

@app.route('/alogin', methods=['GET', 'POST'])
def alogin():
	error = None
	if request.method == 'POST':
		if request.form['username'] != 'admin' or request.form['password'] != 'admin':
			error = 'Invalid Credentials. Please try again.'
		else:
			return redirect(url_for('home1'))

	return render_template('alogin.html', error=error)

@app.route('/home1', methods=['GET', 'POST'])
def home1():
	return render_template('home1.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
	error = None
	if request.method == 'POST':
		if request.form['login'] == 'Clear List':
			row = ['candidate','Party','votes']
			myFile = open('candidate.csv','w')
			writer = csv.writer(myFile)
			writer.writerow(row)
			myFile.close()
		elif request.form['login'] == 'Add':
			can = request.form['can']
			party = request.form['party']
			row = [can,party,0]
			myFile = open('candidate.csv','a')
			writer = csv.writer(myFile)
			writer.writerow(row)
			myFile.close()			
	return render_template('add.html')

@app.route('/approve', methods=['GET', 'POST'])
def approve():
	global idx
	df = pd.read_csv('viis.csv')
	name = df._get_value(idx,'name')
	adhar = df._get_value(idx,'adhar')
	voter = df._get_value(idx,'voter')
	contact = df._get_value(idx,'contact')

	if request.method == 'POST':
		if request.form['sub'] == 'Next':
			df = pd.read_csv('viis.csv')
			if(idx<len(df)-1):
				idx = idx + 1
			else:
				idx = 0
		elif request.form['sub'] == 'Approve':
			df._set_value(idx,'approve',1)
			df.to_csv('viis.csv',index=False)

	return render_template('approve.html',name=name,adhar=adhar,voter=voter,contact=contact)
# No caching at all for API endpoints.
@app.after_request
def add_header(response):
	# response.cache_control.no_store = True
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)