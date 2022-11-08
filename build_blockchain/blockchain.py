import datetime
import hashlib
import json
from flask import Flask, jsonify


def hash_operation(proof, prev_proof):
    return hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()


class Blockchain:

    def __init__(self):
        self.chain = []
        self.create_block(proof=1, prev_hash='0')

    def create_block(self, proof, prev_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'prev_hash': prev_hash
        }

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


app = Flask(__name__)

block_chain = Blockchain()


@app.route('/mine_block', methods=['GET'])
def mine_block():
    prev_block = block_chain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = block_chain.pOw(prev_proof)
    prev_hash = block_chain.hash(prev_block)

    block = block_chain.create_block(proof, prev_hash)
    response = {
        'message': 'Succesfully mined!!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash']
    }
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': block_chain.chain,
        'chain_len': len(block_chain.chain)
    }
    return jsonify(response), 200


app.run(host='0.0.0.0', port=5001)
