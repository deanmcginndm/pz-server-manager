from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from configparser import ConfigParser
import socket
from paramiko.py3compat import u
import os
import sys
import select
import termios
import tty
import pty
from subprocess import Popen


# windows does not have termios... because windows suucks sweaty balls... so bite me Bill....
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        return posix_shell(chan)
    else:
        return windows_shell(chan)


def posix_shell(chan):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = u(chan.recv(1024))
                    if len(x) == 0:
                        sys.stdout.write("\r\n*** EOF\r\n")
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write(
        "Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n"
    )

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write("\r\n*** EOF ***\r\n\r\n")
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass


class PZOptionsManager(ConfigParser):
    def __init__(self, *args, **kwargs):
        filename = kwargs.pop('options_filename', 'management/options.ini')
        super(PZOptionsManager, self).__init__(*args, **kwargs)
        self.read(filename)

    def optionxform(self, optionstr):
        # we override this to preserve case of the cofig file keys
        # which otherwise would be exported as lower equivlant which isnt read on server
        return str(optionstr)


class PZServerManager(object):
    _client = None
    _mods = None
    container_name = None
    ssh_mode = True

    def __init__(self,
                 hostname: str = '51.89.137.84',  # os.environ.get('PZ_REMOTE_HOST'),
                 username: str = 'ubuntu',  # os.environ.get('PZ_REMOTE_USER'),
                 key_filename: str = 'management/broco_id_rsa',
                 container_name: str = 'pz',
                 options_key: str = 'DEFAULT',
                 options_file_path: str = 'management/options.ini'):
        self.hostname = hostname
        self.username = username

        self.key_filename = key_filename
        self.container_name = container_name
        if not hostname or not username:
            self.ssh_mode = False
        self._client = self.client
        self.options_key = options_key

        self.options_file_path = options_file_path
        self._options = PZOptionsManager(options_filename=self.options_file_path, interpolation=None)
        self.settings = self.options[options_key]

        self.mods  # ensures mods is populated and serialised from the options file
        self.update_setting_attributes()

    @property
    def scp(self):
        if not self.ssh_mode:
            raise NotImplementedError('SCP is only supported in ssh mode, use the web interface to manage your files')
        self.connect
        return SCPClient(self.client.get_transport())

    @property
    def client(self):
        if not self._client:
            if self.ssh_mode:
                self._client = SSHClient()
                self._client.load_system_host_keys()
                self._client.set_missing_host_key_policy(AutoAddPolicy())
            else:
                self._client = LocalClient()
        return self._client

    @property
    def connect(self):
        self._client.connect(hostname=self.hostname, username=self.username, key_filename=self.key_filename)
        return self._client

    ###############################
    #                             #
    #         SSH COMMANDS        #
    #                             #
    ###############################
    @property
    def df(self):
        sin, sout, serr = self.run('df')
        print(sout.read().decode())

    @property
    def restart_server(self):
        self.stop_server
        return self.start_server

    @property
    def stop_server(self):
        return self.run(f'docker exec -it {self.container_name} ./anthesis-pzserver stop', get_pty=True)

    @property
    def start_server(self):
        return self.run(f'docker exec -it {self.container_name} ./anthesis-pzserver start', get_pty=True)

    @property
    def status(self):
        return self.run(f'docker exec -it {self.container_name} ./anthesis-pzserver monitor', get_pty=True)

    def server_console(self):
        print('acquiring pzserver console...')
        self.connect
        channel = self.client.get_transport().open_session()

        # Open interactive SSH session
        channel.get_pty()
        channel.invoke_shell()

        print('Executing command 1')
        ret = channel.send(f'docker exec -it {self.container_name} ./anthesis-pzserver console')
        print(ret)

        print('Executing command 2')
        ret = channel.send('showoptions\n')
        print(ret)

    @property
    def logs_follow(self):
        raise NotImplementedError('currently doesnt work for some reason/s')
        return self._logs(follow=True)

    @property
    def logs(self):
        return self._logs(follow=False)

    def _logs(self, follow=False):
        if not follow:
            return self.run(
                f'docker exec -it {self.container_name} '
                'cat Zomboid/server-console.txt',
                get_pty=True
            )
        return self.run(
            f'docker exec -it {self.container_name} '
            'tail -fn +1 Zomboid/server-console.txt',
            get_pty=True
        )

    def run(self, command: str, **kwargs):
        if self.ssh_mode:
            self.connect
            return sys.stdout.write(self.client.exec_command(command, **kwargs)[1].read().decode())
        else:
            return sys.stdout.write(self.client.exec_command(command))

    def download_settings(self):
        try:
            self.scp.get('project/server-data/Server/anthesis-pzserver.ini', './options.ini', )
            return True
        except Exception as e:
            print(e)
            return False

    def upload_settings(self, restart_server=False):
        try:
            self.scp.put('./options.ini', 'project/server-data/Server/anthesis-pzserver.ini')
            if restart_server:
                self.restart_server
            return True
        except Exception as e:
            print(e)
            return False

    def upload_file(self, host_path, remote_path):
        try:
            self.scp.put(host_path, remote_path)
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def options(self):
        return self._options

    def save_options(self):
        for setting in self.settings:
            self.options[self.options_file_path][setting] = getattr(self, setting)
        try:
            with open(self.options_file_path, 'w') as configfile:
                self.options.write(configfile, space_around_delimiters=False)
            return True
        except Exception as e:
            print(e)
            return False

    def get_mod_list(self):
        return list(zip(
            self.options['DEFAULT']['Mods'].split(';'),
            self.options['DEFAULT']['WorkshopItems'].split(';')
        ))

    def set_mod_list(self):
        try:
            mods_string = ';'.join([x[0] for x in self.mods])
            workshop_items_string = ';'.join([x[1] for x in self.mods])
            self.Mods = mods_string
            self.WorkshopItems = workshop_items_string
        except Exception as e:
            print(e)
            return False
        return True

    def add_mod(self, mod_id: str):
        from bs4 import BeautifulSoup
        import requests
        r = requests.get(f'https://steamcommunity.com/workshop/filedetails/?id={mod_id}')
        s = BeautifulSoup(r.content, 'html.parser')
        l = str(s.select_one('#highlightContent')).split('<br/>')[-5:]
        l = [x for x in l if 'Mod ID:' in x or 'Workshop ID:' in x]
        l[-1] = BeautifulSoup(l[-1], 'html.parser').text  # accurately remove any html tags if there is any
        if len(l) > 2:
            raise NotImplementedError('we dont support adding more that 1 of each mod id and workshop id')
        v = (l[1].split()[-1], l[0].split()[-1])
        self.mods.append(v)
        self.set_mod_list()
        print(f'added mod {v} successfully')

    def remove_mod(self, mod_id: str):
        self._mods = list(filter(lambda x: x[1] != mod_id, self.mods))
        return self.mods

    @property
    def mods(self):
        if self._mods is None:
            self._mods = self.get_mod_list()
        return self._mods

    def update_setting_attributes(self):
        for setting in self.settings:
            setattr(self, setting, self.settings[setting])

command = 'bash'
# command = 'docker run -it --rm centos /bin/bash'.split()

# save original tty setting then set it to raw mode
class LocalClient(object):
    def exec_command(self, command, *args, **kwargs):
        old_tty = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        # open pseudo-terminal to interact with subprocess
        master_fd, slave_fd = pty.openpty()

        # use os.setsid() make it run in a new process group, or bash job control will not be enabled
        try:
            p = Popen(command,
                      preexec_fn=os.setsid,
                      stdin=slave_fd,
                      stdout=slave_fd,
                      stderr=slave_fd,
                      shell=False)

            while p.poll() is None:
                r, w, e = select.select([sys.stdin, master_fd], [], [])
                if sys.stdin in r:
                    d = os.read(sys.stdin.fileno(), 10240)
                    os.write(master_fd, d)
                if master_fd in r:
                    o = os.read(master_fd, 10240)
                    if o:
                        os.write(sys.stdout.fileno(), o)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            return p
        except Exception as e:
            print(str(e) + '\r\n')
            # restore tty settings back
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
