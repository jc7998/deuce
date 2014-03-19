from pecan import conf
import os
import hashlib
import string
import six
from six.moves.urllib.parse import urlparse, parse_qs
from unittest import TestCase
from deuce.tests import FunctionalTest
from deuce.drivers.storage.metadata.sqlite import SqliteStorageDriver
import uuid


class TestFilesController(FunctionalTest):

    def setUp(self):
        super(TestFilesController, self).setUp()

        self.file_list = []
        self.max_ret_num = conf.api_configuration.max_returned_num
        self.total_file_num = 0
        self._hdrs = {"X-Project-ID": "test_project_id"}

        # Create a vault and a file for us to work with
        self.project_id = 'test_project_id'
        self.vault_id = 'files_vault_test'
        self._vault_path = '/v1.0/' + self.vault_id
        self._files_path = self._vault_path + '/files'

        # Create Vault
        response = self.app.post(self._vault_path, headers=self._hdrs)
        # Create File
        response = self.app.post(self._files_path, headers=self._hdrs)
        self._file_id = response.headers["Location"]
        self._file_id = urlparse(self._file_id).path
        # Now, _file_id is '/v1.0/files_vault_test/files/SOME_FILE_ID'

        self._NOT_EXIST_files_path = '/v1.0/not_exists/files'

    def _create_file_id(self):
        return str(uuid.uuid4())

    def test_tenancy_requirement(self):
        # vault does not exists
        # If we pass in no headers, we should get a 400 back
        response = self.app.get(self._NOT_EXIST_files_path,
                                expect_errors=True)
        assert response.status_int == 400

        # vault does not exists
        response = self.app.get(self._NOT_EXIST_files_path,
                                headers=self._hdrs, expect_errors=True)
        assert response.status_int == 404  # Not found

    def helper_create_files(self, num):
        params = {}
        for cnt in range(0, num):
            response = self.app.post(self._files_path, headers=self._hdrs)
            file_id = response.headers["Location"]
            response = self.app.post(file_id,
                                     params=params, headers=self._hdrs)
            file_id = urlparse(file_id).path.split('/')[-1]
            self.file_list.append(file_id)
        return num

    def helper_get_files(self, marker, limit, assert_return_url,
                         assert_data_len, repeat=False):

        resp_file_list = []

        params = dict()

        if limit is not None:
            params['limit'] = limit

        while True:

            response = self.app.get(self._files_path,
                                    params=params, headers=self._hdrs)

            next_batch_url = response.headers.get("X-Next-Batch", '')

            resp_file_list += list(response.json_body)
            assert isinstance(response.json_body, list)

            if not repeat:
                assert (not next_batch_url) == (not assert_return_url)
                assert len(resp_file_list) == assert_data_len
                for h in resp_file_list:
                    assert h in self.file_list
                if assert_data_len == -1 or \
                        assert_data_len == self.total_file_num:
                    for h in self.file_list:
                        assert h in resp_file_list
                return next_batch_url
            if not next_batch_url:
                break

            params['marker'] = \
                parse_qs(urlparse(next_batch_url).query)['marker']

        self.assertEqual(len(resp_file_list), assert_data_len)

        for h in resp_file_list:
            assert h in self.file_list
        for h in self.file_list:
            assert h in resp_file_list

    def test_get_all(self):
        # Create few (< max_returned_num) files in the vault
        file_num = int(0.5 * self.max_ret_num)
        self.total_file_num = self.helper_create_files(file_num)

        # Get list of files in the vault with a given limit.
        next_batch_url = self.helper_get_files(marker=None, limit=4,
           assert_return_url=True, assert_data_len=4)

        # Get list of all files in the vault with the default limit.
        self.helper_get_files(marker=None, limit=None,
            assert_return_url=False, assert_data_len=self.total_file_num)
        # Add more (< max_returned_num) files in the vault
        file_num = int(0.5 * self.max_ret_num) - 1
        self.total_file_num += self.helper_create_files(file_num)

        # Get list of all files in the vault.
        self.helper_get_files(marker=None, limit=None,
            assert_return_url=False, assert_data_len=self.total_file_num)

        # Add one more file
        self.total_file_num += self.helper_create_files(1)

        # Get list of all files in the vault, which is exact one load.
        next_batch_url = self.helper_get_files(marker=None, limit=None,
           assert_return_url=False,
           assert_data_len=self.total_file_num)

        # Add more files to make the total files more than one load
        file_num = int(0.5 * self.max_ret_num)
        self.total_file_num += self.helper_create_files(file_num)

        # Get list of all files in the vault, need multiple runs,
        self.helper_get_files(marker=None, limit=None,
            assert_return_url=False, assert_data_len=self.total_file_num,
            repeat=True)

    def test_bad_limit_and_marker(self):

        params = dict(marker='blah')
        response = self.app.get(self._NOT_EXIST_files_path,
            params=params, headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_code, 404)

        params = dict(limit='blah')
        response = self.app.get(self._NOT_EXIST_files_path,
            params=params, headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_code, 404)

        params = dict(marker='blah')
        response = self.app.get(self._NOT_EXIST_files_path + '/' +
            self._create_file_id() + '/blocks', params=params,
            headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_code, 404)

    def test_get_one(self):
        # vault does not exists
        response = self.app.get(self._NOT_EXIST_files_path,
                                headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 404)

        response = self.app.get(self._NOT_EXIST_files_path + '/',
                                headers=self._hdrs, expect_errors=True)
        assert response.status_int == 404

        file_id = self._create_file_id()

        response = self.app.get(self._NOT_EXIST_files_path + '/' + file_id,
                                headers=self._hdrs, expect_errors=True)

        assert response.status_int == 404

        # fileid is not privded
        response = self.app.get(self._files_path + '/', headers=self._hdrs,
                                expect_errors=True)
        assert response.status_int == 404

        # fileid does not exists
        response = self.app.get(self._files_path + '/' + file_id,
                                headers=self._hdrs, expect_errors=True)

        assert response.status_int == 404

    def test_post_and_check_one_file(self):
        # vault does not exists
        response = self.app.post(self._NOT_EXIST_files_path,
                                 headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 400)

        response = self.app.post(self._NOT_EXIST_files_path + '/',
                                 headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 400)

        file_id = self._create_file_id()

        response = self.app.post(self._NOT_EXIST_files_path + '/' + file_id,
                                 headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 400)

        # fileid is not provided.
        response = self.app.post(self._files_path + '/',
                                 headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 400)

        # fileid does not exists
        response = self.app.post(self._files_path + '/' +
             self._create_file_id(), headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_int, 404)

        hdrs = {'content-type': 'application/x-deuce-block-list'}
        hdrs.update(self._hdrs)
        data = "{\"blocks\":["
        enough_num = int(conf.api_configuration.max_returned_num)
        for cnt in range(0, enough_num):
            data = data + '{' + '\"id\": {0}, \"size\": 100, \
                \"offset\": {1}'.format(cnt, cnt * 100) + '}'
            if cnt < enough_num - 1:
                data = data + ','
        data = data + ']}'
        # Add blocks to files, resp has a list of missing blocks.
        response = self.app.post(self._file_id, params=data, headers=hdrs)
        assert len(response.body) > 2

        driver = SqliteStorageDriver()

        # Register 100 blocks into system.
        for cnt in range(0, enough_num):
            driver.register_block(self.project_id, self.vault_id, cnt, 100)
        # Then add blocks to files again. resp is empty.
        response = self.app.post(self._file_id, params=data, headers=hdrs)

        assert len(response.body) == 2

        # Get unfinalized file.
        response = self.app.get(self._file_id, headers=hdrs)
        assert len(response.body) == 0

        # Register 120 blocks into system.
        data = "{\"blocks\":["
        enough_num = int(1.2 * conf.api_configuration.max_returned_num)
        for cnt in range(conf.api_configuration.max_returned_num, enough_num):
            data = data + '{' + '\"id\": {0}, \"size\": 100, \
                \"offset\": {1}'.format(cnt, cnt * 100) + '}'
            if cnt < enough_num - 1:
                data = data + ','
            driver.register_block(self.project_id, self.vault_id, cnt, 100)

        data = data + ']}'
        # Then add blocks to files again. resp is empty.
        response = self.app.post(self._file_id, params=data, headers=hdrs)
        assert len(response.body) == 2

        # Get the file.
        response = self.app.get(self._file_id, headers=hdrs)
        assert len(response.body) == 0

        # Finalize file
        params = {}
        response = self.app.post(self._file_id, params=params, headers=hdrs)
        assert response.status_int == 200

        # Error on trying to change Finalized file.
        response = self.app.post(self._file_id, params=data, headers=hdrs,
                                 expect_errors=True)

        assert response.status_int == 400

        # Get finalized file.
        response = self.app.get(self._file_id, headers=hdrs)
        assert response.status_int == 200

        # Now list the blocks that make up this file
        self.helper_test_file_blocks_controller(self._file_id, hdrs)

    def test_nonexistent_file_endpoints(self):
        file_path_format = '/v1.0/{0}/files/{1}'

        incorrect_vault = file_path_format.format('bogus_vault',
                                                  self._create_file_id())

        response = self.app.get(incorrect_vault, headers=self._hdrs,
                                expect_errors=True)

        self.assertEqual(response.status_code, 404)

        incorrect_file = file_path_format.format(self.vault_id,
                                                 self._create_file_id())

        response = self.app.get(incorrect_file, headers=self._hdrs,
                                expect_errors=True)

        self.assertEqual(response.status_code, 404)

        incorrect_file_get_blocks = file_path_format.format(self.vault_id,
            self._create_file_id()) + '/blocks'

        response = self.app.get(incorrect_file_get_blocks,
                                headers=self._hdrs, expect_errors=True)

        self.assertEqual(response.status_code, 404)

    def helper_test_file_blocks_controller(self, file_id, hdrs):
        # Get blocks of a file.
        response = self.app.get(file_id + '/blocks', headers=hdrs)
        assert response.status_int == 200
        next_batch_url = response.headers["X-Next-Batch"]

        # vault does not exists
        response = self.app.get(self._NOT_EXIST_files_path +
                                '/%s/blocks' % (file_id,),
                                headers=self._hdrs, expect_errors=True)

        assert response.status_int == 404  # Not found

        # fileid does not exists
        nonexistent_fileid = self._create_file_id()
        response = self.app.get(self._files_path +
                                '/%s/blocks' % (nonexistent_fileid, ),
                                headers=self._hdrs, expect_errors=True)

        assert response.status_int == 404

        # Get blocks of a file. with limit not zero
        params = {'limit': '5'}
        response = self.app.get(file_id + '/blocks',
                                params=params, headers=hdrs)

        assert response.status_int == 200
        next_batch_url = response.headers["X-Next-Batch"]

        resp_block_list = []
        # params = {'marker': 0}
        while True:
            response = self.app.get(file_id + '/blocks',
                                    params=params, headers=self._hdrs)

            next_batch_url = response.headers.get("X-Next-Batch", '')
            resp_block_list += list(response.json_body)
            assert isinstance(response.json_body, list)
            if not next_batch_url:
                break
            params['marker'] = \
                parse_qs(urlparse(next_batch_url).query)['marker']

        self.assertEqual(len(resp_block_list), 1.2 *
                         conf.api_configuration.max_returned_num)