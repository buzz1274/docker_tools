#!/usr/bin/python

"""
Copyright (c) 2015 David Exelby

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys
import subprocess
import json
import re
from termcolor import cprint
from optparse import OptionParser

class DockerTools():

    parser = None
    containers = None

    def __init__(self):
        """
        initialize docker tools
        """
        self.create_parser()

    def parse_args(self):
        """
        parse command line args and execute command
        """
        (options, args) = self.parser.parse_args()

        if not os.geteuid() == 0:
            sys.exit("Please use sudo dt.py")

        if options.kill:
            self.kill(options.kill)

        if options.connect:
            self.connect(options.connect)

        if options.update_hosts:
            self.update_hosts()

    def kill(self, container):
        """
        stops and removes the named container
        """
        subprocess.call(['docker', 'stop', container])
        subprocess.call(['docker', 'rm', container])
        subprocess.call(['dt', '-u'])

    def update_hosts(self):
        """
        updates /etc/hosts with the ip-address for all
        current containers
        """
        hosts_entries = []
        containers = subprocess.check_output(['docker', 'ps', '-aq',
                                              '--no-trunc'])

        for container in containers.split("\n"):
            try:
                if container:
                    container_details = \
                        subprocess.check_output(['docker', 'inspect',
                                                 container])

                    if container_details:
                        container_details = json.loads(container_details)
                        if (container_details[0]['NetworkSettings']['IPAddress'] and
                            container_details[0]['Name']):
                            hosts_entries.append("%s %s" %\
                                (container_details[0]['NetworkSettings']['IPAddress'],
                                 container_details[0]['Name'].strip('/')))

            except Exception:
                pass

        if hosts_entries:
            hosts_entries = \
                "##Auto Generated Entries[DO NOT EDIT]##\n%s\n##END##" %\
                ("\n".join(hosts_entries,))

            try:
                with open('/etc/hosts', 'r+') as f:
                    hosts_file = f.read()
                    hosts_file = "%s%s" % (re.sub(r"##Auto.*##END##", '',
                                                  hosts_file, flags=re.S),
                                           hosts_entries,)

                    f.seek(0)
                    f.write(hosts_file)

            except IOError:
                self.error("Error: Updating host file.")

    def connect(self, container):
        """
        connects to the named docker container
        """
        subprocess.call(['docker', 'exec', '-it', container, 'bash'])

    def error(self, error_message):
        """
        displays an error message and exits
        """
        cprint(error_message, 'red')
        sys.exit()

    def create_parser(self):
        """
        create parser for command line args
        """
        self.parser = OptionParser()
        self.parser.add_option('-k', '--kill', dest='kill', metavar='kill',
                               help='stop and remove the named container')
        self.parser.add_option('-c', '--connect', dest='connect',
                               metavar='connect',
                               help='connect to the named container')
        self.parser.add_option('-u', '--update_hosts', dest='update_hosts',
                               metavar='update_hosts', action="store_true",
                               help='update hosts file with container ips')


if __name__ == '__main__':
    DockerTools().parse_args()
