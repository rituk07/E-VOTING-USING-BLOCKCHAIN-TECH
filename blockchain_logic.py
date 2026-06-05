import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []
        # Create Genesis block
        genesis_block = {
            'index': 1,
            'timestamp': time(),
            'vote': "Genesis Block",
            'previous_hash': "0"
        }
        genesis_block['hash'] = self.hash_block(genesis_block)
        self.chain.append(genesis_block)

    def add_vote(self, voter_id, candidate):
        previous_hash = self.chain[-1]['hash'] if self.chain else "0"
        vote_data = {
            'voter_id': voter_id,
            'candidate': candidate,
            'timestamp': time()
        }
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'vote': vote_data,
            'previous_hash': previous_hash
        }
        block['hash'] = self.hash_block(block)
        self.chain.append(block)
        return block

    def hash_block(self, block):
        # Sort keys to ensure consistent hashes
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_chain(self):
        return self.chain

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check if block's own hash is valid
            temp_block = current.copy()
            actual_hash = temp_block.pop('hash')
            if actual_hash != self.hash_block(temp_block):
                return False
                
            # Check if it links correctly to previous block
            if current['previous_hash'] != previous['hash']:
                return False
        return True