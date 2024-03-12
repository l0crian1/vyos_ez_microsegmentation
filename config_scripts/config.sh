#!/bin/vbash
source /opt/vyatta/etc/functions/script-template
configure
source <(/config/scripts/tempConfigFile.py)
commit
