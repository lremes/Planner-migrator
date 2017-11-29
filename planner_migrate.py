from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_oauthlib.client import OAuth, OAuthException
import migrator
import json
import os
from werkzeug.utils import secure_filename

# from flask_sslify import SSLify

from logging import Logger
import uuid

app = Flask(__name__)
# sslify = SSLify(app)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

UPLOAD_FOLDER = '/tmp/flask_uploads'
ALLOWED_EXTENSIONS = set(['json'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

config = json.load(open('config.json'))

# Put your consumer key and consumer secret into a config file
# and don't check it into github!!
export_permissions = [
    'User.Read',
#    'User.Read.All',
    'Directory.Read.All',
    'Group.Read.All',
    'Group.ReadWrite.All',
    ]
microsoft = oauth.remote_app(
    'PlannerExporter',
    consumer_key= config['export']['consumer_key'],
    consumer_secret=config['export']['consumer_secret'],
    request_token_params={'scope': ' '.join(export_permissions)},
    base_url='https://graph.microsoft.com/v1.0/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
)

import_permissions = [
    'User.Read',
#    'Directory.Read.All',
#    'Group.Read.All',
#    'Group.ReadWrite.All'
#    'User.Read.All',
    ]
new_planner = oauth.remote_app(
    'PlannerImporter',
    consumer_key=config['import']['consumer_key'],
    consumer_secret=config['import']['consumer_key'],
    request_token_params={'scope': ' '.join(import_permissions)},
    base_url='https://graph.microsoft.com/v1.0/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
)
#new_planner = oauth.remote_app(
#    'PlannerImporter',
#    consumer_key='9b2d4bfe-b163-4f40-a7f2-1f9dbaa65b0f',
#    consumer_secret='zjyqxPQD661~-{qpFZOF07=',
#    request_token_params={'scope': ' '.join(import_permissions)},
#    base_url='https://graph.microsoft.com/v1.0/',
#    request_token_url=None,
#    access_token_method='POST',
#    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
#    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
#)


#exporter = migrator.Migrator(microsoft)

#PLANNER_API_URL = 'https://graph.microsoft.com/v1.0/planner'

@app.route('/')
def index():
    return render_template('hello.html')

@app.route('/login', methods = ['POST', 'GET'])
def login():

    if 'microsoft_token' in session:
        return redirect(url_for('me'))

    # Generate the guid to only accept initiated logins
    guid = uuid.uuid4()
    session['state'] = guid

    return microsoft.authorize(callback=url_for('authorized', _external=True), state=guid)
    
@app.route('/logout', methods = ['POST', 'GET'])
def logout():
    session.pop('microsoft_token', None)
    session.pop('microsoft_token2', None)
    session.pop('state', None)
    session.pop('state2', None)
    return redirect(url_for('index'))

@app.route('/login/authorized')
def authorized():
    response = microsoft.authorized_response()
    if response is None:
        return "Access Denied: Reason=%s\nError=%s" % (
            response.get('error'), 
            request.get('error_description')
        )
            
    # Check response for state
    print("Response: " + str(response))
    if str(session['state']) != str(request.args['state']):
        raise Exception('State has been messed with, end authentication')
        
    # Okay to store this in a local variable, encrypt if it's going to client
    # machine or database. Treat as a password. 
    session['microsoft_token'] = (response['access_token'], '')
    return redirect(url_for('me'))

@app.route('/me')
def me():
    me = microsoft.get('me')
    exporter = migrator.Migrator(microsoft)
    groups = exporter.get("users/%s/memberOf" % (me.data.get('id')), session.get('microsoft_token')[0])
    return render_template('me.html', me=me, groups=groups)

@app.route('/export')
def export():
    gId = request.args.get('gId', '')

    # me aka. owner
    me = microsoft.get('me')

    output_data = {}

    # plan
    exporter = migrator.Migrator(microsoft)
    
    exporter.plans = exporter.get("groups/%s/planner/plans" % (gId), session.get('microsoft_token')[0])['value']
    plan = exporter.plans[0]
    output_data['plan'] = plan
    plan['details'] = exporter.get("planner/plans/%s/details" % (exporter.getPlanId(0)), session.get('microsoft_token')[0])
    
    # buckets /planner/plans/<id>/buckets
    plan['buckets'] = exporter.get("planner/plans/%s/buckets" % (exporter.getPlanId(0)), session.get('microsoft_token')[0])
    
    # tasks /planner/plans/{id}/tasks
    tasks = exporter.get("planner/plans/%s/tasks" % (exporter.getPlanId(0)), session.get('microsoft_token')[0])['value']
    plan['tasks'] = []
    
    for task in tasks:
        task['details'] = exporter.get("planner/tasks/%s/details" % (task['id']), session.get('microsoft_token')[0])
        plan['tasks'].append(task)

    with open('planner_export.json', 'w') as outfile:
        json.dump(output_data, outfile)

    #print "Logging in to new planner"
    #return new_planner.authorize(callback=url_for('import_login', _external=True), state=guid2)
    return redirect(url_for('logout'))

@app.route('/import')
def import_index():
    return render_template('import.html')

@app.route('/import/do')
def import_data():
    # load file
    input_file = json.load(open(session['filename']))
    print "Loaded file %s" % (session['filename'])
    
    me = new_planner.get('me')
    
    importer = migrator.Migrator(new_planner)
    # create new plan
    #groups = migrator.get("users/%s/memberOf" % (me.data.get('id')), session.get('microsoft_token')[0])
    #groups = migrator.get("me/memberOf" % (me.data.get('id')), session.get('microsoft_token')[0])
    groups = importer.get("me/memberOf", session.get('microsoft_token')[0])
    # find correct group
    for g in groups:
        print g

    #new_plan = migrator.create_plan(groups['value'][0].get('id'), 'ENW migration test', session.get('microsoft_token2')[0])
    
    # create buckets
    # create tasks
    # update task details
    # add comments
    # add attachments
    
    return render_template('import_done.html', me=me.data)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.route('/import/upload', methods=['GET', 'POST'])
def import_upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['filename'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            return render_template('import_upload.html', file=file)
    return redirect(url_for('import_index'))
        
@app.route('/import/start', methods=['GET', 'POST'])
def import_start():
    session.pop('microsoft_token2', None)
    session.pop('state2', None)

    # Generate the guid to only accept initiated logins
    guid2 = uuid.uuid4()
    session['state2'] = guid2

    return new_planner.authorize(callback=url_for('import_login', _external=True), state=guid2)
            
@app.route('/login/import')
def import_login():
    print "IMPORT STARTED"
    response = new_planner.authorized_response()
    if response is None:
        return "Access Denied: Reason=%s\nError=%s" % (
            response.get('error'), 
            request.get('error_description')
        )
            
    # Check response for state
    print("Response: " + str(response))
    if str(session['state2']) != str(request.args['state']):
        raise Exception('State has been messed with, end authentication')
        
    # Okay to store this in a local variable, encrypt if it's going to client
    # machine or database. Treat as a password. 
    session['microsoft_token2'] = (response['access_token'], '')
    
    return redirect(url_for('import_data'))

# If library is having trouble with refresh, uncomment below and implement refresh handler
# see https://github.com/lepture/flask-oauthlib/issues/160 for instructions on how to do this

# Implements refresh token logic
# @app.route('/refresh', methods=['POST'])
# def refresh():

@microsoft.tokengetter
def get_microsoft_oauth_token():
    return session.get('microsoft_token')

@new_planner.tokengetter
def get_microsoft_oauth_token():
    return session.get('microsoft_token2')

if __name__ == '__main__':
    app.run()