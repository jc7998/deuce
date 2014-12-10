import ConfigParser


class ZapConfig(object):

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('zap/config.cfg')

    @property
    def proxy_url(self):
        """URL to ZAP"""
        return self.config.get('zap', 'proxy')

    @property
    def attack_level(self):
        """ZAP Active Scan Level. LOW, MEDIUM, HIGH, INSANE"""
        return self.config.get('zap', 'attacklevel')
