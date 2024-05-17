I created this tool to make performing MPLS Microsegmentation on VyOS as easy as clicking buttons.

To install this on VyOS:
1. Enter the VyOS shell by typing 'sudo su'
2. Navigate to '/config/scripts' with 'cd /config/scripts'
3. Clone the git repository using 'git clone https://github.com/l0crian1/vyos_ez_microsegmentation.git'
4. Download PIP using 'wget https://bootstrap.pypa.io/get-pip.py'
5. Install PIP using 'python3 ./get-pip.py --break-system-packages'
6. Install Flask using 'python3 -m pip install Flask --break-system-packages'
7. Enable the VyOS API using `set service https api keys id <name of key ID> key <key value>` (ex. `set service https api keys id mykey key 'key'`). You may wish to further secure this using this page: https://docs.vyos.io/en/latest/configuration/service/https.html
8. Navigate to the `/config/scripts/vyos_ez_microsegmentation` folder.
9. Find and update the 'apiKey = 'key'' string towards the top of the ez_microsegmentation.py file to whatever you made your key.
10. Run the script using 'python3 ez_microsegmentation.py'
11. Access the GUI on http://\<IP\>:5001

By default, the script will be listening on all interfaces. You can modify that if desired.

You can set the script to launch when VyOS boots, or just run it when you need to modify your VRFs.

The script will fully manage your route-target imports and nothing can talk to each other until you configure pairings, so if you already have imports configured, don't push the config to VyOS until you've verfied the output shown in the GUI matches what you want/need.


![image](https://github.com/l0crian1/vyos_ez_microsegmentation/assets/143656816/5d14dce2-f0d5-482c-ae3f-3a3142011e89)


```
vyos@vyos# run show ip route vrf Users

VRF Users:
C>* 10.2.105.0/24 is directly connected, dum105, 01:07:05
```

![image](https://github.com/l0crian1/vyos_ez_microsegmentation/assets/143656816/9d415ce8-4740-46dd-ae58-8681e5084d78)

```
vyos@vyos# run show ip route vrf Users

VRF Users:
B>  10.1.101.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 155, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/155, weight 1, 00:00:12
B>  10.1.102.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 161, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/161, weight 1, 00:00:12
B>  10.1.103.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 153, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/153, weight 1, 00:00:12
B>  10.1.104.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 154, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/154, weight 1, 00:00:12
B>  10.1.105.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 156, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/156, weight 1, 00:00:12
B>  10.1.106.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 160, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/160, weight 1, 00:00:12
B>  10.1.107.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 146, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/146, weight 1, 00:00:12
B>  10.1.118.0/24 [200/0] via 10.0.0.1 (vrf default) (recursive), label 157, weight 1, 00:00:12
  *                         via 10.1.2.1, eth0 (vrf default), label implicit-null/157, weight 1, 00:00:12
B>* 10.2.101.0/24 [20/0] is directly connected, dum101 (vrf AD), weight 1, 00:00:12
B>* 10.2.102.0/24 [20/0] is directly connected, dum102 (vrf DNS), weight 1, 00:00:12
B>* 10.2.103.0/24 [20/0] is directly connected, dum103 (vrf DHCP), weight 1, 00:00:10
B>* 10.2.104.0/24 [20/0] is directly connected, dum104 (vrf Printers), weight 1, 00:00:12
C>* 10.2.105.0/24 is directly connected, dum105, 01:08:26
B>* 10.2.106.0/24 [20/0] is directly connected, dum106 (vrf Admins), weight 1, 00:00:09
B>* 10.2.107.0/24 [20/0] is directly connected, dum107 (vrf Proxy), weight 1, 00:00:12
B>* 10.2.118.0/24 [20/0] is directly connected, dum118 (vrf Fileshare), weight 1, 00:00:12
```
