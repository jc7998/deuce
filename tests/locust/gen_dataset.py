import os
import sha
import shutil
import sys
import tempfile

DATA_FOLDER = './data'

if os.path.exists(DATA_FOLDER):
    shutil.rmtree(DATA_FOLDER)
os.mkdir(DATA_FOLDER)


def gen_dataset(num_files, size):
    """
    Generate a number of files (num_files) of size (size)
    """

    id_paths = []
    for _ in range(num_files):
        data = os.urandom(size)
        fname = sha.new(data).hexdigest()
        with open(os.path.join(DATA_FOLDER, fname), 'wb') as f:
            f.write(data)
            f.flush()
        id_paths.append((fname, os.path.join(DATA_FOLDER, fname)))
    return id_paths


def gen_temp_dataset(size):
    """
    Generate a file of size (size).
    Filename prefixed with load_
    """

    data = os.urandom(size)
    fname = tempfile.NamedTemporaryFile(prefix='load__',
                                        delete=False)
    fname.write(data)
    fname.flush()
    fname.close()
    return (sha.new(data).hexdigest(), fname.name)


if __name__ == '__main__':
    num_files = long(sys.argv[1])
    size = long(sys.argv[2])
    id_paths = gen_dataset(num_files, size)
