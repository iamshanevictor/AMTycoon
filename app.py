from flask import Flask, request, jsonify, render_template, g
import math
import sqlite3

app = Flask(__name__)

# Constants for maximum capacities
MAX_CAPACITY = {
    "A380-800": {
        "Economy": 853,
        "Business": 80,
        "First": 10,
        "Cargo": 200
    },
    "A350-1000": {
        "Economy": 522,
        "Business": 60,
        "First": 8,
        "Cargo": 150
    }
}

# Path to the SQLite database
DATABASE = 'airline_demand.db'

# Initialize database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database on application startup
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airport_name TEXT NOT NULL,
                aircraft_type TEXT NOT NULL,
                economy INTEGER NOT NULL,
                business INTEGER NOT NULL,
                first INTEGER NOT NULL,
                cargo INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                flight_duration TEXT NOT NULL
            )
        ''')
        db.commit()

init_db()

# Function to fetch paginated data
def fetch_paginated_data(table_name, page, sort_by):
    db = get_db()
    cursor = db.cursor()

    offset = (page - 1) * 10
    if sort_by == 'name_asc':
        cursor.execute(f'SELECT * FROM calculations WHERE table_name = ? ORDER BY airport_name ASC LIMIT 10 OFFSET ?', (table_name, offset))
    elif sort_by == 'name_desc':
        cursor.execute(f'SELECT * FROM calculations WHERE table_name = ? ORDER BY airport_name DESC LIMIT 10 OFFSET ?', (table_name, offset))
    elif sort_by == 'economy_asc':
        cursor.execute(f'SELECT * FROM calculations WHERE table_name = ? ORDER BY economy ASC LIMIT 10 OFFSET ?', (table_name, offset))
    elif sort_by == 'economy_desc':
        cursor.execute(f'SELECT * FROM calculations WHERE table_name = ? ORDER BY economy DESC LIMIT 10 OFFSET ?', (table_name, offset))
    else:
        cursor.execute(f'SELECT * FROM calculations WHERE table_name = ? LIMIT 10 OFFSET ?', (table_name, offset))

    return cursor.fetchall()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', None, type=str)

    db = get_db()
    cursor = db.cursor()

    # Fetch data for Air Minatozaki
    air_minatozaki_data = fetch_paginated_data('Air Minatozaki', page, sort_by)

    # Fetch data for Zenithal Airlines
    zenithal_airlines_data = fetch_paginated_data('Zenithal Airlines', page, sort_by)

    return render_template('index.html',
                           air_minatozaki_data=air_minatozaki_data,
                           zenithal_airlines_data=zenithal_airlines_data,
                           page=page, sort_by=sort_by)

@app.route('/calculate', methods=['POST'])
def calculate():
    airport_name = request.form['airport_name']
    aircraft_type = request.form['aircraft_type']
    economy = int(request.form['economy'])
    business = int(request.form['business'])
    first = int(request.form['first'])
    cargo = int(request.form['cargo'])
    table_selection = request.form['table_selection']
    flight_duration = request.form['flight_duration']

    max_capacity = MAX_CAPACITY.get(aircraft_type, MAX_CAPACITY["A380-800"])
    max_economy_capacity = max_capacity["Economy"]
    num_aircraft_economy = math.ceil(economy / max_economy_capacity)
    remaining_economy = economy
    results = []

    for i in range(num_aircraft_economy):
        if remaining_economy > 0:
            eco = min(remaining_economy, max_economy_capacity)
            remaining_economy -= eco
        else:
            eco = 0

        if i == num_aircraft_economy - 1:
            result = {
                "Airport Name": f"{airport_name} {i + 1}" if i > 0 else airport_name,
                "Aircraft Type": aircraft_type,
                "Economy": eco,
                "Business": business,
                "First": first,
                "Cargo": cargo,
                "Table Name": table_selection,
                "Flight Duration": flight_duration
            }
        else:
            result = {
                "Airport Name": f"{airport_name} {i + 1}" if i > 0 else airport_name,
                "Aircraft Type": aircraft_type,
                "Economy": eco,
                "Business": 0,
                "First": 0,
                "Cargo": 0,
                "Table Name": table_selection,
                "Flight Duration": flight_duration
            }

        results.append(result)

    db = get_db()
    cursor = db.cursor()
    for entry in results:
        cursor.execute('''
            INSERT INTO calculations (airport_name, aircraft_type, economy, business, first, cargo, table_name, flight_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (entry['Airport Name'], entry['Aircraft Type'], entry['Economy'], entry['Business'], entry['First'], entry['Cargo'], entry['Table Name'], entry['Flight Duration']))
    db.commit()

    return jsonify(results)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM calculations WHERE id = ?', (id,))
    db.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
