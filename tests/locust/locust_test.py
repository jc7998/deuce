from locust import HttpLocust, TaskSet, task, events

from logging.handlers import RotatingFileHandler

import config
import gen_dataset
import logging
import random
import threading
import time
import util

# load cfg
cfg = config.LocustConfig()
VNAME_SIZE = cfg.vaultname_size
NUM_BLOCKS = cfg.num_blocks
B_SIZE = cfg.block_size
RATIO = cfg.dedup_ratio
API_KEY = cfg.api_key
API_USER = cfg.api_user
USE_AUTH = cfg.use_auth
AUTH_URL = cfg.auth_url

# dedup ratio and common dataset
NUM_COMMON_BLOCKS = int((NUM_BLOCKS * RATIO) / 100)
NUM_NEW_BLOCKS = NUM_BLOCKS - NUM_COMMON_BLOCKS
COMMON_BLOCKS = gen_dataset.gen_dataset(NUM_COMMON_BLOCKS, B_SIZE)
FILE_SIZE = NUM_BLOCKS * B_SIZE

# lock
auth_token = 'token'
project_id = 'tenantid'
lock1 = threading.Lock()

# logging
BACKUP_COUNT = 20
MAX_LOG_BYTES = 1024 * 1024 * 20
LOG_FILENAME = 'locust_test.log'

success_handler = RotatingFileHandler(filename=LOG_FILENAME,
                                      maxBytes=MAX_LOG_BYTES,
                                      backupCount=BACKUP_COUNT,
                                      delay=1)

formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s')
formatter.converter = time.gmtime
success_handler.setFormatter(formatter)

success_logger = logging.getLogger('request.success')
success_logger.propagate = False
success_logger.addHandler(success_handler)


def success_request(request_type, name, response_time, response_length):
    msg = ' | '.join([str(request_type), name, str(response_time),
                     str(response_length)])
    success_logger.info(msg)


events.request_success += success_request


class DeuceTasks(TaskSet):

    @task
    def upload_file(self):
        """
        Locust task to Upload a file
        Creates temporary files (blocks) that are part of the file.
        Assigns all the blocks (common/new) to the file.
        Finalizes the file, with the operation failing.
        Uploads all the new blocks using msgpack.
        Finalizes the file
        """

        # generate new blocks
        self.new_blocks = []
        for _ in range(NUM_NEW_BLOCKS):
            self.new_blocks.append(gen_dataset.gen_temp_dataset(B_SIZE))
        self.list_of_blocks = COMMON_BLOCKS[:] + self.new_blocks[:]
        random.shuffle(self.list_of_blocks)

        # create a file with blocks not uploaded
        self.file_url, self.file_id = self._create_file()
        payload = util.deuce_assign_block(self.list_of_blocks, B_SIZE)
        self._assign_blocks(payload)
        self._finalize_file(incomplete=True)

        # upload the blocks
        if self.firstrun:
            payload = util.msgpacked_payload(COMMON_BLOCKS)
            self._upload_blocks(payload)
        self.firstrun = False
        if len(self.new_blocks):
            payload = util.msgpacked_payload(self.new_blocks)
            self._upload_blocks(payload)

        self._finalize_file()

        # delete temporary files
        util.remove_temp_files(self.new_blocks)

    def on_start(self):
        """
        Locust task executed at the beginning per user.
        Creates the user's vault prefixed with load_
        """

        self.vaultname = 'load_' + util.id_generator(VNAME_SIZE)
        self.firstrun = True

        if USE_AUTH:
            global lock1
            with lock1:
                self._token()
        self._create_vault()

    def _create_vault(self):
        """Create a vault"""

        self._set_headers()
        self.client.put('/v1.0/vaults/{0}'.format(self.vaultname),
                name='Create Vault')

    def _create_file(self):
        """Create a file"""

        self._set_headers()
        resp = self.client.post(
            '/v1.0/vaults/{0}/files'.format(self.vaultname),
            name='Create File')
        return resp.headers['location'], resp.headers['x-file-id']

    def _assign_blocks(self, payload):
        """Assign blocks to a file"""

        self._set_headers()
        resp = self.client.post(
            '/v1.0/vaults/{0}/files/{1}/blocks'
            ''.format(self.vaultname, self.file_id),
            data=payload,
            name='Assign Blocks')

    def _upload_blocks(self, payload):
        """Upload blocks using msgpack"""

        self._set_headers(ctype=1)
        resp = self.client.post(
            '/v1.0/vaults/{0}/blocks'.format(self.vaultname),
            data=payload,
            name='Upload Blocks')

    def _finalize_file(self, incomplete=False):
        """Finalize the file"""

        self._set_headers()
        self.client.headers.update({'x-file-length': FILE_SIZE})
        if incomplete:
            with self.client.post(
                    '/v1.0/vaults/{0}/files/{1}'
                    ''.format(self.vaultname, self.file_id),
                    name='Finalize File (409 Fail)',
                    catch_response=incomplete) as resp:
                if resp.status_code == 409:
                    resp.success()
                else:
                    resp.failure()
        else:
            resp = self.client.post(
                '/v1.0/vaults/{0}/files/{1}'
                ''.format(self.vaultname, self.file_id),
                name='Finalize File (Success)')

    def _token(self):
        """Request token and project id information"""

        import requests

        global auth_token
        global project_id
        self.auth_token = None
        self.project_id = None
        if auth_token == 'token':
            req = util.auth_request(API_USER, API_KEY)
            header = {'content-type': 'application/json'}
            resp = requests.post(
                AUTH_URL + '/tokens', data=req, headers=header)
            self.auth_token = util.auth_token(resp.json())
            self.project_id = util.project_id(resp.json())
            auth_token = self.auth_token
            project_id = self.project_id
        if self.auth_token is None:
            self.auth_token = auth_token
            self.project_id = project_id

    def _set_headers(self, ctype=0):
        """Common Headers"""

        if not ctype:
            self.client.headers.update({'content-type': 'application/json'})
        else:
            self.client.headers.update(
                {'content-type': 'application/msgpack'})
        self.client.headers.update({'x-auth-token': self.auth_token})
        self.client.headers.update({'x-project-id': self.project_id})


class DeuceUser(HttpLocust):
    task_set = DeuceTasks
    min_wait = cfg.min_pause
    max_wait = cfg.max_pause
