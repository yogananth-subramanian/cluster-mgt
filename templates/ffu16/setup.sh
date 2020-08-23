#!/bin/bash

set -ex

git clone https://github.com/redhat-openstack/infrared.git
cd infrared
virtualenv /tmp/.venv2
echo "export IR_HOME=`pwd`" >> /tmp/.venv2/bin/activate
source /tmp/.venv2/bin/activate
pip install -U pip
pip install .
pip list --format=columns
cp infrared.cfg.example infrared.cfg
infrared plugin add all

cat << EOF > ansible.cfg
[defaults]
host_key_checking = False
forks = 500
pipelining = True
timeout = 30
force_color = 1
roles_path = infrared/common/roles
library = infrared/common/library
filter_plugins = infrared/common/filter_plugins
callback_plugins = infrared/common/callback_plugins
callback_whitelist = timer,profile_tasks,junit_report

[ssh_connection]
control_path = /tmp/.venv2/%%h-%%r
EOF


infrared plugin remove tripleo-upgrade
infrared plugin add --revision stable/train tripleo-upgrade
if [ -n "" ]; then
    pushd plugins/tripleo-upgrade
    git remote add gerrit https://review.opendev.org/openstack/tripleo-upgrade.git
    for a_patch in
        do
            git review -x $a_patch
        done
    popd
fi

# move neutron-ovs.yaml inclusion location
sudo yum install patch -y
curl -4 https://review.opendev.org/changes/747562/revisions/dd184988862e6d10b127658bcebc4662f232f1cd/patch?download | base64 -d | sudo patch -d $(pwd)/plugins/tripleo-upgrade -p1

# use mv instead of symbolic link to avoid too many levels of symbolic links issue
mkdir -p $(pwd)/plugins/tripleo-upgrade/infrared_plugin/roles/tripleo-upgrade
find $(pwd)/plugins/tripleo-upgrade -maxdepth 1 -mindepth 1 -not -name infrared_plugin -exec mv '{}' $(pwd)/plugins/tripleo-upgrade/infrared_plugin/roles/tripleo-upgrade \;

if [ ! -f workarounds.yaml ]; then
    curl -ko workarounds.yaml https://gitlab.cee.redhat.com/osp16/ffwd2/raw/master/infrared/workarounds/ffwd2_workarounds_unsubscribed.yaml
    sed -i -E 's|(.*rhos-release 16.1.*)-p [A-Za-z0-9_.-]+|\1-p passed_phase2|' workarounds.yaml
    sed -i  's/redhat\.local/localdomain/g' workarounds.yaml
fi

