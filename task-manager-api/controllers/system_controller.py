from datetime import datetime


class SystemController:
    def __init__(self, app_name, version):
        self.app_name = app_name
        self.version = version

    def index(self):
        return {'message': self.app_name, 'version': self.version}

    def health(self):
        return {'status': 'ok', 'timestamp': str(datetime.now())}
