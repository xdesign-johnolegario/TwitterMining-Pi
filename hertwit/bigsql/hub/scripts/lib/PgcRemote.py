####################################################################
############      Copyright (c) 2016 BigSQL           ##############
####################################################################

import paramiko
from fabric.state import connections, ssh
from fabric.api import env, hide, cd, put, run, settings, sudo
from fabric.contrib import files
from StringIO import StringIO
from fabric.context_managers import shell_env
import os
from fabric.context_managers import remote_tunnel

class PgcRemoteException(Exception):
    pass


class PgcRemote(object):
    def __init__(self, host, username="", password=""):
        self.user = username
        self.host = host
        self.password = password
        self.sftp = None
        self.client = None
        env.host_string = "%s@%s" % (username, host)  # , 22)
        env.password = password
        env.remote_interrupt = True
        env.output_prefix = False
        env.connection_attempts = 1
        env.warn_only = True

    def connect(self):
        sshClient = ssh.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshClient.connect(self.host,
                          username=self.user,
                          password=self.password, timeout=10)
        if env.host_string not in connections:
            connections[env.host_string] = sshClient
        self.client = sshClient

    def is_exists(self, path):
        return files.exists(path)

    def upload_pgc(self, source_path, target_path, pgc_version, repo, repo_port=8000):
        with cd(target_path), shell_env(PGC_VER=pgc_version, PGC_REPO=repo), remote_tunnel(repo_port),hide("everything"):
            pgc_file = "bigsql-pgc-" + pgc_version + ".tar.bz2"
            source_file = os.path.join(source_path, pgc_file)
            put(source_file, ".")
            source_file = os.path.join(source_path, "install.py")
            put(source_file, ".")
            run("python install.py")
            run("rm install.py")

    def execute(self, cmd):
        with settings(hide('everything'), warn_only=True):
            m = run(cmd, shell_escape=True, pty=False)
            if m.return_code == 0:
                out = m.stdout.strip()
                err = m.stderr.strip()
            else:
                out = ""
                err = m.stdout.strip()
            return {"stdout": out, "stderr": err}

    def disconnect(self):
        self.client.get_transport().close()
