#!/usr/bin/env python
# -*- coding: utf-8 -*-

import novaclient.client as nova
from novaclient.exceptions import *
import logger
import socket
import time
import os

LOGGER = logger.setup_logger("instances")

def get_nova_client(config=os.environ):
    LOGGER.info("Initializing a new OpenStack client")
    client = nova.Client(2,
        config['OS_USERNAME'],
        config['OS_PASSWORD'],
        project_id=config['OS_TENANT_NAME'],
        auth_url=config['OS_AUTH_URL'],
        region_name=config['OS_REGION_NAME']
    )
    return client

def check_pubkey(name, path, client=None):
    LOGGER.info("Checking for existance of the public key %s", name)
    if not client:
        client = get_nova_client()
    try:
        key = client.keypairs.find(name=name)
        LOGGER.debug("Key %s exists", name)
        with open(path, 'r') as keyfile:
            local_key = keyfile.read()
            if key.public_key != local_key:
                LOGGER.warning("The public key and the local one do not match, replacing !")
                key.delete()
                client.keypairs.create(name, local_key)
    except IOError:
        LOGGER.critical("Could not open file %s", path)
        raise
    except NotFound:
        LOGGER.debug("Key %s does not exist, creating", name)
        try:
            with open(path, 'r') as keyfile:
                local_key = keyfile.read()
                client.keypairs.create(name, local_key)
        except IOError:
            LOGGER.critical("Could not open file %s", path)
            raise

def vm_exists(name, client=None):
    LOGGER.info("Checking for existance of %s", name)
    if not client:
        client = get_nova_client()
    try:
        server = client.servers.find(name=name)
        LOGGER.debug("Instance %s exists", name)
        return server
    except NotFound:
        LOGGER.debug("Instance %s does not exists", name)
        return None

def create_server(name, flavor, image, key, client=None):
    LOGGER.info("Creating instance %s", name)
    if not client:
        client = get_nova_client()
    vm = vm_exists(name, client)
    if vm:
        LOGGER.info("Instance %s already exists, nothing to do", name)
        return (vm, False)
    # The instance does not exist, we must create it
    LOGGER.info("Instance %s does not exist, creating it with flavor %s and image %s",
        name,
        flavor,
        image
    )

    try:
        flavor = client.flavors.find(name=flavor)
        LOGGER.debug("Found flavor %s", flavor)
    except NotFound:
        LOGGER.critical("The flavor %s cound not be found !", flavor)
        raise

    try:
        image = client.images.find(name=image)
        LOGGER.debug("Found image %s", image)
    except NotFound:
        LOGGER.critical("The image %s cound not be found !", image)
        raise

    try:
        client.keypairs.find(name=key)
        LOGGER.debug("Found key %s", key)
    except NotFound:
        LOGGER.critical("The key %s cound not be found !", key)
        raise

    server = client.servers.create(name, image, flavor, key_name=key)
    LOGGER.info("Created new server %s...", server)
    return (server, True)

def wait_for_vm_ip(name, network="Ext-Net", delay=1, client=None):
    LOGGER.info("Waiting for instance %s's IP", name)
    if not client:
        client = get_nova_client()
    address = None
    while not address:
        try:
            vm = client.servers.find(name=name)
            address = vm.networks[network]
        except KeyError:
            time.sleep(delay)
        except Exception as exce:
            LOGGER.error("Got unexpected exception : %s", str(exce))
            time.sleep(delay)
    LOGGER.info("Got %s as an IP for %s on %s", address, name, network)
    return address

def wait_for_vm_ssh(address, timeout=3, delay=1, port=22):
    LOGGER.info("Waiting for instance %s's SSH to come up", address)

    ssh = False
    LOGGER.debug("Trying to connect %s:%d", address, port)
    while not ssh:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((address, port))
            sock.close()
            ssh = True
        except Exception as exce:
            time.sleep(delay)

    LOGGER.info("Got SSH for address %s on port %d", address, port)
