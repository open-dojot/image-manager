""" Service configuration module """

import os


class Config(object):
    """ Abstracts configuration, either retrieved from environment or from ctor arguments """

    def __init__(self,
                 db="dojot_imgm",
                 dbhost="postgres",
                 dbuser="postgres",
                 dbpass=None,
                 dbdriver="postgresql+psycopg2",
                 create_db=True,
                 s3url='minio:9000',
                 s3user='9HEODSF6WQN5EZ39DM7Z',
                 s3pass='fT5nAgHR9pkj0yYsBdc4p+PPq6ArjshcPdz0HA6W'):
        self.dbname = os.environ.get('DBNAME', db)
        self.dbhost = os.environ.get('DBHOST', dbhost)
        self.dbuser = os.environ.get('DBUSER', dbuser)
        self.dbpass = os.environ.get('DBPASS', dbpass)
        self.dbdriver = os.environ.get('DBDRIVER', dbdriver)
        self.create_db = os.environ.get('CREATE_DB', create_db)
        self.s3url = os.environ.get('S3URL', s3url)
        self.s3user = os.environ.get('S3ACCESSKEY', s3user)
        self.s3pass = os.environ.get('S3SECRETKEY', s3pass)

    def get_db_url(self):
        """ From the config, return a valid postgresql url """
        if self.dbpass is not None:
            return "%s://%s:%s@%s/%s" % (self.dbdriver, self.dbuser, self.dbpass,
                                         self.dbhost, self.dbname)
        else:
            return "%s://%s@%s/%s" % (self.dbdriver, self.dbuser, self.dbhost, self.dbname)


CONFIG = Config()
