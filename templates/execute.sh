#!/bin/bash

set -ex

cd /root/infrared

virtualenv /tmp/.venv
echo "export IR_HOME=`pwd`" >> /tmp/.venv/bin/activate
source /tmp/.venv/bin/activate
pip install -U pip
pip install .
pip list --format=columns
cp infrared.cfg.example infrared.cfg
if [ -d /root/.infrared ]; then
  rm -rf /root/.infrared
fi
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
control_path = /tmp/.venv/%%h-%%r
EOF

bash deploy.sh

#if [ -f $HOME/workload.sh ]; then
#  scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $HOME/workload.sh stack@undercloud-0:~/
#  infrared ssh undercloud-0 "bash workload.sh"
#fi

# FFU
cd /root/ffu16
bash setup.sh
bash undercloud.sh
bash overcloud.sh

# keep the tmux open
sleep infinity
