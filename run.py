#!flask/bin/python
import os
from app import app

from flask import Flask
from flask_sslify import SSLify
from flask_cors import CORS

os.putenv('LANG', 'en_US.UTF-8')
os.putenv('LC_ALL', 'en_US.UTF-8')
#context = ('ssl/cert.pem','ssl/privkey.pem')
#sslify = SSLify(app)
#app.debug = False

#CORS(app, origins="*", allow_headers=[
#    "Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
#    supports_credentials=True)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


#Note: the secret_key should be generated randomly using some seed and be kept away from people and github public repos (In the future, for now it doesn't really matter :D)
app.secret_key = 'supersecretpasswordwewillneverdisclosecauseyougottagitgudlikeover9000tripleunderscore__'
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
	#app.run(host='127.0.0.1',port=port, use_reloader=True, ssl_context=('cert.pem','privkey.pem'))
    #app.run(host='0.0.0.0',port=port, use_reloader=True,threaded=True,ssl_context=context)
    app.run(host='0.0.0.0',port=port, use_reloader=True,threaded=True)

print ">> Run File Loaded."