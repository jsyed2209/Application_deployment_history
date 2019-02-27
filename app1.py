

from flask import Flask, session, render_template, request, redirect, json,url_for
#from pandas_datareader import data as web
import datetime
import re
import os
import pymongo
from flask import Session
from collections import OrderedDict
#from flask_wtf import FlaskForm
#from wtforms.validators import DataRequired



app = Flask(__name__)

#Function to return sorted dictionary in each env Collection
def sorted_dict(dict_collection):
		dict_collection_format={}
		sorted_patches_list=[]
		formatted_dates_list=[]
		dict_collection_format_sorted=OrderedDict()
		for key,value in dict_collection.iteritems():
			dict_collection_format[datetime.datetime.strptime(value,'%Y_%m_%d_%H_%M_%S').ctime()]=key
			formatted_dates_list=[each_date for each_date,value in dict_collection_format.iteritems()]
			formatted_dates_list.sort(key=lambda date:datetime.datetime.strptime(date, '%a %b  %d %H:%M:%S %Y'))
			sorted_patches_list=[dict_collection_format[each_date]  for each_date in formatted_dates_list]
			
		print sorted_patches_list
		print formatted_dates_list
			
		for i in range(len(sorted_patches_list)):
			dict_collection_format_sorted[sorted_patches_list[i]]=formatted_dates_list[i]
		
		return dict_collection_format_sorted
		
#Function to return deployment status in each Env Collection		
def Env_patches_list(db,affiliate,env,sorted_patches_dict):		
		prod_patches={}
		collection_env=db[affiliate+'_'+env]
		print collection_env
		for doc in collection_env.find():
			for each_rm in doc['RM_ID'].keys():
				for RM,date in sorted_patches_dict.iteritems():
					if RM==each_rm:
						prod_patches[RM]=doc['RM_ID'][each_rm]['deployed_time']
		prod_patches=sorted_dict(prod_patches)
		return prod_patches		

def process_data(RMticket, Application, affiliate, Prod_status):
		#Connecting to LGDOP mongoDB
		#connection = pymongo.MongoClient('mongodb://mongodb')
		connection = pymongo.MongoClient(port=27017)
		db=connection[Application]
		coll_name=affiliate + '_ci'
		print RMticket
		print coll_name
		collection_ci=db[coll_name]
		dict_output_list=OrderedDict() #Final ouput
		#Getting list of files in RMticket from CI collection
		list_files=[]
		for doc in collection_ci.find():
			for each_rm in doc['RM_ID'].keys():
				if each_rm == RMticket:
					for each_file in doc['RM_ID'][each_rm]['component'].keys():
						if each_file not in list_files:
							list_files.append(each_file)
		#Getting Dependent RMs list in ci collection
		dict_ci={}
		for doc in collection_ci.find():
			for each_rm in doc['RM_ID'].keys():
					for each_file in doc['RM_ID'][each_rm]['component'].keys():
						if each_file in list_files:
							dict_ci[each_rm]=doc['RM_ID'][each_rm]['build_time']
                        
		print dict_ci
		print db
		print affiliate
		sorted_patches_dict=OrderedDict()
		sorted_patches_dict=sorted_dict(dict_ci)
		print  'sorted_patches_dict:-'
		print   sorted_patches_dict
		prod_sorted_patches=OrderedDict()
		prod_sorted_patches=Env_patches_list(db,affiliate,'prod',sorted_patches_dict)
		print  'prod_sorted_patches:-'
		print   prod_sorted_patches
				
		for key,value in prod_sorted_patches.iteritems():
			 element=sorted_patches_dict.pop(key,'None')
		
		uat_sorted_patches=OrderedDict()
		uat_sorted_patches=Env_patches_list(db,affiliate,'uat',sorted_patches_dict)
		print  'uat_sorted_patches:-'
		print   uat_sorted_patches
				
		for key,value in uat_sorted_patches.iteritems():
			 element=sorted_patches_dict.pop(key,'None')
			 
		sit_sorted_patches=OrderedDict()
		sit_sorted_patches=Env_patches_list(db,affiliate,'sit',sorted_patches_dict)
		print  'sit_sorted_patches:-'
		print   sit_sorted_patches
		
		for key,value in sit_sorted_patches.iteritems():
			 element=sorted_patches_dict.pop(key,'None')
			 
		print sorted_patches_dict
		
		if Prod_status == 'Yes':
			dict_output_list['PROD']=prod_sorted_patches
			
		dict_output_list['UAT']=uat_sorted_patches
		dict_output_list['SIT']=sit_sorted_patches
		dict_output_list['Not Installed in SIT&UAT&PROD']=sorted_patches_dict
		
		bolstatus=0
		for key,value in dict_output_list.iteritems():
			if key == 'PROD' or key == 'UAT' or key == 'SIT':
				for key1,value1 in value.iteritems():
					if key1==RMticket:
						bolstatus=1
						value[key1]=value1+'-**-'+'Current'
					else:
						if bolstatus==1:
							value[key1]=value1+'-**-'+'Before'
						else:
							value[key1]=value1+'-**-'+'After'
		
		return dict_output_list
		
@app.route('/dependency_check')
def homePage():
    return render_template('Dependency.html')

@app.route('/dependency_check_output')
def dependency_check_output():
    dict_output = OrderedDict()
    
    a=session.get('RMticket', None)
    b=session.get('application', None)
    c=session.get('affiliate', None)
    d=session.get('prod', None)
    
    dict_output['RMticket']=a
    dict_output['Application']=b
    dict_output['Affiliate']=c
    dict_output['Prod inclusion']=d
    dict_output_list=process_data(a,b,c,d)
    for key,value in dict_output_list.iteritems():
		dict_output[key]=value
    print dict_output
    
    return render_template('Output.html',dependency_check_output=dict_output)

@app.route('/submitDetails', methods=['POST'])
def submitDetails():
    if request.method == 'POST':
        RMticket =  request.form['RMticket']
        session['RMticket']=RMticket
        application = request.form['application']
        session['application']=application
        affiliate = request.form['affiliate']
        session['affiliate']=affiliate
        prod = request.form['prod']
        session['prod']=prod
        #return json.dumps({'status':'OK','RMticket':RMticket,'Application':application,'Affiliate':affiliate,'Prod':prod});
        return redirect(url_for('dependency_check_output'))


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    #sess.init_app(app)
    app.run(debug = True)

