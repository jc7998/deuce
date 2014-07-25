from tests.api.utils import base

import os
import time

from zapv2 import ZAPv2

class TestZAP(base.TestBase):

    def setUp(self):
        super(TestZAP, self).setUp()
        # Configure ZAP
        self.http_proxy = os.environ.get('HTTP_PROXY')
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
        self.zap = ZAPv2()
        self.zap.ascan.enable_all_scanners()
        self.zap.ascan.set_option_attack_strength('INSANE')
        for policy in self.zap.ascan.policies:
            if policy['enabled'] != 'true':
                self.zap.ascan.set_enabled_policies([policy['id']])

        # Deuce Api Calls (build site map for ZAP)
        self.create_empty_vault()
        self.blocks_file = []
        self.blocks = []
        self.create_new_file()
        for _ in range(3):
            self.upload_block()
        self.assign_all_blocks_to_file()
        self.blocks_file.append(self.blocks)
        self.finalize_file()
        self.client.get_vault(self.vaultname)
        self.client.vault_head(self.vaultname)
        self.client.list_of_blocks(vaultname=self.vaultname)
        self.client.list_of_blocks(vaultname=self.vaultname, limit=20)
        self.client.list_of_blocks(vaultname=self.vaultname, marker=self.blockid, limit=20)
        self.client.get_block(self.vaultname, self.blockid)
        self.client.list_of_blocks_in_file(vaultname=self.vaultname, fileid=self.fileid)
        self.client.list_of_blocks_in_file(vaultname=self.vaultname, fileid=self.fileid, limit=20)
        self.client.list_of_blocks_in_file(vaultname=self.vaultname, fileid=self.fileid, marker=self.blockid, limit=20)
        self.client.get_file(vaultname=self.vaultname, fileid=self.fileid)
        self.client.list_of_files(vaultname=self.vaultname)
        self.client.list_of_files(vaultname=self.vaultname, limit=20)
        self.client.list_of_files(vaultname=self.vaultname, marker=self.fileid, limit=20)



    def test_zap(self):

        # Do an Active Scan on the main Deuce Url
        self.zap_scan_url = self.zap.core.urls[0]
        self.zap.ascan.scan(self.zap_scan_url, recurse='true')
        while int(self.zap.ascan.status) < 100:
            print('Scan progress {0}'.format(self.zap.ascan.status))
            time.sleep(5)
        print('Scan completed')    
        alerts = self.zap.core.alerts()
        if len(alerts):
            raise Exception(str(alerts))

    def tearDown(self):
        if not self.http_proxy:
            del os.environ['HTTP_PROXY']
        else:
            os.environ['HTTP_PROXY'] = self.http_proxy
