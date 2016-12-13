# -*- coding: utf-8 -*-

import logging
import json
import sqlite3
from types import TupleType, DictType
from functools import wraps

from flask import Flask, request

app = Flask(__name__)

MAX_GW_QUERY = "select max(gw_num) from rankings"
SEARCH_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where id in (select distinct id from cur_gw where id in (select distinct id from rankings where name like ? escape '!')) order by id, gw_num desc"

def response_helper(f):
    @wraps(f)
    def wrapper():
        value = f()
        
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
    conn = sqlite3.connect('gbf-gw.sqlite')
    c = conn.cursor()
    c.execute(MAX_GW_QUERY)

    return 'Guild Wars data available up to GW #' + str(c.fetchone()[0])

@app.route('/search', methods = ('POST',))
@response_helper
def get_guilds():
    obj = request.get_json(force = True)
    assert obj is not None
    
    if 'search' not in obj:
        return 'Missing search key', 400
    
    conn = sqlite3.connect('gbf-gw.sqlite')
    c = conn.cursor()
    bindings = (''.join(('%', like_escape(obj['search']), '%')),)
    c.execute(SEARCH_QUERY, bindings)
    
    result = {}
    for (gw_num, is_seed, name, rank, points, id) in c.fetchall():
        entry = {
                    'gw_num': gw_num,
                    'is_seed': is_seed,
                    'name': name,
                    'rank': rank,
                    'points': points
                }
        
        if id in result:
            result[id].append(entry)
        else:
            result[id] = [entry]
    
    conn.close()
    return result

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

if __name__ == '__main__':
    app.run()
