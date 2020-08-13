INFRARED HYBRID SETUP on DSLA
=============================

Preparation
-----------
```
git clone https://github.com/krsacme/cluster-mgt.git
cd cluster-mgt
./configure
source .venv/bin/activate
```

File Specific to Cluster
------------------------
A cluster specific file has to be created in
* ``pool/`` directory to specifiy the machine details and nic details
* ``files/`` directory to specify the compute node details used in hybird deployemnt (merged with instackenv.json of controller nodes).


Sample Executions
-----------------
```bash
# Re-provision the node and prepare for infrared's hybrid deployment
./setup.py -n dell-r730-031.dsal.lab.eng.rdu2.redhat.com -u skramaja -r 13 -t osp13_ref -b z1

# Re-provision the node only
./setup.py -n dell-r640-001.dsal.lab.eng.rdu2.redhat.com -u skramaja

# CentOS Provision
cp files/centos-7.6.yml infrared/
./setup.py -n dell-r640-001.dsal.lab.eng.rdu2.redhat.com -u skramaja --centos

# Providing the list of nodes using a file
./setup.py -n pool/skramaja -u skramaja

# Providing the list of nodes using a file (first node of the list is selected for hypervisor)
./setup.py -n pool/<user_file> -u skramaja -r 13 -t /home/stack/tht-dpdk/osp13_ref -d

```
