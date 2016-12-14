# -*- coding: utf-8 -*-

import logging
import json
import sqlite3
from types import TupleType, DictType
from functools import wraps
from itertools import groupby

from flask import Flask, request

app = Flask(__name__)

MAX_GW_QUERY = "select max(gw_num) from rankings"
SEARCH_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where id in (select distinct id from cur_gw where id in (select distinct id from rankings where name like ? escape '!')) order by id, gw_num desc"
FIND_BY_ID_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where id = ? order by gw_num desc"
GET_GW_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where gw_num = ? order by is_seed, rank"

def response_helper(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        
        if type(value) is TupleType:
            (obj, return_code) = value
        else:
            obj = value
            return_code = 200
        
        return json.dumps(obj) if type(obj) is DictType else obj, return_code, {'Content-Type': 'application/json; charset=utf-8'}
    
    return wrapper

def like_escape(str):
    # sqlite doesn't support [] so no need to escape
    return str.replace('!', '!!').replace('%', '!%').replace('_', '!_')

@app.route('/')
@response_helper
def index():
    try:
        conn = sqlite3.connect('gbf-gw.sqlite')
        c = conn.cursor()
        c.execute(MAX_GW_QUERY)
        
        return 'Guild Wars data available up to GW #' + str(c.fetchone()[0])
    
    finally:
        conn.close()

@app.route('/search', methods = ('POST',))
@response_helper
def get_guilds():
    obj = request.get_json(force = True)
    assert obj is not None
    
    if 'search' not in obj:
        return 'Missing search key', 400
    
    try:
        conn = sqlite3.connect('gbf-gw.sqlite')
        c = conn.cursor()
        bindings = (''.join(('%', like_escape(obj['search']), '%')),)
        c.execute(SEARCH_QUERY, bindings)
        
        result = {}
        
        for id, group in groupby(c.fetchall(), lambda x: x[-1]):
            result[id] = [{
                            'gw_num': gw_num,
                            'is_seed': is_seed,
                            'name': name,
                            'rank': rank,
                            'points': points
                         } for (gw_num, is_seed, name, rank, points, _) in group]
        
        return result
    
    finally:
        conn.close()

@app.route('/info/<int:id>')
@response_helper
def find_by_id(id):
    try:
        conn = sqlite3.connect('gbf-gw.sqlite')
        c = conn.cursor()
        c.execute(FIND_BY_ID_QUERY, (id,))
        
        result = [{
                    'gw_num': gw_num,
                    'is_seed': is_seed,
                    'name': name,
                    'rank': rank,
                    'points': points
                 } for (gw_num, is_seed, name, rank, points, _) in c.fetchall()]
        
        return {id: result}
    
    finally:
        conn.close()

@app.route('/full/<int:id>')
@response_helper
def get_gw_data(id):
    try:
        conn = sqlite3.connect('gbf-gw.sqlite')
        c = conn.cursor()
        c.execute(GET_GW_QUERY, (id,))
        
        result = [{
                    'is_seed': is_seed,
                    'name': name,
                    'rank': rank,
                    'points': points,
                    'id': id
                 } for (_, is_seed, name, rank, points, id) in c.fetchall()]
        
        return {id: result}
    
    finally:
        conn.close()

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

if __name__ == '__main__':
    app.run()
