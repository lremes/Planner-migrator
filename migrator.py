import requests
import json

class Migrator:
    oauth = None
    plans = None
    base_url = None

    def __init__(self, oauth):
        self.oauth = oauth
        
    def get(self, url, token):
        if self.oauth == None:
            raise Exception('OAUTH object not set')
        full_url = self.oauth.base_url + url
        print full_url
        resp = requests.get(full_url, 
                  #data=json.dumps(p),
                  headers={ 
                      'Accept': 'application/json',
                      'Authorization': 'Bearer ' + token
                })
        print resp
        print json.dumps(resp.json(), indent=4)
        return resp.json()
    
    def update_task_details(self, task, data, token):
        if self.oauth == None:
            raise Exception('OAUTH object not set')
        full_url = self.oauth.base_url + "planner/tasks/%s/details" % (task['id'])
        print full_url
        
        resp = requests.patch(full_url, 
                #data=json.dumps(p),
                headers={ 
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + token,
                    'If-Match': task['Etag']
                },
                data=data
                )
        print resp
        print json.dumps(resp.json(), indent=4)
        return resp.json()
    
    def create_plan(self, owner, title, token):
        full_url = self.oauth.base_url + "planner/plans"
        print full_url
        
        data = {
            "owner": owner,
            "title": title
        }
        print data
        resp = requests.post(full_url, 
                #data=json.dumps(p),
                headers={ 
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                data=json.dumps(data)
                )
        print resp
        print json.dumps(resp.json(), indent=4)
        return resp.json()
    
    def create_bucket(self, name, planId, orderHint, token):
        full_url = self.oauth.base_url + "planner/buckets"
        print full_url
        
        data = {
            "name": name,
            "planId": planId,
            "orderHint": orderHint
        }
        
        resp = requests.post(full_url, 
                #data=json.dumps(p),
                headers={ 
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                data=json.dumps(data)
                )
        print resp
        print json.dumps(resp.json(), indent=4)
        return resp.json()
    
    def getPlanId(self, idx):
        #print "PLAN ["+ self.plans[idx].get('id') +"]"
        return self.plans[idx].get('id')