import os
from agavepy.agave import Agave
from util.secrets_helper import get_secrets, save_secrets

def create_client():
    """
    Create a session using credentials in secrets.json.

    :return: new Agave client
    """
    secrets = get_secrets()
    credentials = secrets['agave']
    
    if not (credentials.get('api_key') and credentials.get('api_secret')):
        print("Generating new api_key and api_secret and saving to secrets.json")
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
               api_secret=credentials['api_secret'], 
               client_name=credentials['client_name'],
               tenant_id="sd2e")

    me = ag.profiles.get()
    print('Client created as {} {}'.format(me['first_name'], me['last_name']))
    
    return ag

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")

class BaseSpaceClient():
    
    def __init__(self):
        self.agave_client = create_client()
        self.restore()
        self.basespace_project = None
        self.tacc_service = None
        self.aq_plan = None
        
    def set_basespace_project(self, name):
        self.basespace_project = name
        
    def set_tacc_service(self, service):
        self.tacc_service = service
        
    def set_aq_plan(self, plan):
        self.aq_plan = plan

    def plan_path(self):
        if self.tacc_service and self.aq_plan:
            tacc_path = os.path.join('/home/jupyter', self.tacc_service.replace('.', '/').replace('data-', ''))
            plan_path = os.path.join(tacc_path, self.aq_plan)
            return plan_path
        
    def project_dir(self):
        return 'Projects/%s/Samples/' % self.basespace_project

    def system_id(self):
        return 'data-sd2e-basespace-biofab'
    
    def list_files(self, limit=250, offset=0, ignore_dotfiles=True, sort=True):
        all_files = []

        while True:
            batch = self.agave_client.files.list(
                filePath=self.project_dir(), 
                systemId=self.system_id(), 
                limit=limit, offset=offset
            )
            more_files = len(batch) == limit

            if ignore_dotfiles:
                batch = [item for item in batch if not item['name'].startswith(".")]

            all_files.extend(batch)
            offset += limit

            if not more_files:
                break
                
        if sort:
            all_files.sort(key=lambda x: x['name'])

        return all_files
    
    def restore(self):
        self.agave_client.restore()
    