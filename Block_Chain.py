# Description: This file contains the code for the blockchain implementation
import random

from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib.pyplot as plt
from wallet import *
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import mysql.connector
from utils import *


import json
import os
app = Flask(__name__)
# Define the path to the JSON file
VEHICLES_FILE = 'vehicles.json'
RELATIONS_FILE = 'relations.json'
def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    else:
        return []

def save_data(data, file):
    with open(file, 'w') as f:
        json.dump(data, f)

def calculate_energy_token(data):
    # Implementation depends on your specific requirements
    return random.randint(1, 100)

def add_block(data, previous_hash, wallet, energy_token, state):
    block = {
        'data': data,
        'previous_hash': previous_hash,
        'wallet': wallet,
        'energy_token': {
            'token': energy_token,
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
    vehicles = load_data(VEHICLES_FILE)

    for vehicle in vehicles:
        wallet = vehicle['Wallet']
        for transaction in wallet['transactions']:
            if transaction['energy_token']['state'] == 'ACTIVE':
                # Check if the token should be changed to 'PASSIVE'
                if should_change_to_passive(transaction):  # You need to implement this function
                    transaction['energy_token']['state'] = 'PASSIVE'
                    save_data(vehicles, VEHICLES_FILE)

def add_block_to_chain(blockchain, data, wallet):
    energy_token = calculate_energy_token(data)
    state = "ACTIVE"
    previous_hash = hashlib.sha256(data.encode()).hexdigest() if blockchain else '0'
    block = add_block(data, previous_hash, wallet, energy_token, state)
    blockchain.append(block)
    return blockchain

scheduler = BackgroundScheduler()
scheduler.add_job(check_token_state, 'interval', minutes=1)
scheduler.start()
@app.route('/view_wallet', methods=['GET', 'POST'])
def view_wallet():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        vehicles = load_data(VEHICLES_FILE)
        for vehicle in vehicles:
            if vehicle['Wallet']['username'] == username and vehicle['Wallet']['password'] == password:
                wallet_info = {
                    'username': vehicle['Wallet']['username'],
                    'balance': vehicle['Wallet']['balance'],
                    'transactions': vehicle['Wallet']['transactions']
                }
                return jsonify(wallet_info)
        return "Invalid credentials"
    else:
        return render_template('view_wallet.html')
@app.route('/buy_tokens', methods=['GET', 'POST'])
def buy_tokens():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        num_tokens = int(request.form['num_tokens'])

        vehicles = load_data(VEHICLES_FILE)
        for vehicle in vehicles:
            if vehicle['Wallet']['username'] == username and vehicle['Wallet']['password'] == password:
                vehicle['Wallet']['balance'] += num_tokens
                transaction = {
                    'type': 'buy',
                    'amount': num_tokens,
                    'timestamp': time.time()  # You need to import the time module
                }
                vehicle['Wallet'] = add_transaction(vehicle['Wallet'], transaction)

                # Add block to blockchain
                blockchain = load_data('blockchain.json')
                data = f"{vehicle['VehicleID']}-{vehicle['Wallet']}-{vehicle['EncryptedData']}"
                blockchain = add_block_to_chain(blockchain, data, vehicle['Wallet'])
                save_data(blockchain, 'blockchain.json')

                save_data(vehicles, VEHICLES_FILE)
                return "Tokens bought successfully"
    else:
        return render_template('buy_tokens.html')



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_blockchain', methods=['GET', 'POST'])
def generate_blockchain():
    if request.method == 'POST':
        vehicles = load_data(VEHICLES_FILE)

        blockchain = []
        previous_hash = '0'
        for vehicle in vehicles:
            data = f"{vehicle['VehicleID']}-{vehicle['Wallet']}-{vehicle['EncryptedData']}"
            wallet = vehicle['Wallet']
            energy_token = calculate_energy_token(data)
            state = "ACTIVE"
            block = add_block(data, previous_hash, wallet, energy_token, state)
            blockchain.append(block)
            previous_hash = hashlib.sha256(data.encode()).hexdigest()

        return jsonify(blockchain)
    else:
        return render_template('generate_blockchain.html')
@app.route('/verify_blockchain', methods=['GET', 'POST'])
def verify_blockchain_route():
    if request.method == 'POST':
        blockchain = request.json
        result = verify_blockchain(blockchain)
        return jsonify(result)
    else:
        blockchain = load_data('blockchain.json')
        result = verify_blockchain(blockchain)
        return jsonify(result)


@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        vehicle_details = request.form['vehicle_details']
        username = request.form['username']
        password = request.form['password']

        wallet = generate_wallet(username, password)
        encrypted_data = encrypt_data(vehicle_details, wallet['public_key'])

        vehicles = load_data(VEHICLES_FILE)
        vehicles.append({
            'VehicleID': vehicle_id,
            'Wallet': wallet,
            'EncryptedData': encrypted_data
        })
        save_data(vehicles, VEHICLES_FILE)

        return "Wallet created successfully"
    else:
        return render_template('create_wallet.html')

@app.route('/update_records', methods=['GET', 'POST'])
def update_records():
    if request.method == 'POST':
        group_id = request.form['group_id']
        vehicle_id = request.form['vehicle_id']
        vehicle_details = request.form['vehicle_details']

        private_key, public_key = generate_key_pair()
        public_key_hex = serialize_public_key(public_key)

        encrypted_data = encrypt_data(vehicle_details, public_key)

        vehicles = load_data(VEHICLES_FILE)
        for vehicle in vehicles:
            if vehicle['VehicleID'] == vehicle_id:
                vehicle['GroupID'] = group_id
                vehicle['PublicKey'] = public_key_hex
                vehicle['EncryptedData'] = encrypted_data
                break
        else:
            vehicles.append({
                'GroupID': group_id,
                'VehicleID': vehicle_id,
                'PublicKey': public_key_hex,
                'EncryptedData': encrypted_data
            })
        save_data(vehicles, VEHICLES_FILE)

        return "Data added successfully"
    else:
        return render_template('update_records.html')

@app.route('/add_group_vehicle_relation', methods=['POST'])
def add_group_vehicle_relation():
    group_id = request.form['group_id']
    vehicle_id = request.form['vehicle_id']

    relations = load_data(RELATIONS_FILE)

    existing_relation = next((relation for relation in relations if relation['GroupID'] == group_id and relation['VehicleID'] == vehicle_id), None)

    if existing_relation:
        return "Relation already exists"

    vehicles = load_data(VEHICLES_FILE)

    vehicle_data = next((vehicle for vehicle in vehicles if vehicle['VehicleID'] == vehicle_id), None)

    if not vehicle_data:
        return "Invalid vehicle"

    relations.append({
        'GroupID': group_id,
        'VehicleID': vehicle_id
    })
    save_data(relations, RELATIONS_FILE)

    return "Relation added successfully"

#
# @app.route('/generate_merkle_tree', methods=['POST'])
# def generate_merkle_tree_route():
#     data = request.json
#     tree = generate_merkle_tree(data)
#     return jsonify(tree)
#
# @app.route('/verify_merkle_tree', methods=['POST'])
# def verify_merkle_tree_route():
#     data = request.json['data']
#     root = request.json['root']
#     result = verify_merkle_tree(data, root)
#     return jsonify(result)


@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    relations = load_data(RELATIONS_FILE)

    G = nx.DiGraph()
    for relation in relations:
        G.add_edge(relation['GroupID'], relation['VehicleID'])

    nx.draw(G, with_labels=True)
    plt.savefig('graph.png')

    return "Graph generated successfully"

@app.route('/view_blockchain', methods=['GET'])
def view_blockchain():
    blockchain = load_data('blockchain.json')
    return render_template('view_blockchain.html', blockchain=blockchain)


if __name__ == '__main__':
    # Load existing blockchain or create a new one if it doesn't exist
    if os.path.exists('blockchain.json'):
        with open('blockchain.json', 'r') as f:
            blockchain = json.load(f)
    else:
        blockchain = []

    # Only add blocks for vehicles that are not already in the blockchain
    vehicles = load_data(VEHICLES_FILE)
    for vehicle in vehicles:
        data = f"{vehicle['VehicleID']}-{vehicle['Wallet']}-{vehicle['EncryptedData']}"
        if not any(block['data'] == data for block in blockchain):
            blockchain = add_block_to_chain(blockchain, data, vehicle['Wallet'])

    save_data(blockchain, 'blockchain.json')
    app.run(debug=True)