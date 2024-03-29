import os         # For Windows stuff
import json       # json library
import requests   # See: http://docs.python-requests.org/en/master/
import pprint
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO) # Don't want this debug level to cloud ours
pp = pprint.PrettyPrinter(width=120)

REQUEST_TIMEOUT = 10                    # Request timeout in seconds

## Utility class to make the main IMatchAPI class a little less complex
class IMatchUtility:
    def file_id_list(self, fileids):
        """ Turn a list of file id numbers into a string for passing to a function """
        return ",".join(map(str, fileids))
                
    def getID(self, x):
        """ Pull the file id from a {} record where ID is a field"""
        return x['id']

    def listIDs(self, x):
        """ Given a list of items where one record in the field is ID, return the list of IDs"""
        return list(map(self.getID, x))

class IMatchAPI:

    def __init__(self, hostPort = 50519):
        self.auth_token = ''                     # This stores the IMWS authentication token after authenticate() has been called
        self.hostPort = hostPort                 

        # Not validting this in any way
        self.hostURL = f"http://127.0.0.1:{self.hostPort}"
        self.utility = IMatchUtility()

        self.authenticate()

    def authenticate(self):
        """ Authenticate against IMWS and set the auth_token variable
            to the returned authentication token. We need this for all other endpoints. """

        try:
            logging.info(f"Attempting connection to IMatch on port {self.hostPort}")
            req = requests.post(self.hostURL + '/v1/authenticate', params={
                'id': os.getlogin(),
                'password': '',
                'appid': ''},
                timeout=REQUEST_TIMEOUT)

            response = json.loads(req.text)

            # If we're OK, store the auth_token in the global variable
            if req.status_code == requests.codes.ok:
                self.auth_token = response["auth_token"]
            else:
                # Raise the exception matching the HTTP status code
                req.raise_for_status()

            logging.info(f"Authenticated to {self.hostURL}")
            return

        except requests.exceptions.ConnectionError as ce:
            logging.info(f"Unable to connect to IMatch on port {self.hostPort}. Please check IMatch is running and the port is correct.\n\nThe full error was {ce}")
            raise SystemExit
        except requests.exceptions.RequestException as re:
            print(re)
            raise SystemExit
        except Exception as ex:
            print(ex)


    def getIMatch(self, endpoint, params):
        """ Generic get function to IMatch. Other functions call this so there is no need for them to repeat
         the main control loop. Ensures the auth_token is not missed as a parameter. """

        params['auth_token'] = self.auth_token

        # Easy to miss the leading / so add it as a courtesy
        if endpoint[:1] != "/":
            endpoint = "/" + endpoint
        
        try:
            req = requests.get(self.hostURL + endpoint, params, timeout=REQUEST_TIMEOUT)
          
            response = json.loads(req.text)

            if req.status_code == requests.codes.ok:
                return response
            else:
                req.raise_for_status()

            return

        except requests.exceptions.RequestException as re:
            print(re)
            print(response)

        except Exception as ex:
            print(ex)

    def postIMatch(self, endpoint, params):
        """ Generic post function to IMatch. Other functions call this so there is no need for them to repeat
         the main control loop. Ensures the auth_token is not missed as a parameter. """

        params['auth_token'] = self.auth_token

        # Easy to miss the leading / so add it as a courtesy
        if endpoint[:1] != "/":
            endpoint = "/" + endpoint
        
        try:
            req = requests.post(self.hostURL + endpoint, params, timeout=REQUEST_TIMEOUT)

            response = json.loads(req.text)

            if req.status_code == requests.codes.ok:
                return response
            else:
                req.raise_for_status()
            return

        except requests.exceptions.RequestException as re:
            print(re)
            print(response)

        except Exception as ex:
            print(ex)

    def getAppVar(self, variable):
        """ Retrieve the named application variable from IMatch (Edit|Preferences|Vairables)"""
        params = {}
        params['name'] = variable

        response = self.getIMatch( '/v1/imatch/appvar', params)

        return response['value']


    def getAttributes(self, set, filelist, params={}):
        """ Return all attributes for a list of file ids. filelist is an array. """

        params['set'] = set
        params['id'] = self.utility.file_id_list(filelist)

        logging.debug(f"Retreiving attributes for {params['id']}")
        response = self.getIMatch( '/v1/attributes', params)

        # Strip away the wrapping from the result
        results = []
        for attributes in response['result']:
            logging.debug(attributes)
            results.append(attributes)
        logging.debug(f"{len(results)} attribute instances retrieved.")
        return results


    def getCategoryFiles(self, path):
        """ Return the requested information all files in the specified category """

        params={}
        params['path'] = path
        params['fields'] = 'files'

        logging.debug(f'Retrieving list of files in the {path} category.')
        response = self.getIMatch( '/v1/categories', params)
        if len(response['categories']) == 0:
            logging.debug("0 files found.")
            return []
        else:
            # Get straight to the data if present
            logging.debug(f"{len(response['categories'][0]['files'])} files found.")
            return response['categories'][0]['files']


    def getFileCategories(self, filelist, params={}):
        """ Return the categories for the list of files """

        params['id'] = self.utility.file_id_list(filelist)

        response = self.getIMatch( '/v1/files/categories', params)
        results = {}
        for file in response['files']:
            logging.debug(file)
            results[file['id']] = file['categories']
        logging.debug(f"{len(results)} images with categories.")
        return results


    def getFileInfo(self, filelist, params={}):
        """ Return details list of file ids """

        params['id'] = self.utility.file_id_list(filelist)

        response = self.getIMatch( '/v1/files', params)

        return response['files']
    

    def getMaster(self, id):
        """ Return the number of the master if one exists """

        params = {}
        params["id"] = id
        params["type"] = "masters"

        response = self.getIMatch( '/v1/files/relations', params)
        
        return response['files'][0]['masters'][0]['files'][0]['id']


    def files_for_selection(self, params={'fields': 'id,filename'}):
        """ Return the requested information all selected files in the active file window. """

        params['idlist'] = '@imatch.filewindow.active.selection'
            
        response = self.getIMatch("/v1/files", params)
        
        return response['files']
 

    def list_file_names(self):
        """ Print the id and name of all selected files in the active file window. """

        try:
            req = requests.get(self.hostURL + '/v1/files', params={
            'auth_token': self.token(),
            'idlist': '@imatch.filewindow.active.selection',
            'fields': 'id,filename'
            }, timeout=REQUEST_TIMEOUT)

            response = json.loads(req.text)

            if req.status_code == requests.codes.ok:

                print(response['files'])

                for f in response['files']:
                    print(f['id'],' ',f['fileName'])

            else:
                req.raise_for_status()

            return

        except requests.exceptions.RequestException as re:
            print(re)
            print(response)

        except Exception as ex:
            print(ex)

    def setAttributes(self, set, filelist, params={}, data={}):
        """ Set attributes for files. Assumes attributes only exist once. Will either add or update as needed.
         (modification required if multiple instances of attribute sets are to be managed) """

        for id in filelist:
            params['set'] = set
            params['id'] = f"{id}"

            # Can neither assume no attribute instance, or an existing attribute instance. 
            # Check first

            if len(self.getAttributes(set, [id])) == 0:
                # No existing attributes, do an add
                op = 'add'
                logging.debug("Adding attribute row.")
            else:
                op = 'update'
                logging.debug("Updating existing attribute row.")

            tasks = [{
                'op' : op,
                'instanceid': [1],
                'data' : data
            }]

            params['tasks'] = json.dumps(tasks)  # Necessary to stringify the tasks array before sending

            logging.debug(f"Sending instructions : {params}")

            response = self.postIMatch( '/v1/attributes', params)

            if response['result'] == "ok":
                logging.debug("Success")
                return
            else:
                logging.error("There was an error updating attributes.")
                pp.pprint(response)
                raise SystemExit
