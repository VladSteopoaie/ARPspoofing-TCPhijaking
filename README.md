# ARPspoofing-TCPhijaking

## Network structure

```
            MIDDLE------------\
        subnet2: 198.7.0.3     \
        MAC: 02:42:c6:0a:00:02  \
               forwarding        \ 
              /                   \
             /                     \
Poison ARP 198.7.0.1 is-at         Poison ARP 198.7.0.2 is-at 
           02:42:c6:0a:00:02         |         02:42:c6:0a:00:02
           /                         |
          /                          |
         /                           |
        /                            |
    SERVER <---------------------> ROUTER <---------------------> CLIENT
net2: 198.7.0.2                      |                           net1: 172.7.0.2
MAC: 02:42:c6:0a:00:03               |                            MAC eth0: 02:42:ac:0a:00:02
                           subnet1:  172.7.0.1
                           MAC eth0: 02:42:ac:0a:00:01
                           subnet2:  198.7.0.1
                           MAC eth1: 02:42:c6:0a:00:01
                           subnet1 <------> subnet2
                                 forwarding

```

## Installation

### Requirements

- [docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/standalone/)


Getting the repository:
```bash
git clone https://github.com/VladSteopoaie/ARPspoofing-TCPhijaking.git
cd ARPspoofing-TCPhijaking
```

Building the containers (docker might require admin permissions):
```bash
docker-compose up
```

Now you can connect to each container with the following command:
```bash
docker exec -it <container-id> /bin/bash
# to get the container id you can use `docker ps`
```

## Usage

### Scenario I (client-server communication)

Connect to the `client` container and follow the commands:

```bash
cd scripts
python3 tcp_client.py
```

You should see the `client` hanging with the following message:

```
[~] Connecting to ('198.7.0.2', 10000)...
```

Connect to the `server` container and follow the commands:

```bash
cd scripts
python3 tcp_server.py
```

You should see the `server`'s message:

```
[~] Server listening on 198.7.0.2:10000
[~] Waiting for connections...
```

After a short while the `server` and `client` should communicate and you should see something like this:

```
------- SERVER -------
[~] Handshake with ('198.7.0.1', 51902)
[~] Message received: "b'gAFMG`'"
[~] Message sent: "b'gAFMG`-server'"
[~] Message received: "b'`{qEUHmR'"
[~] Message sent: "b'`{qEUHmR-server'"
[~] Message received: "b'RWfBnD'"
[~] Message sent: "b'RWfBnD-server'"

------- CLIENT -------
[~] Handshake with ('198.7.0.2', 10000)
[~] Message sent: "gAFMG`"
[~] Message received: "b'gAFMG`-server'"
[~] Message sent: "`{qEUHmR"
[~] Message received: "b'`{qEUHmR-server'"
[~] Message sent: "RWfBnD"
[~] Message received: "b'RWfBnD-server'"
```

Note: The `client` is generating random strings as messages and the `server` is appending '-server' to the data and sends it back.

### Scenario II (ARP spoofing)

Now that we have the `client` and `server` communicating let's add the `middle`.
Connect to the `middle` container and follow the commands:

```bash
cd scripts
sysctl -w net.ipv4.ip_forward=0 # enables packet forwarding
python3 arp.py 198.7.0.1 198.7.0.2 # Usage: python3 arp.py router_ip victim_ip
```

You should see the following:

```
[*] Default Gateway MAC: 02:42:c6:07:00:01
[*] Victim MAC: 02:42:c6:07:00:02
[~] Started ARP poisoning!
[~] Starting network caputre.
```

Start the `client` and `server` as before and wait until some packets are sent.<br>
Stop all the scripts with CTRL^C repeatedly.<br>
On the `middle` container you should have a file that looks like this `198.7.0.2_caputre.pcap`, check if it has some contents. If the file is not empty then the attack was successful and the middle intercepted the packets. You can use `tcpdump -r <file_name>.pcap` to analyze the packets from the terminal or extract the file on your machine with `docker cp` and analyze it in Wireshark.<br> <br>

Here is the file analyzed with Wireshark:
![Wireshark image](images/wireshark.png)