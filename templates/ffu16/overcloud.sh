#!/bin/bash

set -ex

source /tmp/.venv2/bin/activate
cd infrared

# prepare
infrared tripleo-upgrade --deployment-files osp13_ref --overcloud-ffu-upgrade yes --overcloud-ffu-releases '14,15,16.1' --upgrade-floatingip-check no --upgrade-workload no  --upgrade-ffu-workarounds yes -e @workarounds.yaml -e upgrade_prepare_extra_params="/home/stack/overcloud-params.yaml,/home/stack/overcloud-repos.yaml" --ansible-args="skip-tags=ffu_overcloud_run,ffu_overcloud_ceph,ffu_overcloud_converge,ffu_overcloud_post" -e launch_sanity_workload=false

# run
infrared tripleo-upgrade --deployment-files osp13_ref --overcloud-ffu-upgrade yes --overcloud-ffu-releases '14,15,16.1' --upgrade-floatingip-check no --upgrade-workload no  --upgrade-ffu-workarounds yes -e @workarounds.yaml --ansible-args="skip-tags=ffu_overcloud_prepare,ffu_overcloud_ceph,ffu_overcloud_converge,ffu_overcloud_post" -e launch_sanity_workload=false


# converge
infrared tripleo-upgrade --deployment-files osp13_ref --overcloud-ffu-upgrade yes --overcloud-ffu-releases '14,15,16.1' --upgrade-floatingip-check no --upgrade-workload no  --upgrade-ffu-workarounds yes -e @workarounds.yaml --ansible-args="skip-tags=ffu_overcloud_prepare,ffu_overcloud_run,ffu_overcloud_ceph,ffu_overcloud_post" -e launch_sanity_workload=false

