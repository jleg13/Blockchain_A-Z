import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain


def hash_operation(proof, prev_proof):
    return hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()


class Blockchain:

    def __init__(self):
        self.chain = []
        self.mempool = []
        self.create_block(proof=1, prev_hash='0')
        self.nodes = set()

    def create_block(self, proof, prev_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'prev_hash': prev_hash,
            'transactions': self.mempool
        }
        self.mempool = []
        self.chain.append(block)
        return block

    def get_prev_block(self):
        return self.chain[-1]

    def pOw(self, prev_proof):

        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash = hash_operation(new_proof, prev_proof)
            if hash[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]
            if block['prev_hash'] != self.hash(prev_block):
                return False

            hash = hash_operation(block['proof'], prev_block['proof'])
            if hash[:4] != '0000':
                return False

            prev_block = block
            block_index += 1

        return True

    def add_transaction(self, sender, receiver, amount):
        self.mempool.append(
            {
                'sender': sender,
                'receiver': receiver,
                'amount': amount
            }
        )
        prev_block = self.get_prev_block()
        return prev_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['chain_len']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

block_chain = Blockchain()


# Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    prev_block = block_chain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = block_chain.pOw(prev_proof)
    prev_hash = block_chain.hash(prev_block)
    block_chain.add_transaction(sender=node_address, receiver='Aide', amount=1)
    block = block_chain.create_block(proof, prev_hash)
    response = {
        'message': 'Succesfully mined!!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': block_chain.chain,
        'chain_len': len(block_chain.chain)
    }
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = block_chain.add_transaction(
        json['sender'], json['receiver'], json['amount']
    )
    response = {
        'message': f'This transaction will be added to Block {index}'
    }
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain


# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        block_chain.add_node(node)
    response = {
        'message': 'Nodes are now connected. JoshCoin Blockchain nodes:',
        'total_nodes': list(block_chain.nodes)
    }
    return jsonify(response), 201


# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = block_chain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'The nodes where replaced by the longest chain',
            'new_chain': block_chain.chain
        }
    else:
        response = {
            'message': 'All good. The chain is the largest one',
            'actual_chain': block_chain.chain
        }
    return jsonify(response), 200

# Running the app


app.run(host='0.0.0.0', port=5003)
