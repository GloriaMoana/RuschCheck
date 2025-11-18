import os
import sqlite3
from flask import Flask, render_template, request, jsonify, g
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from detection import average_people_in_video

DATABASE = os.path.join(os.path.dirname(__file__), 'data.sqlite')

app = Flask(__name__, static_url_path='/static')

#locations that we can dynamically add and delete to allowing for easy accesibility by us (devs)
LOCATIONS = {
    'student_union': {
        'name': 'Student Union, SJSU',
        'video': 'videos/lotsofpeoplewalking.mp4',
        'image': 'images/studentunion.jpg',
        'capacity': 33,
        'address': 'Student Union, SJSU'
    },
    'clark_hall': {
        'name': 'Clark Hall, SJSU',
        'video': 'videos/lotsofpeoplewalking.mp4',
        'image': 'images/clarkhall.jpg',
        'capacity': 60,
        'address': 'Clark Hall, SJSU'
    },
    'engineering_building': {
        'name': 'Engineering Building, SJSU',
        'video': 'videos/lotsofpeoplewalking.mp4',
        'image': 'images/engineeringblding.jpg',
        'capacity': 150,
        'address': 'Engineering Building, SJSU'
    },
    'mlk_library': {
        'name': 'MLK Library, SJSU',
        'video': 'videos/lotsofpeoplewalking.mp4',
        'image': 'images/mlklibrary.jpg',
        'capacity': 81,
        'address': 'MLK library, SJSU'
    }
}

#using sqllite db to store information
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#our basic table layout is the id, location name, # of people, cpacity, percent full, level(how full), the address, and last time it was updated
def init_db():
    db = get_db()
    db.execute(
        '''CREATE TABLE IF NOT EXISTS status (
            id TEXT PRIMARY KEY,
            location_name TEXT,
            average_people INTEGER,
            capacity INTEGER,
            percent REAL,
            level TEXT,
            address TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    db.commit()

with app.app_context():
    init_db()


#These are just the routes for each of the pages
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/spaces')
def spaces():
    db = get_db()
    cur = db.execute('SELECT * FROM status')
    rows = cur.fetchall()
    statuses = {r['id']: dict(r) for r in rows}

    return render_template('spaces.html', locations=LOCATIONS, statuses=statuses)

@app.route('/help')
def help_page():
    return render_template('help.html')


#yolo api responsible for detecting the people
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    loc_id = data.get('location')

    if loc_id not in LOCATIONS:
        return jsonify({'error': 'Unknown location'}), 400

    loc = LOCATIONS[loc_id]

    video_path = loc['video']
    if not os.path.exists(video_path):
        return jsonify({'error': f'Video file not found: {video_path}'}), 404

    try:
        avg_people = average_people_in_video(video_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    capacity = loc['capacity']
    percent = (avg_people / capacity) * 100 if capacity > 0 else 0

    if percent > 60:
        level = 'High'
    elif percent >= 40:
        level = 'Medium'
    else:
        level = 'Low'

    #saving the congestion track to the database
    db = get_db()
    db.execute(
        '''INSERT OR REPLACE INTO status
           (id, location_name, average_people, capacity, percent, level, address, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
        (loc_id, loc['name'], int(round(avg_people)), capacity, round(percent, 1), level, loc['address'])
    )
    db.commit()

    return jsonify({
        'id': loc_id,
        'location': loc['name'],
        'average_people': int(round(avg_people)),
        'capacity': capacity,
        'percent': round(percent, 1),
        'level': level,
        'address': loc['address']
    })


#gettin gthe lates results from teh previous user check from the database without running yolo again(unless user runs it again)
@app.route('/api/get_last_status', methods=['POST'])
def get_last_status():
    data = request.get_json()
    loc_id = data.get('location')

    db = get_db()
    row = db.execute("SELECT * FROM status WHERE id = ?", (loc_id,)).fetchone()

    if not row:
        return jsonify({'error': 'No previous data'}), 404

    return jsonify(dict(row))


if __name__ == '__main__':
    app.run(debug=True)
