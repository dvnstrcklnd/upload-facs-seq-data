import pydent
from pydent import AqSession, __version__
from util.secrets_helper import get_secrets

prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)

def create_session(aq_instance):
    """
    Create a session using credentials in secrets.json.

    :param aq_instance: the instance of Aquarium to use
        Corresponds to a key in the secrets.json file
    :type aq_instance: str
    :return: new Session
    """
    secrets = get_secrets()
    credentials = secrets[aq_instance]
    session = AqSession(
        credentials["login"],
        credentials["password"],
        credentials["aquarium_url"]
    )

    msg = "Connected to Aquarium at {} using pydent version {}"
    print(msg.format(session.url, str(__version__)))

    me = session.User.where({'login': credentials['login']})[0]
    print('Logged in as {}\n'.format(me.name))

    return session
    
def list_methods(obj):
    print("Methods available in {}".format(obj.__class__.__name__))
    for d in dir(obj):
        if not d.startswith('_'):
            print(d)
