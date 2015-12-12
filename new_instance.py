#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import instances, logger

from ansible.playbook import PlayBook
from ansible.inventory import Inventory
from tempfile import NamedTemporaryFile
from ansible import callbacks
from ansible import utils

from tempfile import NamedTemporaryFile
import ConfigParser
import jinja2
import sys
import os

# Read the coonfig file
CONFIG = ConfigParser.ConfigParser()
CONFIG.read('cloud.ini')

# Simple logger
LOGGER = logger.setup_logger("new_instance")

# Ansible loggers, courtesy of https://serversforhackers.com/running-ansible-programmatically
utils.VERBOSITY = 1
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
stats = callbacks.AggregateStats()
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

# check_pubkey, if it does not exist will create an "ansible" key
instances.check_pubkey(CONFIG.get("instances", "key_name"), CONFIG.get("instances", "pub_key_path"))

# Let's create the server
server = instances.create_server('%s' % (sys.argv[1]),
    CONFIG.get("instances", "flavor"),
    CONFIG.get("instances", "image"),
    CONFIG.get("instances", "key_name")
)
addr = instances.wait_for_vm_ip('%s' % sys.argv[1])

# Generate the inventory template
inventory = jinja2.Template("{{ hostname }} ansible_ssh_host=\"{{ host_address }}\"")
inventory = inventory.render({"hostname": "%s" % sys.argv[1], "host_address": addr[0]})
hosts = NamedTemporaryFile(delete=False)
hosts.write(inventory)
hosts.close()
LOGGER.info("Inventory: %s" % inventory)

# Wait for the VM to come up
instances.wait_for_vm_ssh(addr[0])

pb = PlayBook(
    playbook='post_create.yml',
    host_list=hosts.name,
    remote_user='admin',
    become='true',
    become_user='root',
    become_method="sudo",
    callbacks=playbook_cb,
    runner_callbacks=runner_cb,
    stats=stats,
    private_key_file=CONFIG.get("instances", "priv_key_path")
)
results = pb.run()


pb = PlayBook(
    playbook='base.yml',
    host_list=hosts.name,
    remote_user='root',
    callbacks=playbook_cb,
    runner_callbacks=runner_cb,
    stats=stats,
    private_key_file=CONFIG.get("instances", "priv_key_path")
)
results = pb.run()
print results
