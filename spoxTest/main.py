
import json
import flask
import httplib2
import os
import sys
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import uuid
from email.mime.text import MIMEText
import base64

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = str(uuid.uuid4())

SCOPES = 'https://www.googleapis.com/auth/gmail'
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = 'Gmail API'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
        http = credentials.authorize(httplib2.Http())
        drive_service = discovery.build('gmail', 'v1', http=http)
        files = drive_service.users().messages().list(userId='me').execute()
        return json.dumps(files)
        
@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/gmail.modify',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('index'))
        
        
def CreateMessage(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}
        
@app.route('/sendEmail')
def sendEmail():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
        message = CreateMessage('me', 'aluque94@gmail.com', 'TESTING SWAG', 'did it work?')
        try:
            message = (service.users().messages().send(userId='me', body=message).execute())
            print 'Message Id: %s' % message['id']
            return message
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
    


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
    
if __name__ == '__main__':
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = False
    app.run()
