from agavepy.agave import Agave
from util.secrets_helper import get_secrets, save_secrets

def create_client():
    """
    Create a session using credentials in secrets.json.

    :return: new Agave client
    """
    secrets = get_secrets()
    credentials = secrets['agave']
    
    if not credentials.get('api_key') or credentials.get('api_secret'):
        ag = Agave(api_server=credentials['api_server'],
                   username=credentials['username'],
                   password=credentials['password'])
        new_secrets = ag.clients_create()
        credentials.update(new_secrets)
        save_secrets(secrets)
        
    ag = Agave(api_server=credentials['api_server'],
               username=credentials['username'],
               password=credentials['password'],
               api_key=credentials['api_key'],
               api_secret=credentials['api_secret'])
    
    return ag
    
    