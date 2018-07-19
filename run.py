#!flask/bin/python
import os
from app import app

os.putenv('LANG', 'en_US.UTF-8')
os.putenv('LC_ALL', 'en_US.UTF-8')

app.debug = True
app.secret_key = 'supersecretpasswordwewillneverdisclosecauseyougottagitgudlikeover9000tripleunderscore__'
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0',port=port, use_reloader=True)

#Note: the secret_key should be generated randomly using some seed and be kept away from people and github public repos (In the future, for now it doesn't really matter :D)

print "run DONE!"