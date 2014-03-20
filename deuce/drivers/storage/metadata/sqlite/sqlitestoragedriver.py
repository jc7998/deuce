
from pecan import conf

from sqlite3 import Connection
from deuce.drivers.storage.metadata import MetadataStorageDriver

# SQL schemas. Note: the schema is versions
# in such a way that new instances always start
# with user version 1, then proceeed to upgrade
# through each version until we get to the latest.

schemas = list()

schemas.append([
    """
    CREATE TABLE files
    (
        projectid TEXT NOT NULL,
        vaultid TEXT NOT NULL,
        fileid TEXT NOT NULL,
        finalized INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(projectid, vaultid, fileid)
    )
    """,
    """
    CREATE TABLE fileblocks
    (
        projectid TEXT NOT NULL,
        vaultid TEXT NOT NULL,
        fileid TEXT NOT NULL,
        blockid TEXT NOT NULL,
        offset INTEGER NOT NULL,
        UNIQUE (projectid, vaultid, fileid, blockid, offset)
    )
    """,
    """
    CREATE TABLE blocks
    (
        projectid TEXT NOT NULL,
        vaultid TEXT NOT NULL,
        blockid TEXT NOT NULL,
        size INTEGER NOT NULL,
        PRIMARY KEY(projectid, vaultid, blockid)
    )
    """
])  # Version 1

CURRENT_DB_VERSION = len(schemas)

SQL_CREATE_FILE = '''
    INSERT INTO files (projectid, vaultid, fileid)
    VALUES (:projectid, :vaultid, :fileid)
'''

SQL_GET_FILE = '''
    SELECT finalized
    FROM files
    WHERE projectid = :projectid
    AND vaultid = :vaultid
    AND fileid = :fileid
'''

SQL_DELETE_FILE = '''
    DELETE FROM files
    where projectid=:projectid
    AND vaultid=:vaultid
    AND fileid=:fileid
'''

SQL_GET_ALL_FILE_BLOCKS = '''
    SELECT blockid, offset
    FROM fileblocks
    WHERE projectid = :projectid
    AND vaultid = :vaultid
    AND fileid = :fileid
    ORDER BY offset
'''

SQL_GET_FILE_BLOCKS = '''
    SELECT blockid, offset
    FROM fileblocks
    WHERE projectid = :projectid
    AND vaultid = :vaultid
    AND fileid = :fileid
    AND offset >= :offset
    ORDER BY offset
    LIMIT :limit
'''

SQL_GET_ALL_BLOCKS = '''
    SELECT blockid
    FROM blocks
    WHERE projectid = :projectid
    AND vaultid = :vaultid
    AND blockid >= :marker
    order by blockid
    LIMIT :limit
'''

SQL_GET_ALL_FILES = '''
    SELECT fileid
    FROM files
    WHERE projectid=:projectid
    AND vaultid = :vaultid
    AND fileid >= :marker
    AND finalized = :finalized
    order by fileid
    LIMIT :limit
'''

SQL_CREATE_FILEBLOCK_LIST = '''
    CREATE TEMP TABLE fileblock_list
    AS SELECT blocks.blockid, fileblocks.offset, blocks.size
    FROM blocks, fileblocks
    WHERE fileblocks.blockid = blocks.blockid
    AND fileblocks.projectid = :projectid
    AND fileblocks.vaultid = :vaultid
    AND fileblocks.fileid = :fileid
    ORDER by offset
'''

SQL_FILEBLOCK_LIST_VALIDATE_FRONT = '''
    SELECT blockid, offset
    FROM fileblock_list
    WHERE rowid = 1
    AND offset != 0
'''

SQL_FILEBLOCK_LIST_VALIDATE = '''
    SELECT l1.offset + l1.size - l2.offset,
        l1.blockid, l1.offset, l2.blockid, l2.offset
    FROM fileblock_list l1
    JOIN fileblock_list l2
    ON l1.rowid+1 = l2.rowid and l1.offset + l1.size != l2.offset
'''

SQL_FILEBLOCK_LIST_LAST_ROW = '''
    SELECT blockid, offset, size
    FROM fileblock_list
    ORDER BY rowid DESC
    LIMIT 1
'''

SQL_FINALIZE_FILE = '''
    UPDATE files
    SET finalized=1
    WHERE projectid=:projectid
    AND fileid=:fileid
    AND vaultid=:vaultid
'''

SQL_ASSIGN_BLOCK_TO_FILE = '''
    INSERT OR REPLACE INTO fileblocks
    (projectid, vaultid, fileid, blockid, offset)
    VALUES (:projectid, :vaultid, :fileid, :blockid, :offset)
'''

SQL_REGISTER_BLOCK = '''
    INSERT OR REPLACE INTO blocks
    (projectid, vaultid, blockid, size)
    VALUES (:projectid, :vaultid, :blockid, :blocksize)
'''

SQL_UNREGISTER_BLOCK = '''
    DELETE FROM blocks
    WHERE projectid=:projectid AND blockid=:blockid
'''

SQL_HAS_BLOCK = '''
    SELECT count(*)
    FROM blocks
    WHERE projectid=:projectid
    AND blockid = :blockid
    AND vaultid = :vaultid
'''


class SqliteStorageDriver(MetadataStorageDriver):

    def __init__(self):
        self._dbfile = conf.metadata_driver.options.path
        self._conn = Connection(self._dbfile)

        self._do_migrate()

    def _get_user_version(self):
        res = self._conn.execute('pragma user_version')
        row = next(res)
        return row[0]

    def _set_user_version(self, version):
        # NOTE: for whatever reason, pragma's don't seem to
        # work with the built-in query formatter so
        # we just use string formatting here. This should be
        # OK since version is internally generated.
        self._conn.execute('pragma user_version=%d' % version)

    def _do_migrate(self):
        db_ver = self._get_user_version()

        for ver in range(db_ver, CURRENT_DB_VERSION):
            schema = schemas[db_ver]

            for query in schema:
                res = self._conn.execute(query)

            db_ver = db_ver + 1
            self._set_user_version(db_ver)

    def _determine_limit(self, limit):
        """ Determines the limit based on user input """

        # Note: +1 is allowed here because it allows
        # the user to fetch one beyond to see if they
        # are at the end of the list
        if not limit:
            res = conf.api_configuration.max_returned_num + 1
        else:
            res = min(conf.api_configuration.max_returned_num + 1, limit)

        return res

    def create_file(self, project_id, vault_id, file_id):
        """Creates a new file with no blocks and no files"""
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        res = self._conn.execute(SQL_CREATE_FILE, args)
        self._conn.commit()

        # TODO: check that one row was inserted
        return file_id

    def has_file(self, project_id, vault_id, file_id):
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        res = self._conn.execute(SQL_GET_FILE, args)

        try:
            row = next(res)
            return True
        except StopIteration:
            return False

    def is_finalized(self, project_id, vault_id, file_id):
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        res = self._conn.execute(SQL_GET_FILE, args)

        try:
            row = next(res)
            return row[0] == 1
        except StopIteration:
            return False

    def delete_file(self, project_id, vault_id, file_id):
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        res = self._conn.execute(SQL_DELETE_FILE, args)
        self._conn.commit()

    def finalize_file(self, project_id, vault_id, file_id, file_size=None):
        """Updates the files table to set a file to finalized. This function
        makes no assumptions about whether or not the file record actually
        exists"""
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        # Check for gaps and overlaps.
        retlist = []
        res = self._conn.execute(SQL_CREATE_FILEBLOCK_LIST, args)

        res = self._conn.execute(SQL_FILEBLOCK_LIST_VALIDATE_FRONT)
        if list(res):
            retlist.extend([{"Gap" if inv[0] > 0 else "Overlap":
                {"after": [None, None], "before": [inv[0], inv[1]]}}
                for inv in res])

        res = list(self._conn.execute(SQL_FILEBLOCK_LIST_VALIDATE))
        if res:
            retlist.extend([{"Gap" if inv[0] < 0 else "Overlap":
                {"after": [inv[1], inv[2]], "before": [inv[3], inv[4]]}}
                for inv in res])

        if file_size and file_size != 0:
            res = list(self._conn.execute(SQL_FILEBLOCK_LIST_LAST_ROW))
            if res and res[0][1] + res[0][2] != file_size:
                retlist.extend([{"Gap" if res[0][1] + res[0][2]
                    - file_size < 0 else "Overlap":
                    {"after": [inv[0], inv[1]]}}
                    for inv in res])

        self._conn.execute('DROP TABLE IF EXISTS fileblock_list')

        if retlist:
            return retlist

        res = self._conn.execute(SQL_FINALIZE_FILE, args)
        self._conn.commit()
        return None

    def get_file_data(self, project_id, vault_id, file_id):
        """Returns a tuple representing data for this file"""
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id
        }

        res = self._conn.execute(SQL_GET_FILE, args)

        try:
            row = next(res)
        except StopIteration:
            raise Exception("No such file: {0}".format(file_id))

        return row

    def has_block(self, project_id, vault_id, block_id):
        # Query the blocks table
        retval = False

        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'blockid': block_id
        }

        res = self._conn.execute(SQL_HAS_BLOCK, args)

        cnt = next(res)
        return cnt[0] > 0

    def create_block_generator(self, project_id, vault_id, marker=0, limit=0):

        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'limit': self._determine_limit(limit),
            'marker': marker
        }

        res = self._conn.execute(SQL_GET_ALL_BLOCKS, args)

        return [row[0] for row in res]

    def create_file_generator(self, project_id, vault_id,
                              marker=0, limit=0, finalized=True):

        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'limit': self._determine_limit(limit),
            'marker': marker,
            'finalized': finalized
        }

        res = self._conn.execute(SQL_GET_ALL_FILES, args)
        return [row[0] for row in res]

    def create_file_block_generator(self, project_id, vault_id, file_id,
                                    offset=None, limit=None):

        args = {
            'fileid': file_id,
            'projectid': project_id,
            'vaultid': vault_id,
        }

        if limit is None:
            query = SQL_GET_ALL_FILE_BLOCKS

        else:
            query = SQL_GET_FILE_BLOCKS

            args.update({
                'limit': self._determine_limit(limit),
                'offset': offset or 0
            })

        query_res = self._conn.execute(query, args)

        return [(row[0], row[1]) for row in query_res]

    def assign_block(self, project_id, vault_id, file_id, block_id, offset):
        # TODO(jdp): tweak this to support multiple assignments
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'fileid': file_id,
            'blockid': block_id,
            'offset': offset
        }

        res = self._conn.execute(SQL_ASSIGN_BLOCK_TO_FILE, args)
        self._conn.commit()

    def register_block(self, project_id, vault_id, block_id, blocksize):
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'blockid': block_id,
            'blocksize': blocksize
        }

        res = self._conn.execute(SQL_REGISTER_BLOCK, args)
        self._conn.commit()

    def unregister_block(self, project_id, vault_id, block_id):
        args = {
            'projectid': project_id,
            'vaultid': vault_id,
            'blockid': block_id
        }

        res = self._conn.execute(SQL_UNREGISTER_BLOCK, args)
        self._conn.commit()
