import os
import stat
import logging

class Pipe():
    def __init__(self, f_name, blocking=True, debug=False):
        """Create named pipe

        Args:
            f_name   : Desired file name
            blocking : Whether or not to use blocking file reads
            debug    : Verbose debug output
        """
        if (debug):
            logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

        # Define name pipe open flags
        if (not blocking):
            flags = os.O_RDWR | os.O_NONBLOCK
        else:
            flags = os.O_RDWR

        # Create pipe directory, in case it does not exist yet
        pipe_dir = os.path.dirname(f_name)
        if not os.path.exists(pipe_dir):
            os.makedirs(pipe_dir)

        # Check if file exists
        if os.path.exists(f_name):
            logging.debug('File %s exists' % f_name)
            # Check if the file is pipe
            if stat.S_ISFIFO(os.stat(f_name).st_mode):
                logging.debug('and is pipe, opening ...')
                pipe = os.open(f_name, flags)
            else:
                logging.debug('but is not pipe, remove and recreate ...')
                os.system('rm ' + f_name)
                os.mkfifo(f_name, 0o777)
                pipe = os.open(f_name, flags)
        else:
            logging.debug("File %s does not exist, create ..." % f_name)
            os.mkfifo(f_name, 0o777)
            pipe = os.open(f_name, flags)

        # Save internally
        self.pipe = pipe
        self.name = f_name

    def __del__(self):
        """Close named pipe

        """
        os.close(self.pipe)

    def read(self, size):
        """Read data from pipe file

        Args:
            data : The data to write into the pipe file
        """
        data = os.read(self.pipe, size)

        return data

    def write(self, data):
        """Write data to pipe file

        Args:
            data : The data to write into the pipe file
        """
        os.write(self.pipe, data)

