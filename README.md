# OVH /cloud ansible demo
This project aims at showing how to spawn and configure an OVH/cloud OpenStack
server programatically from python.

It uses exclusively Python.

The VM management is done via the python Openstack bindings, and the configuration
via Ansible.

## Disclaimer
Yes I know I have SSH private keys in `private/`, please regenerate them they are just
here for demo purposes :)

Before using anything, do not forget to `pip install -r requirements.txt`

## Generate /cloud credentials.
You have to login on the OVH panel, go to the /cloud section, then "Project manaagement",
then OpenStack, then add a user. When it is done hit the wrench icon and "Download an Openstack
configuration file", and overwrite the openrc.sh of this project. You are now good to go !

## The scripts !
Several scripts are present here. The main one is
new_instance.py and its role is to spawn and
configure new VMs. It uses functions from the `utils`
module not to overload it.

The general workflow is the following :
`./new_instance.py vm-name`
 * Will check that the Ansible key is registsred in
   OpenStack. And if not create it from the local
   files.
 * Create the VM if it does not exists, following
   the parameters set in `cloud.ini` (flavor and
   shit)
 * Wait for the VM to have an IP address in the
   Ext-Net (Internet) network
 * Generate an Ansible inventory containing only
   this VM
 * Wait for the VM to be SSH accessible
 * Apply Ansible manifests on it.

Note that to run it, you MUST have the OpenStack
configuration variables set in your env. To do
so execute the openrc.sh file given by OVH or
manually set :
 * `OS_USERNAME`
 * `OS_PASSWORD`
 * `OS_TENANT_NAME`
 * `OS_AUTH_URL`
 * `OS_REGION_NAME`

## The Ansible manifests
There are two ansible manifests that will be executed.

### post_create.yml
I don't know if this is portable to other providers
than OVH, but it assumes the following:
 * The only user you will be able to use when the VM
   start is `admin`, he can sudo and everything.
 * You cannot login as root.
 * The `ansible` key will be in `admin`'s home

So the first manifest, `post_create.yml` will fix it:
 * Upgrate the system
 * Remove the annoying `cloud-init` package
 * Install the `ansible` key in `root`'s home

If you want to add more keys, please edit the`group_vars/all` file ;)

## base.yml
This manifest will just install a few packages and
perform some configration to show what ansible can
do. It will install:
 * apt
 * root_user
 * base
 * ssh
 * ntp
 * bash
 * vim
 * tmux
 * pip
 * docker
 * git
