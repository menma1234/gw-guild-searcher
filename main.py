# -*- coding: utf-8 -*-

import json
import sqlite3
from types import TupleType, DictType
from functools import wraps
from itertools import groupby

from flask import Flask, request, render_template

app = Flask(__name__)

GW_RANGE_QUERY = "select min(gw_num), max(gw_num) from rankings"
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

def likify(str):
    # sqlite doesn't support [] so no need to escape
    return ''.join(('%', str.replace('!', '!!').replace('%', '!%').replace('_', '!_'), '%'))

@app.route('/')
def index():
    try:
        conn = sqlite3.connect('gbf-gw.sqlite')
        c = conn.cursor()
        c.execute(GW_RANGE_QUERY)
        
        (min_gw, max_gw) = c.fetchone()
        return render_template('index.html', min_gw = min_gw, max_gw = max_gw)
    
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
        c.execute(SEARCH_QUERY, (likify(obj['search']),))
        
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

if __name__ == '__main__':
    app.run()
