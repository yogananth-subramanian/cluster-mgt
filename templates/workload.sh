#!/bin/bash

set -ex

source $HOME/overcloudrc

# OSP13 Workload Commands
openstack image create rhel --container-format bare --disk-format qcow2 --file rhel.qcow2

openstack keypair create test >test.pem
chmod 600 test.pem

openstack flavor create --vcpus 4 --ram 4096 --disk 40 m1.nano
openstack flavor set m1.nano --property hw:mem_page_size=large --property hw:emulator_threads_policy=isolate --property hw:cpu_policy=dedicated

openstack network create tenant1
openstack subnet create tenant1_subnet --network tenant1 --subnet-range 192.1.1.0/24

tenant1_net=$(openstack network list | awk ' /tenant1/ {print $2;}')
openstack server create --flavor m1.nano --nic net-id=$tenant1_net --image rhel --key-name test  test2

