#!/bin/bash

set -ex

source /tmp/.venv2/bin/activate
cd infrared

infrared tripleo-inventory --host $(hostname) --ssh-key /root/.ssh/id_rsa

# Takes 30mins
infrared tripleo-upgrade --undercloud-ffu-os-upgrade yes --upgrade-ffu-workarounds true -e @workarounds.yaml -e leapp_unsubscribed=True -e leapp_skip_release_check=True

# Takes 7mins
infrared tripleo-undercloud -o undercloud-upgrade.yml --upgrade yes --mirror "tlv" --build passed_phase2   --ansible-args="tags=discover_python,upgrade_repos,undercloud_containers" --version 16.1 -e undercloud_version=13

# Takes 46 mins
infrared tripleo-upgrade --undercloud-ffu-upgrade yes --undercloud-ffu-releases '14,15,16.1' --mirror "tlv" --upgrade-ffu-workarounds true -e @workarounds.yaml


infrared ssh undercloud-0 'cat << EOF > /home/stack/overcloud-repos.yaml
parameter_defaults:
  UpgradeInitCommand: |
    sudo yum localinstall -y http://rhos-release.virt.bos.redhat.com/repos/rhos-release/rhos-release-latest.noarch.rpm
    sudo rhos-release -x
    sudo yum clean all
    sudo rhos-release 16.1
EOF'

