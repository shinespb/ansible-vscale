#!/usr/bin/python


import requests
import json as json_module

API_ENDPOINT = 'https://api.vscale.io'

class apimanager(object):

    def __init__(self, api_key, api_version=1):
        self.api_endpoint = API_ENDPOINT
        self.api_key = api_key
        self.api_version = int(api_version)
        self.api_endpoint += '/v1'

    # get list of ssh keys
    def sshkey_list(self):
        json = self.request('/sshkeys')
        return json

    def sshkey_add(self, keyname, pubkey):
        params = {"name": keyname, "key": pubkey}
        json = self.request('/sshkeys', params, method='POST')
        return json

    def sshkey_delete(self, key_id):
        json = self.request('/sshkeys/%s' % key_id, method='DELETE')
        return json

    def request(self, path, params={}, method='GET'):
        headers={}
        if not path.startswith('/'):
            path = '/'+path
        url = self.api_endpoint+path

        headers['X-Token'] = self.api_key
        resp = self.request_v1(url, headers, params, method=method)

        return resp

    def request_v1(self, url, headers={}, params={}, method='GET'):
        headers['Content-Type'] = 'application/json'
        try:
            if method == 'POST':
                resp = requests.post(url, data=json_module.dumps(params), headers=headers, timeout=60)
                # print('Headers: {}. Params: {}'.format(headers, json_module.dumps(params)))
                json = resp.json()
            elif method == 'DELETE':
                resp = requests.delete(url, headers=headers, timeout=60)
                json = {'status': resp.status_code}
            elif method == 'GET':
                resp = requests.get(url, headers=headers, params=params, timeout=60)
                json = resp.json()
            else:
                raise DoError('Unsupported method %s' % method)

        except ValueError:
            raise ValueError("The API server doesn't respond with a valid json")
        except requests.RequestException as e:
            raise RuntimeError(e)

        if resp.status_code != requests.codes.ok:
            if resp.headers:
                if 'vscale-error-message' in resp.headers:
                    raise DoError(resp.headers['vscale-error-message'])
            resp.raise_for_status()

        return json

def std(module):
    state = module.params['state']
    api_key = module.params['api_key'] or os.environ['API_KEY']
    api = apimanager(api_key)

    def listkeys(k):
        mod = module.params[k]
        # print('parameters: {}'.format(mod))
        return mod

    def changekey(keyid, name, pub_key):
        # print('Deleting key {}'.format(keyid))
        api.sshkey_delete(keyid)
        # print('Adding key {}: {} with pub: {}'.format(keyid, name, pub_key))
        api.sshkey_add(name, pub_key)
                
    name = listkeys('name')
    pub_key = listkeys('pub_key')
    keylist = api.sshkey_list()

    nokey = True
    for key in keylist:
        if str(key['name']) == str(name):
            nokey = False
            if key['key'] == pub_key:
                module.exit_json(msg="Key equals")
            else:
                changekey(key['id'], key['name'], pub_key)
                module.exit_json(changed=True, msg=key['name'])


    if nokey:
        res = api.sshkey_add(name, pub_key)
        module.exit_json(changed=True, msg=res)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(type='str'),
            pub_key = dict(type='str'),
            state = dict(choices=['present', 'absent'], default='present'),
            api_key = dict(aliases=['API_KEY'], no_log=True),
            id = dict(aliases=['scalet_id'], type='int'),
        ),
        required_one_of = (
            ['id', 'name'],
        ),
    )
    std(module)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()