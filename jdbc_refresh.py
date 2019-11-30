import json
from Crypto.Cipher import AES
from xml.dom import minidom
import sys
import os

userID = os.getlogin()
pwdPath = r"C:/Users/" + userID + r"/AppData/Roaming/DBeaverData/workspace6/General/.dbeaver/credentials-config.json"
dbPath = r'C:/Users/' + userID + r'/AppData/Roaming/DBeaverData/workspace6/General/.dbeaver/data-sources.json'
driverPath = r'C:/Users/' + userID + r'/AppData/Roaming/DBeaverData/workspace6/.metadata/.plugins/org.jkiss.dbeaver.core/drivers.xml'

# default setting
resultFile = 'jdbc_connections.json'
getCredential = True

# get setting from arguments
args = sys.argv
if len(args) == 0:
    pass
elif len(args) == 1:
    if '-sc' == args[0]:
        getCredential = False
    else:
        resultFile = args[0]
elif len(args) >= 2:
    if '-sc' in args:
        getCredential = False
        args.remove('-sc')
    resultFile = args[0]

if getCredential:
    PASSWORD_DECRYPTION_KEY = bytes([186, 187, 74, 159, 119, 74, 184, 83, 201, 108, 45, 101, 61, 254, 84, 74])

    with open(pwdPath, 'rb') as pwd_file:
        data = pwd_file.read()
    decryptor = AES.new(PASSWORD_DECRYPTION_KEY, AES.MODE_CBC, data[:16])
    output = decryptor.decrypt(data[16:])#[:-1]
    output = output[:output.rfind(b'}') + 1]
    pwds = json.loads(output)
mydoc = minidom.parse(driverPath)
items = mydoc.getElementsByTagName('driver')
drivers = dict()
for item in items:
    if 'class' in item.attributes:
        drivers[item.attributes['id'].value] = item.attributes['class'].value

connections = {}
with open(dbPath, 'r') as db_file:
    dbs = json.load(db_file)

for conn, prop in dbs['connections'].items():
    if prop['provider'] == 'sqlserver':
        url = 'jdbc:sqlserver://' + \
                prop['configuration']['host'] + \
                ':' + \
                prop['configuration']['port'] + \
                ';databaseName=' + \
                prop['configuration'].get('database', 'master')
    else:
        url = prop['configuration']['url']
        
    new_conn = connections.get(prop['provider'], [])
    new_conn.append({"name":prop['name']
                    , "url":url
                    , "options":{"driver":drivers[prop['driver']]}
                   })
    connections[prop['provider']] = new_conn
    if getCredential:
        credential = pwds[conn]['#connection']
        connections[prop['provider']][-1]['options']['user'] = credential['user']
        connections[prop['provider']][-1]['options']['password'] = credential['password']

    if prop['configuration'].get('properties', '') != '':
        for p, v in prop['configuration']['properties'].items():
            connections[prop['provider']][-1]['options'][p] = v
    #     if prop['configuration']['properties'].get('oracle.jdbc.timezoneAsRegion', 'true') == 'false':
    #         connections[prop['provider']][-1]['options']['oracle.jdbc.timezoneAsRegion'] = 'false'
with open(resultFile, 'w') as result_json:
    json.dump({'connections':connections}, result_json, indent=4, sort_keys=True)

# print(json.dumps({'connections':connections}, indent=4, sort_keys=True))