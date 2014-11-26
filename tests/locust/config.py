import ConfigParser


class LocustConfig(object):

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('config.cfg')

    @property
    def vaultname_size(self):
        """Length for vault names"""
        return self.config.getint('deuce', 'vaultname_size')

    @property
    def num_blocks(self):
        """Number of blocks per file"""
        return self.config.getint('deuce', 'num_blocks')

    @property
    def block_size(self):
        """Size of a single block"""
        return self.config.getint('deuce', 'block_size')

    @property
    def dedup_ratio(self):
        """Deduplication Ratio"""
        return self.config.getint('deuce', 'dedup_ratio')

    @property
    def min_pause(self):
        return self.config.getint('locust', 'min_pause')

    @property
    def max_pause(self):
        return self.config.getint('locust', 'max_pause')

    @property
    def api_user(self):
        return self.config.get('authentication', 'api_user')

    @property
    def api_key(self):
        return self.config.get('authentication', 'api_key')

    @property
    def use_auth(self):
        return self.config.getboolean('authentication', 'use_auth')

    @property
    def auth_url(self):
        return self.config.get('authentication', 'base_url')
