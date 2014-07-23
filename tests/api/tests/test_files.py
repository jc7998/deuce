from tests.api.utils import base

import ddt
import json
import os
import sha


class TestCreateFile(base.TestBase):

    def setUp(self):
        super(TestCreateFile, self).setUp()
        self.create_empty_vault()

    def test_create_file(self):
        """Create a file"""

        resp = self.client.create_file(self.vaultname)
        self.assertEqual(201, resp.status_code,
                         'Status code for creating a file is '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        self.assertIn('location', resp.headers)
        self.assertUrl(resp.headers['location'], filelocation=True)
        # TODO
        if "null" == resp.content:
            self.skipTest("Skipping because the response is null")
        self.assertEqual(0, len(resp.content))

    def tearDown(self):
        super(TestCreateFile, self).tearDown()
        self.client.delete_vault(self.vaultname)


class TestFileBlockUploaded(base.TestBase):

    def setUp(self):
        super(TestFileBlockUploaded, self).setUp()
        self.create_empty_vault()
        self.upload_block()
        self.create_new_file()

    def test_assign_block_to_file(self):
        """Assign an uploaded block to a file"""

        block_list = list()
        block_info = self.blocks[0]
        block_list.append({'id': block_info.Id, 'size': len(block_info.Data),
                           'offset': 0})
        block_dict = {'blocks': block_list}

        resp = self.client.assign_to_file(json.dumps(block_dict),
                                          alternate_url=self.fileurl)
        self.assertEqual(200, resp.status_code,
                         'Status code for assigning blocks to files '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        resp_body = json.loads(resp.content)
        self.assertListEqual([], resp_body)

    def test_assign_missing_block_to_file(self):
        """Assign a missing block to a file"""

        block_data = os.urandom(30720)
        blockid = sha.new(block_data).hexdigest()
        block_list = list()
        block_list.append({'id': blockid, 'size': len(block_data),
                           'offset': 0})
        block_dict = {'blocks': block_list}

        resp = self.client.assign_to_file(json.dumps(block_dict),
                                          alternate_url=self.fileurl)
        self.assertEqual(200, resp.status_code,
                         'Status code for assigning blocks to files '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        resp_body = json.loads(resp.content)
        self.assertListEqual([blockid], resp_body)

    def tearDown(self):
        super(TestFileBlockUploaded, self).tearDown()
        self.client.delete_vault(self.vaultname)


class TestEmptyFile(base.TestBase):

    def setUp(self):
        super(TestEmptyFile, self).setUp()
        self.create_empty_vault()
        self.create_new_file()

    def test_finalize_empty_file(self):
        """Finalize an empty file"""

        resp = self.client.finalize_file(alternate_url=self.fileurl)
        self.assertEqual(200, resp.status_code,
                         'Status code for finalizing file '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        # TODO
        if "null" == resp.content:
            self.skipTest("Skipping because the response is null")
        self.assertEqual(0, len(resp.content))

    def test_list_empty_file(self):
        """Get list of files with only one file that is empty and not
        finalized"""

        resp = self.client.list_of_files(vaultname=self.vaultname)
        self.assertEqual(200, resp.status_code,
                         'Status code for getting the list of all files '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        self.assertListEqual([], resp.json())

    def tearDown(self):
        super(TestEmptyFile, self).tearDown()
        self.client.delete_vault(self.vaultname)


class TestFileAssignedBlocks(base.TestBase):

    def setUp(self):
        super(TestFileAssignedBlocks, self).setUp()
        self.create_empty_vault()
        for _ in range(3):
            self.upload_block()
        self.create_new_file()
        self.assign_all_blocks_to_file()

    def test_finalize_file(self):
        """Finalize a file with some blocks assigned"""

        resp = self.client.finalize_file(alternate_url=self.fileurl)
        self.assertEqual(200, resp.status_code,
                         'Status code for finalizing file '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        # TODO
        if "null" == resp.content:
            self.skipTest("Skipping because the response is null")
        self.assertEqual(0, len(resp.content))

    def tearDown(self):
        super(TestFileAssignedBlocks, self).tearDown()
        self.client.delete_vault(self.vaultname)


class TestFileMissingBlock(base.TestBase):

    def setUp(self):
        super(TestFileMissingBlock, self).setUp()
        self.create_empty_vault()
        self.upload_block()
        self.generate_block_data()
        self.upload_block()
        self.generate_block_data()
        self.upload_block()
        self.create_new_file()
        self.assign_all_blocks_to_file()

    def test_finalize_file_missing_block(self):
        """Finalize a file with some blocks missing"""

        resp = self.client.finalize_file(alternate_url=self.fileurl)
        self.assertEqual(413, resp.status_code,
                         'Status code for finalizing file '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        # resp_body = json.loads(resp.content)
        # TODO: Add additional validation of the response content

    def tearDown(self):
        super(TestFileMissingBlock, self).tearDown()
        self.client.delete_vault(self.vaultname)


@ddt.ddt
class TestListBlocksOfFile(base.TestBase):

    def setUp(self):
        super(TestListBlocksOfFile, self).setUp()
        self.create_empty_vault()
        for _ in range(20):
            self.upload_block()
        self.blockids = []
        self.blockids_offsets = []
        offset = 0
        for block in self.blocks:
            self.blockids.append(block.Id)
            self.blockids_offsets.append((block.Id, offset))
            offset += len(block.Data)
        self.create_new_file()
        self.assign_all_blocks_to_file()

    def test_list_blocks_file(self):
        """List multiple blocks (20) assigned to the file"""

        resp = self.client.list_of_blocks_in_file(self.vaultname, self.fileid)
        self.assertEqual(200, resp.status_code,
                         'Status code for getting the list of blocks of a '
                         'file {0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        for t in resp.json():
            self.assertIn(t[0], self.blockids)
            i = self.blockids.index(t[0])
            self.assertEqual(t[0], self.blockids_offsets[i][0])
            self.assertEqual(t[1], self.blockids_offsets[i][1])
            del self.blockids[i]
            del self.blockids_offsets[i]
        self.assertEqual(0, len(self.blockids_offsets),
                         'Discrepancy between the list of blocks returned '
                         'and the blocks associated to the file')

    @ddt.data(2, 4, 5, 10)
    def test_list_blocks_file_limit(self, value):
        """List multiple blocks in the file, setting the limit to value"""

        url = None
        for i in range(20 / value):
            if not url:
                resp = self.client.list_of_blocks_in_file(self.vaultname,
                                                          self.fileid,
                                                          limit=value)
            else:
                resp = self.client.list_of_blocks_in_file(alternate_url=url)
            self.assertEqual(200, resp.status_code,
                             'Status code for getting the list of blocks of '
                             'a file {0}'.format(resp.status_code))
            self.assertHeaders(resp.headers, json=True)
            if i < 20 / value - 1:
                self.assertIn('x-next-batch', resp.headers)
                url = resp.headers['x-next-batch']
                self.assertUrl(url, nextfileblocklist=True)
            else:
                self.assertNotIn('x-next-batch', resp.headers)
            self.assertEqual(value, len(resp.json()),
                             'Number of block ids returned is not {0} . '
                             'Returned {1}'.format(value, len(resp.json())))
            for t in resp.json():
                self.assertIn(t[0], self.blockids)
                i = self.blockids.index(t[0])
                self.assertEqual(t[0], self.blockids_offsets[i][0])
                self.assertEqual(t[1], self.blockids_offsets[i][1])
                del self.blockids[i]
                del self.blockids_offsets[i]
        self.assertEqual(0, len(self.blockids_offsets),
                         'Discrepancy between the list of blocks returned '
                         'and the blocks associated to the file')

    @ddt.data(2, 4, 5, 10)
    def test_list_blocks_file_limit_marker(self, value):
        """List multiple blocks in the file, setting the limit to value and
        using a marker"""

        # TODO
        self.skipTest('Skipping. Currently fails because the '
                      'resp.status_code==404 due to the marker')
        markerid = self.blockids[value]

        url = None
        for i in range(20 / value - 1):
            if not url:
                resp = self.client.list_of_blocks_in_file(self.vaultname,
                                                          self.fileid,
                                                          marker=markerid,
                                                          limit=value)
            else:
                resp = self.client.list_of_blocks_in_file(alternate_url=url)
            self.assertEqual(200, resp.status_code,
                             'Status code for getting the list of blocks of '
                             'a file {0}'.format(resp.status_code))
            self.assertHeaders(resp.headers, json=True)
            if i < 20 / value - 2:
                self.assertIn('x-next-batch', resp.headers)
                url = resp.headers['x-next-batch']
                self.assertUrl(url, nextfileblocklist=True)
            else:
                self.assertNotIn('x-next-batch', resp.headers)
            self.assertEqual(value, len(resp.json()),
                             'Number of block ids returned is not {0} . '
                             'Returned {1}'.format(value, len(resp.json())))
            for t in resp.json():
                self.assertIn(t[0], self.blockids)
                i = self.blockids.index(t[0])
                self.assertEqual(t[0], self.blockids_offsets[i][0])
                self.assertEqual(t[1], self.blockids_offsets[i][1])
                del self.blockids[i]
                del self.blockids_offsets[i]
        self.assertEqual(value, len(self.blockids_offsets),
                         'Discrepancy between the list of blocks returned '
                         'and the blocks associated to the file')

    def tearDown(self):
        super(TestListBlocksOfFile, self).tearDown()
        self.client.delete_vault(self.vaultname)


class TestFinalizedFile(base.TestBase):

    def setUp(self):
        super(TestFinalizedFile, self).setUp()
        self.create_empty_vault()
        for _ in range(3):
            self.upload_block()
        self.create_new_file()
        self.assign_all_blocks_to_file()
        self.finalize_file()

    def test_get_file(self):
        """Get a (finalized) file"""

        # TODO
        self.skipTest('Skipping. Currently fails because content-type header '
                      'returned is text/html')
        resp = self.client.get_file(self.vaultname, self.fileid)
        self.assertEqual(200, resp.status_code,
                         'Status code for getting a file is '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, binary=True)
        filedata = ''
        for block in self.blocks:
            filedata += block.Data
        self.assertEqual(filedata, resp.content,
                         'Content of the file does not match was was expected')

    def test_delete_file(self):
        """Delete a (finalized) file"""

        # TODO
        self.skipTest('Skipping. Functionality not implemented')
        resp = self.client.delete_file(self.vaultname, self.fileid)
        self.assertEqual(204, resp.status_code,
                         'Status code for deleting a file is '
                         '{0}'.format(resp.status_code))
        self.assertEqual(0, len(resp.content))

    def test_list_finalized_file(self):
        """Get list of files with only one file that is finalized"""

        resp = self.client.list_of_files(vaultname=self.vaultname)
        self.assertEqual(200, resp.status_code,
                         'Status code for getting the list of all files '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        self.assertListEqual([self.fileid], resp.json())

    def tearDown(self):
        super(TestFinalizedFile, self).tearDown()
        self.client.delete_vault(self.vaultname)


@ddt.ddt
class TestMultipleFinalizedFiles(base.TestBase):

    def setUp(self):
        super(TestMultipleFinalizedFiles, self).setUp()
        self.create_empty_vault()
        self.blocks_file = []
        for _ in range(20):
            self.blocks = []
            self.create_new_file()
            self.upload_block()
            self.assign_all_blocks_to_file()
            self.blocks_file.append(self.blocks)
            self.finalize_file()

    def test_list_multiple_files(self):
        """List multiple files (20)"""

        resp = self.client.list_of_files(vaultname=self.vaultname)
        self.assertEqual(200, resp.status_code,
                         'Status code for getting the list of all files '
                         '{0}'.format(resp.status_code))
        self.assertHeaders(resp.headers, json=True)
        self.assertListEqual(sorted(self.files), resp.json())

    @ddt.data(2, 4, 5, 10)
    def test_list_files_limit(self, value):
        """List multiple files, setting the limit to value"""

        url = None
        for i in range(20 / value):
            if not url:
                resp = self.client.list_of_files(self.vaultname, limit=value)
            else:
                resp = self.client.list_of_files(alternate_url=url)
            self.assertEqual(200, resp.status_code,
                             'Status code for listing all files is '
                             '{0}'.format(resp.status_code))
            self.assertHeaders(resp.headers, json=True)
            if i < 20 / value - 1:
                self.assertIn('x-next-batch', resp.headers)
                url = resp.headers['x-next-batch']
                self.assertUrl(url, nextfilelist=True)
            else:
                self.assertNotIn('x-next-batch', resp.headers)
            self.assertEqual(value, len(resp.json()),
                             'Number of file ids returned is not {0} . '
                             'Returned {1}'.format(value, len(resp.json())))
            for fileid in resp.json():
                self.assertIn(fileid, self.files)
                self.files.remove(fileid)
        self.assertEqual(0, len(self.files),
                         'Discrepancy between the list of files returned '
                         'and the files created/finalized')

    @ddt.data(2, 4, 5, 10)
    def test_list_files_limit_marker(self, value):
        """List multiple files, setting the limit to value and using a
        marker"""

        markerid = sorted(self.files)[value]

        url = None
        for i in range(20 / value - 1):
            if not url:
                resp = self.client.list_of_files(self.vaultname,
                                                 marker=markerid, limit=value)
            else:
                resp = self.client.list_of_files(alternate_url=url)
            self.assertEqual(200, resp.status_code,
                             'Status code for listing all files is '
                             '{0}'.format(resp.status_code))
            self.assertHeaders(resp.headers, json=True)
            if i < 20 / value - 2:
                self.assertIn('x-next-batch', resp.headers)
                url = resp.headers['x-next-batch']
                self.assertUrl(url, nextfilelist=True)
            else:
                self.assertNotIn('x-next-batch', resp.headers)
            self.assertEqual(value, len(resp.json()),
                             'Number of file ids returned is not {0} . '
                             'Returned {1}'.format(value, len(resp.json())))
            for fileid in resp.json():
                self.assertIn(fileid, self.files)
                self.files.remove(fileid)
        self.assertEqual(value, len(self.files),
                         'Discrepancy between the list of files returned '
                         'and the files uploaded')

    def tearDown(self):
        super(TestMultipleFinalizedFiles, self).tearDown()
        self.client.delete_vault(self.vaultname)