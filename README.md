# parentopticon

System for monitoring and limiting child accounts on Linux

# Installation (daemon)

To install on a user account you want to be controlled by parentopticon:

1. Install necessary packages

```
sudo apt install python3-dev python3-virtualenv
```

1. Clone the code

```
sudo mkdir /usr/local/src/parentopticon
sudo chown <adult account> /usr/local/src/parentopticon
cd /usr/local/src
git clone https://github.com/EliRibble/parentopticon parentopticon
```

1. Create a virtualenv for it to run in

```
cd /usr/local/src/parentopticon
python3 -m virtualenv -p python3 ve
source ve/bin/activate[.fish]
pip install -e .
```

1. Create a supervisord service file

```
sudo su <child account>
mkdir -p ~/.local/share/systemd/user
vim ~/.local/share/systemd/user/parentopticon.service
```

With the content

```
[Unit]
Description=Parentopticon Daemon
[Service]
Type=simple
TimeoutStartSec=0
ExecStart=/usr/local/src/parentopticon/ve/bin/python3 /usr/local/src/parentopticon/bin/parentopticond --host http://yourhost:port
[Install]
WantedBy=default.target
```

1. Enable the service

```
sudo su <child account>
systemctl --user enable parentopticon
systemctl --user start parentopticon
```

1. Verify the service is up and running.

```
systemctl --user status parentopticon
journalctl --user
tail ~/.local/share/parentopticon.log
```

# Hacking

```
cd parentopticon
python3 -m venv ve
source ve/bin/activate.fish
pip3 install -e .
```
