from flask import Flask, request, jsonify, render_template, g
import math
import sqlite3

app = Flask(__name__)

# Constants for maximum capacities
MAX_CAPACITY = {
    "A380-800": {
        "Economy": 853,
        "Business": 80,  # Adjust as needed
        "First": 10,     # Adjust as needed
        "Cargo": 200     # Adjust as needed
    },
    "A350-1000": {
        "Economy": 522,
        "Business": 60,  # Adjust as needed
        "First": 8,      # Adjust as needed
        "Cargo": 150     # Adjust as needed
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
                flight_duration TEXT NOT NULL  -- Ensure flight_duration is included
            )
        ''')
        db.commit()

init_db()

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM calculations WHERE table_name = "Air Minatozaki" ORDER BY id ASC')
    air_minatozaki_data = cursor.fetchall()
    
    cursor.execute('SELECT * FROM calculations WHERE table_name = "Zenithal Airlines" ORDER BY id ASC')
    zenithal_airlines_data = cursor.fetchall()
    
    return render_template('index.html', 
                           air_minatozaki_data=air_minatozaki_data,
                           zenithal_airlines_data=zenithal_airlines_data)

@app.route('/calculate', methods=['POST'])
def calculate():
    airport_name = request.form['airport_name']
    aircraft_type = request.form['aircraft_type']
    flight_duration = request.form['flight_duration']

    if flight_duration == '12':
        division_factor = 4
    elif flight_duration == '8':
        division_factor = 8
    else:
        division_factor = 2  # Default to 24-hour flight

    economy = int(request.form['economy']) // division_factor
    business = int(request.form['business']) // division_factor
    first = int(request.form['first']) // division_factor
    cargo = int(request.form['cargo']) // division_factor
    table_selection = request.form['table_selection']

    max_capacity = MAX_CAPACITY.get(aircraft_type, MAX_CAPACITY["A380-800"])

    results = []

    for i in range(1):  # Assuming one result per calculation
        result = {
            "Airport Name": airport_name,
            "Aircraft Type": aircraft_type,
            "Economy": economy,
            "Business": business,
            "First": first,
            "Cargo": cargo,
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
