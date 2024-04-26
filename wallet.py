from .utils import *
from flask import request, jsonify
import mysql.connector

def generate_wallet():
    private_key, public_key = generate_key_pair()
    private_key_hex = serialize_private_key(private_key)
    public_key_hex = serialize_public_key(public_key)
    wallet = {
        'private_key': private_key_hex,
        'public_key': public_key_hex,
        'balance': 0,
        'transactions': []
    }
    return wallet

def add_transaction(wallet, transaction):
    wallet['transactions'].append(transaction)
    return wallet

