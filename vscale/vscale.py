#!/usr/bin/python


import requests
import json as json_module

API_ENDPOINT = 'https://api.vscale.io'

class DoError(RuntimeError):
    pass

class apimanager(object):

    def __init__(self, api_key, api_version=1):
        self.api_endpoint = API_ENDPOINT
        self.api_key = api_key
        self.api_version = int(api_version)
        self.api_endpoint += '/v1'

    def scalets_list(self):
        json = self.request('/scalets')
        return json

    def scalet_info(self, scalet_id):
        json = self.request('/scalets/%s' % scalet_id)
        return json

    def scalet_start(self, scalet_id):
        json = self.request('/scalets/%s/start' % scalet_id, method='PATCH')
        return json

    def scalet_stop(self, scalet_id):
        json = self.request('/scalets/%s/stop' % scalet_id, method='PATCH')
        return json

    def scalet_restart(self, scalet_id):
        json = self.request('/scalets/%s/restart' % scalet_id, method='PATCH')
        return json

    def scalet_upgrade(self, scalet_id, plan):
        params = {
            'rplan': str(plan)
        }
        json = self.request('/scalets/%s/upgrade' % scalet_id, params, method='POST')
        return json

    def scalet_create(self, name, plan, image, location, password=None, keys=None, autostart=True):
        params = {
            'name': str(name),
            'password': str(password),
            'rplan': str(plan),
            'make_from': str(image),
            'do_start': bool(autostart),
            'location': str(location),
        }
        if keys:
            if type(keys) == list:
                params['keys'] = keys

        json = self.request('/scalets', params, method='POST')

        return json

    def scalet_delete(self, scalet_id):
        json = self.request('/scalets/%s' % scalet_id, method='DELETE')
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
    # state = module.params['state']
    api_key = module.params['api_key'] or os.environ['API_KEY']
    api = apimanager(api_key)

    vmlist = api.scalets_list()
    if len(vmlist) == 0:
        # no vms, create new
        if module.params['state'] != 'absent' and module.params['state'] == "started":
            # name, plan, image, location, password=None, keys=None, autostart=True
            res = api.scalet_create(module.params['name'], module.params['plan'], module.params['image'], module.params['location'], module.params['password'], module.params['key_ids'])
            # print('Result OF CREATION {}'.format(res))
            module.exit_json(msg=res)
        elif module.params['state'] == 'stopped':
            print('VM params {}'.format(module.params))
            res = api.scalet_create(module.params['name'], module.params['plan'], module.params['image'], module.params['location'], module.params['password'], module.params['key_ids'], False)
            # print('Result OF CREATION {}'.format(res))
            module.exit_json(msg=res)
        else:
            module.exit_json(msg="Nothing to delete")
    else:
        print('VMS: {}'.format(vmlist))
        print('VM params {}'.format(module.params))
        # module.exit_json(changed=True, msg=res)
        module.fail_json(msg="Error")

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, type='str'),
            password = dict(type='str'),
            plan = dict(required=True, type='str'),
            image = dict(required=True, type='str'),
            location = dict(required=True, type='str'),
            key_ids = dict(type='str'),
            state = dict(choices=['stopped', 'absent', 'started', 'restarted'], default='started'),
            api_key = dict(aliases=['API_KEY'], no_log=True),
        ),
        required_one_of = (
            ['password', 'pub_key'],
        ),
    )
    std(module)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()