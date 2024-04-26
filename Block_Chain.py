# Description: This file contains the code for the blockchain implementation
from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib.pyplot as plt
from .wallet import *
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time

from .utils import *
app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="blockchain"
)
cursor = db.cursor()
def calculate_energy_token(data):
    # Implementation depends on your specific requirements
    return len(data)  # For example, the number of energy tokens could be the length of the data



def add_block(data, previous_hash, wallet, energy_token, state):
    block = {
        'data': data,
        'previous_hash': previous_hash,
        'wallet': wallet,
        'energy_token': {
            'amount': energy_token,
            'state': state
        }
    }
    return block

def verify_blockchain(blockchain):
    for i in range(1, len(blockchain)):
        if blockchain[i]['previous_hash'] != blockchain[i-1]['hash']:
            return False
    return True

def should_change_to_passive(transaction):
    creation_time = transaction['energy_token']['creation_time']
    current_time = time.time()
    if current_time - creation_time > 60:  # Change to 'PASSIVE' after 60 seconds
        return True
    return False

def check_token_state():
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()

    for vehicle in vehicles:
        wallet = json.loads(vehicle[1])
        for transaction in wallet['transactions']:
            if transaction['energy_token']['state'] == 'ACTIVE':
                # Check if the token should be changed to 'PASSIVE'
                if should_change_to_passive(transaction):  # You need to implement this function
                    transaction['energy_token']['state'] = 'PASSIVE'
                    cursor.execute("UPDATE vehicles SET Wallet = %s WHERE VehicleID = %s", (json.dumps(wallet), vehicle[0]))
                    db.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(check_token_state, 'interval', minutes=1)
scheduler.start()


@app.route('/')
def index():
    return render_template('input.html')

@app.route('/update_records', methods=['POST'])

def update_records():
    group_id = request.form['group_id']
    vehicle_id = request.form['vehicle_id']
    vehicle_details = request.form['vehicle_details']

    private_key, public_key = generate_key_pair()
    private_key_hex = serialize_private_key(private_key)
    public_key_hex = serialize_public_key(public_key)

    encrypted_data = encrypt_data(vehicle_details, public_key)

    cursor.execute("INSERT INTO vehicles (GroupID, VehicleID, PublicKey, EncryptedData) VALUES (%s, %s, %s, %s)", (group_id, vehicle_id, public_key_hex, encrypted_data))
    db.commit()

    return "Data added successfully"

@app.route('/add_group_vehicle_relation', methods=['POST'])
def add_group_vehicle_relation():
    group_id = request.form['group_id']
    vehicle_id = request.form['vehicle_id']

    cursor.execute("SELECT GroupID, VehicleID FROM relations WHERE GroupID = %s AND VehicleID = %s", (group_id, vehicle_id))
    existing_relation = cursor.fetchone()

    if existing_relation:
        return "Relation already exists"

    cursor.execute("SELECT GroupID FROM groups WHERE GroupID = %s", (group_id,))
    group_data = cursor.fetchone()

    cursor.execute("SELECT VehicleID FROM vehicles WHERE VehicleID = %s", (vehicle_id,))
    vehicle_data = cursor.fetchone()

    if not group_data or not vehicle_data:
        return "Invalid group or vehicle"

    cursor.execute("INSERT INTO relations (GroupID, VehicleID) VALUES (%s, %s)", (group_id, vehicle_id))
    db.commit()

    return "Relation added successfully"

@app.route('/generate_blockchain', methods=['POST'])
def generate_blockchain():
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()

    blockchain = []
    previous_hash = '0'
    for vehicle in vehicles:
        data = f"{vehicle[0]}-{vehicle[1]}-{vehicle[2]}"
        wallet = json.loads(vehicle[1])
        energy_token = calculate_energy_token(data)  # function to calculate energy tokens
        block = add_block(data, previous_hash, wallet, energy_token)
        blockchain.append(block)
        previous_hash = hashlib.sha256(data.encode()).hexdigest()

    return jsonify(blockchain)
@app.route('/verify_blockchain', methods=['POST'])
def verify_blockchain_route():
    blockchain = request.json
    result = verify_blockchain(blockchain)
    return jsonify(result)

@app.route('/generate_merkle_tree', methods=['POST'])
def generate_merkle_tree_route():
    data = request.json
    tree = generate_merkle_tree(data)
    return jsonify(tree)

@app.route('/verify_merkle_tree', methods=['POST'])
def verify_merkle_tree_route():
    data = request.json['data']
    root = request.json['root']
    result = verify_merkle_tree(data, root)
    return jsonify(result)

@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    cursor.execute("SELECT * FROM relations")
    relations = cursor.fetchall()

    G = nx.DiGraph()
    for relation in relations:
        G.add_edge(relation[0], relation[1])

    nx.draw(G, with_labels=True)
    plt.savefig('graph.png')

    return "Graph generated successfully"

@app.route('/create_wallet', methods=['POST'])
def create_wallet():
    vehicle_id = request.form['vehicle_id']
    vehicle_details = request.form['vehicle_details']

    wallet = generate_wallet()
    encrypted_data = encrypt_data(vehicle_details, wallet['public_key'])

    cursor.execute("INSERT INTO vehicles (VehicleID, Wallet, EncryptedData) VALUES (%s, %s, %s)", (vehicle_id, json.dumps(wallet), encrypted_data))
    db.commit()

    return "Wallet created successfully"

@app.route('/generate_blockchain', methods=['POST'])
def generate_blockchain():
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()

    blockchain = []
    previous_hash = '0'
    for vehicle in vehicles:
        data = f"{vehicle[0]}-{vehicle[1]}-{vehicle[2]}"
        wallet = json.loads(vehicle[1])
        energy_token = calculate_energy_token(data)  # function to calculate energy tokens
        state = "ACTIVE"  # initial state of the energy token
        block = add_block(data, previous_hash, wallet, energy_token, state)
        blockchain.append(block)
        previous_hash = hashlib.sha256(data.encode()).hexdigest()

    return jsonify(blockchain)


if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)
