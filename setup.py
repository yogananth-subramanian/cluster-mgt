#!/usr/bin/env python

import argparse
import subprocess
from infrared.core import execute
import getpass
import os
import sys
import yaml


ANSIBLE_SSH = '''
[defaults]
host_key_checking = False
forks = 500
timeout = 30
force_color = 1
retry_files_enabled = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
'''


def construct_beaker_args(beaker_user, beaker_pswd, beaker_node,
                          cleanup=False, centos=None):
    home_dir = os.environ['HOME']
    args = ['infrared', 'beaker']
    args.extend(['-o', '/dev/null'])
    args.extend(['--url', 'https://beaker.engineering.redhat.com'])
    args.extend(['--host-pubkey', home_dir + '/.ssh/id_rsa.pub'])
    args.extend(['--host-privkey', home_dir + '/.ssh/id_rsa'])
    args.extend(['--host-user', 'root'])
    args.extend(['--web-service', 'rest'])
    if centos == '8':
        args.extend(['--image', 'centos-8'])
    elif centos == '7':
        args.extend(['--image', 'centos-7.6'])
    else:
        args.extend(['--image', 'rhel-7.6'])
    args.extend(['--beaker-user', beaker_user])
    args.extend(['--beaker-password', beaker_pswd])
    # Host address of the host to provision as referenced by beaker
    args.extend(['--host-address', beaker_node])
    if cleanup:
        args.extend(['--release', 'yes'])
    return args



def beaker_reprovision_node(beaker_user, beaker_pswd, beaker_node, centos):
    path = os.path.dirname(os.path.realpath(__file__))
    cwd = os.path.join(path, 'infrared')
    # Cleanup node in beaker
    bargs = construct_beaker_args(beaker_user, beaker_pswd, beaker_node,
                                  cleanup=True)

    print("Beaker Provision: Cleaning node: %s" % beaker_node)
    p = subprocess.Popen(bargs, cwd=cwd)
    p.communicate()
    p_status = p.wait()
    if p_status != 0:
        sys.exit(1)

    # Provision the node
    print("Beaker Provision: Setup: %s" % beaker_node)
    bargs = construct_beaker_args(beaker_user, beaker_pswd, beaker_node,
                                  centos=centos)
    p = subprocess.Popen(bargs, cwd=cwd)
    p.communicate()
    p_status = p.wait()
    if p_status != 0:
        sys.exit(1)


def _prepare(beaker_nodes):
    master_node =  beaker_nodes[0]
    print("Using %s as master node..." % master_node)
    with open('ansible.cfg', 'w') as f:
        f.write(ANSIBLE_SSH)

    with open('hosts', 'w') as f:
        f.write('[beaker-node]\n')
        for node in beaker_nodes:
            f.write(node + '\n')
        f.write('\n')
        f.write('[master]\n')
        f.write(master_node)


def setup_node(beaker_nodes, rhosp_version=None, templates_dir=None, rhosp_build=None, rhosp_deploy=False, pool_vars=None):
    _prepare(beaker_nodes)
    extra_vars = {'rhosp_deploy': rhosp_deploy}
    if pool_vars:
        extra_vars.update(pool_vars)
    if rhosp_version:
        extra_vars['rhosp_version'] = rhosp_version
    if templates_dir:
        extra_vars['templates_dir'] = templates_dir
    if rhosp_build:
        extra_vars['rhosp_build'] = rhosp_build
    execute.ansible_playbook('hosts', 'playbooks/node-prep.yaml', extra_vars=extra_vars)

def subscription(beaker_nodes, rhel_subs_user, rhel_subs_pass, rhel_subs_pool):
    if beaker_nodes:
        _prepare(beaker_nodes)
    else:
        print("Enabling Subscription for existing notes on 'hosts' file")

    extra_vars = {}
    extra_vars['rhel_subs_user'] = rhel_subs_user
    extra_vars['rhel_subs_pass'] = rhel_subs_pass
    extra_vars['rhel_subs_pool'] = rhel_subs_pool
    execute.ansible_playbook('hosts', 'playbooks/rhel-subs.yaml', extra_vars=extra_vars)

def get_nodes(beaker_nodes):
    node_list = []
    obj = {}
    if len(beaker_nodes) == 1 and os.path.exists(beaker_nodes[0]):
        with open(beaker_nodes[0]) as f:
            data = f.read()
        obj = yaml.safe_load(data)

        if type(obj) == dict:
            # File content is yaml ouput
            node_list = obj.get('nodes')
        else:
            # File content is only nodes names per line as string
            # dell-r730-044.dsal.lab.eng.rdu2.redhat.com
            # dell-r730-045.dsal.lab.eng.rdu2.redhat.com
            for line in data.split('\n'):
                line = line.strip()
                if line:
                    node_list.append(line)
    else:
        node_list = beaker_nodes

    return node_list, obj.get('vars')

def main(argv):
    parser = argparse.ArgumentParser(
        description='DSAL Machine Reprovision Utility')
    general = parser.add_argument_group('general')
    general.add_argument('-n', '--node',
                         dest='beaker_nodes',
                         default=[],
                         action='append',
                         help='Nodes to be provisioned using Beaker (hostname '
                              'should be resolvable by beaker). Multiple node '
                              'names can be provided [or] a file with list of '
                              'nodes (one per line) can be provided')
    general.add_argument('-u', '--user',
                         dest='beaker_user',
                         help='Beaker Server User Name (without user '
                              'beaker provisioning is skipped')
    general.add_argument('-s', '--subscription',
                         dest='subs',
                         action='store_true',
                         help='Apply RHEL subscription Playbooks')
    general.add_argument('-c', '--centos',
                         dest='centos_version',
                         help='Deploy with CentOS image')

    osp = parser.add_argument_group('osp')
    osp.add_argument('-r', '--rhosp-version',
                     dest='rhosp_version',
                     help='RH OSP Version (without rhosp version '
                          'OpenStack setup is skipped')
    osp.add_argument('-b', '--rhosp-build',
                     dest='rhosp_build',
                     default="passed_phase1",
                     help='RH OSP Build for puddle deployment')
    osp.add_argument('-t', '--templates-dir',
                     dest='templates_dir',
                     default='osp10_ref',
                     help='Templates Directory')
    general.add_argument('-d', '--deploy',
                         dest='rhosp_deploy',
                         action='store_true',
                         help='Start OSP deploy in tmux after node provision')
    general.add_argument('--offload',
                         dest='feature_offload',
                         action='store_true',
                         help='Enable offload deployment')
    args = parser.parse_args(argv)
    if not argv:
        parser.print_help()
        sys.exit(1)

    if not args.beaker_nodes and not os.path.exists('hosts'):
        parser.print_help()
        sys.exit(1)

    if args.centos_version and args.subs:
        print("No subscription for CentOS image: "
              "--centos and --subscription are mutually exclusive")
        sys.exit(1)
    if args.centos_version and args.rhosp_version:
        print("No RHOSP installation with CentOS image: "
              "--centos and --rhosp-version are mutually exclusive")
        sys.exit(1)

    node_list, pool_vars = get_nodes(args.beaker_nodes)
    if args.feature_offload:
        print("Performing offload deployment")
        pool_vars['feature_offload'] = True


    if args.beaker_user and node_list:
        beaker_pswd = getpass.getpass('Enter Beaker Password:')
    if args.subs:
        rhel_subs_pass = getpass.getpass('Enter RHEL Subscription Password:')

    if args.rhosp_version and len(node_list) > 1:
        node_list = [node_list[0]]
        print("Provisioning only master node (%s) for OSP deployment" % node_list)

    if args.beaker_user and node_list:
        for node in node_list:
            beaker_reprovision_node(args.beaker_user, beaker_pswd, node,
                                    args.centos_version)

    setup_node(node_list, args.rhosp_version, args.templates_dir, args.rhosp_build, args.rhosp_deploy, pool_vars)

    if args.subs:
        print("Subscription is not Implemented")

main(sys.argv[1:])
