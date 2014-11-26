import json
import msgpack
import os
import random
import string


def id_generator(size):
    """Return an alphanumeric string of size"""

    return ''.join(random.choice(string.ascii_letters +
        string.digits + '-_') for _ in range(size))


def msgpacked_payload(list_id_path):
    """Return msgpacked content"""

    data = dict()
    for _id, _path in list_id_path:
        with open(_path, 'r') as fb:
            data[_id] = fb.read()
    packed_data = msgpack.packb(data)
    return packed_data


def auth_request(api_user, api_key):
    """Get request body for Identity"""

    body_dict = {'auth':
        {'RAX-KSKEY:apiKeyCredentials':
            {'username': api_user, 'apiKey': api_key}}}
    return json.dumps(body_dict)


def auth_token(payload):
    """Return identity token"""

    return payload['access']['token']['id']


def project_id(payload):
    """Return project id"""

    tenantid = None
    for entry in payload['access']['serviceCatalog']:
        if entry['type'] == 'object-store':
            endpoints = entry['endpoints']
            for endpoint in endpoints:
                tenantid = endpoint['tenantId']
            break
    return tenantid


def deuce_assign_block(list_blocks, size):
    """Get request body to assign blocks to a file"""

    blocks = []
    offset = 0
    for block in list_blocks:
        blocks.append([block[0], offset])
        offset += size
    return json.dumps(blocks)


def remove_temp_files(list_id_path):
    """Remove temporary files"""

    for _id, _path in list_id_path:
        os.unlink(_path)
