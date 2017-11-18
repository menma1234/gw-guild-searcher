# -*- coding: utf-8 -*-

import json
import sqlite3
from functools import wraps
from itertools import groupby
from shutil import copy
from time import time
from string import strip
import csv

from flask import Flask, request, render_template

app = Flask(__name__)

DB_FILE = 'gbf-gw.sqlite'

GW_RANGE_QUERY = "select min(gw_num), max(gw_num) from rankings"
SEARCH_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where id in (select distinct id from cur_gw where id in (select distinct id from rankings where name like ? escape '!')) order by id, gw_num desc"
FIND_BY_ID_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where id = ? order by gw_num desc"
GET_GW_QUERY = "select gw_num, is_seed, name, rank, points, id from rankings where gw_num = ? order by is_seed, rank"
INSERT_QUERY = "insert or replace into rankings (gw_num, rank, name, points, id, is_seed) values (?, ?, ?, ?, ?, ?)"

def response_helper(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        
        if type(value) is tuple:
            (obj, return_code) = value
        else:
            obj = value
            return_code = 200
        
        return json.dumps(obj) if type(obj) is dict else obj, return_code, {'Content-Type': 'application/json; charset=utf-8'}
    
    return wrapper

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)

    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def likify(input_str):
    # sqlite doesn't support [] so no need to escape
    return '%{}%'.format(input_str.replace('!', '!!').replace('%', '!%').replace('_', '!_'))

def sort_guilds(data, search):
    def cmp_rank_seed(a, b):
        # superseeds first
        if a['gw_num'] != b['gw_num']:
            return a['gw_num'] - b['gw_num']
        
        # seeds next
        if a['is_seed'] != b['is_seed']:
            return b['is_seed'] - a['is_seed']
        
        # higher rank comes first
        return a['rank'] - b['rank']
    
    def cmp_func(a, b):
        a_name = a['data'][0]['name'].lower()
        b_name = b['data'][0]['name'].lower()
        
        # case 1 & 2: one has an exact matching name while the other doesn't
        if a_name == search and b_name != search:
            return -1
        
        if a_name != search and b_name == search:
            return 1
        
        # case 3: both have matching name, sort based on rank and seed status
        if a_name == search and b_name == search:
            return cmp_rank_seed(a['data'][0], b['data'][0])
        
        # case 4: neither have matching name
        # names that contain the search come first, then sort based on rank and seed status
        in_name_a = search in a_name
        in_name_b = search in b_name
        
        if in_name_a and not in_name_b:
            return -1
        
        if not in_name_a and in_name_b:
            return 1
        
        return cmp_rank_seed(a['data'][0], b['data'][0])
    
    search = search.lower()
    return sorted(data, cmp = cmp_func)

@app.route('/')
def index():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(GW_RANGE_QUERY)
        
        (min_gw, max_gw) = c.fetchone()
        return render_template('index.html', min_gw=min_gw, max_gw=max_gw)
    
    finally:
        conn.close()

@app.route('/search', methods=('POST',))
@response_helper
def get_guilds():
    obj = request.get_json(force=True)
    assert obj is not None
    
    if 'search' not in obj:
        return 'Missing search key', 400
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(SEARCH_QUERY, (likify(obj['search']),))
        
        result = []
        
        for id, group in groupby(c.fetchall(), lambda x: x[-1]):
            result.append({
                'id': id,
                'data': [{
                             'gw_num': gw_num,
                             'is_seed': is_seed,
                             'name': name,
                             'rank': rank,
                             'points': points
                         } for (gw_num, is_seed, name, rank, points, _) in group]
            })
        
        return {'result': sort_guilds(result, obj['search'])}
    
    finally:
        conn.close()

@app.route('/info/<int:id>')
@response_helper
def find_by_id(id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(FIND_BY_ID_QUERY, (id,))
        
        result = [{
                     'gw_num': gw_num,
                     'is_seed': is_seed,
                     'name': name,
                     'rank': rank,
                     'points': points
                  } for (gw_num, is_seed, name, rank, points, _) in c.fetchall()]
        
        return {
            'id': id,
            'data': result
        }
    
    finally:
        conn.close()

@app.route('/full/<int:num>')
@response_helper
def get_gw_data(num):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(GET_GW_QUERY, (num,))
        
        result = {}
        for is_seed, group in groupby(c.fetchall(), lambda x: x[1]):
            result['seed' if is_seed else 'regular'] = (
                [{
                    'name': name,
                    'rank': rank,
                    'points': points,
                    'id': id
                 } for (_, _, name, rank, points, id) in group]
            )
        
        return {
            'num': num,
            'data': result
        }
    
    finally:
        conn.close()

@app.route('/upload', methods=('GET', 'POST'))
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    else:
        obj = request.get_json(force = True)
        assert obj is not None
        
        if 'data' not in obj:
            return 'Missing upload data', 400
        
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(GW_RANGE_QUERY)
            
            (_, max_gw) = c.fetchone()
            
            lines = obj['data'].splitlines()
            reader = unicode_csv_reader(lines)
            
            for row in reader:
                if len(row) != 5:
                    return 'Invalid data format.', 400
                
                c.execute(INSERT_QUERY, [max_gw + 1] + [s.strip() for s in row])
        
            copy(DB_FILE, '{}.{}'.format(DB_FILE, str(int(time()))))
            conn.commit()
            
            return '', 200
        
        finally:
            conn.close()


if __name__ == '__main__':
    app.run()
