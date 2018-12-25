
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
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

#Function to return deployment status in each Env Collection 

def check_deployment_status(db,affiliate,env,dict_ci_format,RMticket):
        collection_env=db[affiliate+'_'+env]
   #Getting list of files in RMticket from CI collection
        env_RMs_deployed_format={}
        env_RMs_deployed_format_sorted=OrderedDict()
        for doc in collection_env.find():
            for each_rm in doc['RM_ID'].keys():
            #print each_rm
                for build_time,RM in dict_ci_format.iteritems():
                    if RM == each_rm:
                        if datetime.datetime.strptime(build_time, '%a %b  %d %H:%M:%S %Y') < datetime.datetime.strptime(datetime.datetime.strptime(doc['RM_ID'][each_rm]['deployed_time'],'%Y_%m_%d_%H_%M_%S').ctime(), '%a %b  %d %H:%M:%S %Y'):
                            env_RMs_deployed_format[datetime.datetime.strptime(doc['RM_ID'][each_rm]['deployed_time'],'%Y_%m_%d_%H_%M_%S').ctime()]=RM
        formatted_dates_list=[each_date for each_date,value in env_RMs_deployed_format.iteritems()]
        formatted_dates_list.sort(key=lambda date:datetime.datetime.strptime(date, '%a %b  %d %H:%M:%S %Y'))
        sorted_patches_list=[env_RMs_deployed_format[each_date]  for each_date in formatted_dates_list]
        
        for i in range(len(formatted_dates_list)):
            env_RMs_deployed_format_sorted[sorted_patches_list[i]]=formatted_dates_list[i]

        dep_date=''
        if env != 'prod':
            for key,value in env_RMs_deployed_format_sorted.iteritems():
                if key == RMticket:
                    dep_date=value
                    print dep_date
            if dep_date != '':
                for key,value in env_RMs_deployed_format_sorted.iteritems():
                    if datetime.datetime.strptime(dep_date, '%a %b  %d %H:%M:%S %Y') < datetime.datetime.strptime(value, '%a %b  %d %H:%M:%S %Y'):
                        env_RMs_deployed_format_sorted[key] = value + ' ' + '-- Before'
                    elif datetime.datetime.strptime(dep_date, '%a %b  %d %H:%M:%S %Y') > datetime.datetime.strptime(value, '%a %b  %d %H:%M:%S %Y'):
                        env_RMs_deployed_format_sorted[key] = value + ' ' + '-- After'
                    else :
                        env_RMs_deployed_format_sorted[key] = value + ' ' + '-- Current'
        return env_RMs_deployed_format_sorted



def process_data(RMticket, Application, affiliate, prod):
    #Connecting to LGDOP mongoDB
    #connection = pymongo.MongoClient('mongodb://mongodb')
    connection = pymongo.MongoClient(port=27017)
    db=connection[Application]
    coll_name=affiliate + '_ci'
    print RMticket
    print coll_name
    collection_ci=db[coll_name]
    dict_output_list={} #Final ouput
    #Getting list of files in RMticket from CI collection
    list_files=[]
    for doc in collection_ci.find():
        for each_rm in doc['RM_ID'].keys():
            #print each_rm
            if each_rm == RMticket:
                for each_file in doc['RM_ID'][each_rm]['component'].keys():
                    if each_file not in list_files:
                        list_files.append(each_file)
    #Getting Dependent RMs list in ci collection
    dict_ci={}
    dict_ci_format={}
    dict_ci_format_sorted=OrderedDict()
    dict_Conflicts=OrderedDict()
    for doc in collection_ci.find():
        for each_rm in doc['RM_ID'].keys():
            #print each_rm
            #if each_rm != RMticket:
                for each_file in doc['RM_ID'][each_rm]['component'].keys():
                    if each_file in list_files:
                        dict_ci[each_rm]=doc['RM_ID'][each_rm]['build_time']
                        
                            
    #dict_ci[RMticket]=doc['RM_ID'][RMticket]['build_time']
    for key,value in dict_ci.iteritems():
        dict_ci_format[datetime.datetime.strptime(value,'%Y_%m_%d_%H_%M_%S').ctime()]=key
        formatted_dates_list=[each_date for each_date,value in dict_ci_format.iteritems()]
        formatted_dates_list.sort(key=lambda date:datetime.datetime.strptime(date, '%a %b  %d %H:%M:%S %Y'))
        sorted_patches_list=[dict_ci_format[each_date]  for each_date in formatted_dates_list]
        
    for i in range(len(formatted_dates_list)):
            dict_ci_format_sorted[sorted_patches_list[i]]=formatted_dates_list[i]
            dict_Conflicts[sorted_patches_list[i]]=formatted_dates_list[i]
    #print dict_ci_format_sorted    
    #print dict_Conflicts    
    print db
    print affiliate

    sit_RMs_deployed=check_deployment_status(db,affiliate,'sit',dict_ci_format,RMticket)
    #print sit_RMs_deployed

    UAT_RMs_deployed=check_deployment_status(db,affiliate,'uat',dict_ci_format,RMticket)
    #print UAT_RMs_deployed

    prod_RMs_deployed=check_deployment_status(db,affiliate,'prod',dict_ci_format,RMticket)
        
    dict_output_list['SIT']=sit_RMs_deployed
    dict_output_list['UAT']=UAT_RMs_deployed
    

    for key,value in sit_RMs_deployed.iteritems():
            element=dict_Conflicts.pop(key,'None')

    #print dict_Conflicts

    for key,value in UAT_RMs_deployed.iteritems():
            element=dict_Conflicts.pop(key,'None')
    
    #print dict_Conflicts
      
    dict_output_list['Conflicts']=dict_Conflicts

    if prod == 'Yes':
        dict_output_list['PROD']=prod_RMs_deployed
    else:
        for key,value in prod_RMs_deployed.iteritems():
            element=sit_RMs_deployed.pop(key,'None')
            element=UAT_RMs_deployed.pop(key,'None')
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

