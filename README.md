# hurricane-sync

There are two scripts automatically run called setup.sh and teardown.sh which can be used for related backup tasks.

The directories listed are an example, but the pattern is source:::destination:::type(local or net). Lines below these entires without the ::: are treated as folders to exclude.

Local is intended for physically connected disks while net is intended for networked solutions like offsite servers or local NAS backups. It works on a Linux\Unix host.

This solution requires python3 and the psutil library to be installed (likely already available on your distro installation). It also due the network calls executed uses sshpass (you will likely have to install), ssh, and rsync.

To use please remove the .example from the files from your local copy and make your changes. You will also need to create a file named password with the password contents for the remote server you wish to rsync to.