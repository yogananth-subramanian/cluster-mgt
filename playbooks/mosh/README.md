Mosh Configuration on Remote Server
===================================

* Supported only for the remote server, not supported for VMs running inside the server and jump hosts.
* Ensure .ssh/config entry is present and ssh is established to the server

Sample SSH Config file
---------------------
```
Host entry
  Hostname server.example.com
  User root
```

Command to Configure Mosh
-------------------------
```
./configure entry

```

