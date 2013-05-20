#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, HTTPError, request, response
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import json
import yaml
import datetime

f = open('config.yaml')
settings = yaml.load(f)
f.close()

# Connect to MongoDB and load database
client = MongoClient(settings['mongo']['host'], settings['mongo']['port'])
db = client[settings['mongo']['name']]

# Pre-define routes and their respective functions
def install_routes(app):
    app.route('/', ['ANY'], index)
    app.route('/shows', ['GET'], load_shows)
    #app.route('/shows/<column:re:[a-z_.]+>/<value>', ['GET'], load_shows)
    app.route('/shows/<group:re:[a-z_]+>', ['GET'], load_shows)
    app.route('/show/<_id>', ['GET'], load_show)
    app.route('/show/<_id>/<column:re:[a-z_.]+>', ['GET'], load_show)
    app.route('/staff', ['GET'], load_staff)
    app.route('/staff/<_id>', ['GET'], load_member)
    app.route('/staff/<_id>/shows', ['GET'], load_members_shows)

# Index page
def index():
    return "<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you join me \nin the oak tree?</pre>"

# Return a list of shows
def load_shows(group=None):#, column=None, value=None):
    if group:
        query = {
            'complete': { "status": "complete" },
            'incomplete': { "status": { "$in": [ "unaired", "airing", "incomplete" ] } },
            'aired': { "status": "airing", "progress.encoded": False, "airtime": {"$lt": datetime.datetime.utcnow()} },
            'current_episodes': { "status": "airing", "episodes": { "current": { "$gt": 0 } } }
        }.get(group)
        if not query:
            raise HTTPError(404, 'Group "{0}" does not exist.'.format(group))
        shows = db.shows.find(query)
'''    elif column:
        # maybe this route turned out to be a bad idea.
        shows = db.shows.find({column: value})'''
    else:
        shows = db.shows.find()
    return prepare_json(shows)

def load_show(_id, column=None):
    show = db.shows.find_one({'_id': ObjectId(_id)})
    if not show:
        raise HTTPError(404, 'There is no show with an ObjectId of "{0}".'.format(_id))
    if not column:
        return prepare_json([show])
    else:
        field = db.shows.find_one({'_id': ObjectId(_id)}, {column: 1, '_id': 0})
        if not field:
            raise HTTPError(404, 'The "{0}" field does not exist for {1}'.format(column, show['titles']['english']))
        return prepare_json([field])

def load_member(_id):
    member = db.staff.find_one({'_id': ObjectId(_id)})
    if not member:
        raise HTTPError(404, 'There is no staff member with an ObjectId of "{0}".'.format(_id))
    return prepare_json([member])

def load_staff():
    staff = db.staff.find()
    return prepare_json(staff)

def load_members_shows(_id):
    oid = ObjectId(_id)
    results = db.shows.find({'$or': [{'staff.translator.id': oid}, {'staff.typesetter.id': oid},
                                 {'staff.timer.id': oid}, {'staff.editor.id': oid}]})
    shows = map(lambda s: s['titles']['english'], results)
    return prepare_json(shows)

app = Bottle()

@app.post('/shows/create')
def create_show():
    show_data = request.json
    #sanitization
    # shows.save(show_data)
    return show_data

@app.put('/show/<_id>')
def update_show(_id):
    show_data = request.json
    #sanitization, set values for null data
    # show.update({id: id}, {'$set': {show_data}})
    return show_data

@app.delete('/show/<_id')
def delete_show(_id):
    #check if exists
    # shows.remove({id: id})
    return {'success': True}

@app.get('/show/<_id>/blame')
def who_to_blame_for(_id):
    #resolve id function here
    # shows.find({id: id})
    return "Return position and value for whoever is stalling show '{0}'.".format(_id)

@app.post('/staff/create')
def add_new_member():
    member_data = request.json
    #sanitization
    # staff.save(member_data)
    return member_data

@app.put('/staff/<_id>')
def update_member(_id):
    member_data = request.json
    #sanitization, set values for null data
    # staff.update({id: id}, {'$set': {member_data}})
    return member_data

@app.delete('/staff/<_id>')
def delete_member(_id):
    # staff.remove({id: id})
    return {'success': True}

def prepare_json(ingredients):
    response.content_type = 'application/json'
    #for item in ingredients:
        #item['_id'] = str(item['_id'])
    return dumps(ingredients)

install_routes(app)
app.run(host=settings['bottle']['host'], port=settings['bottle']['port'],
        debug=settings['bottle']['debug'], reloader=settings['bottle']['reloader'])
