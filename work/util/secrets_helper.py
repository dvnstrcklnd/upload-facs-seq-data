import os
import json

def get_secrets():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'secrets.json')

    with open(filename) as f:
        secrets = json.load(f)
        
    return secrets

def save_secrets(new_secrets):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'secrets.json')

    with open(filename, 'w') as f:
        j = json.dumps(new_secrets, indent=4)
        f.writelines(j)