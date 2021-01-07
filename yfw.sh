#!/bin/bash
#
# vim:ft=sh

############### Variables ###############

############### Functions ###############

############### Main Part ###############

apt intall mariadb-server redis-server

sudo systemctl enable redis-server mariadb
sudo systemctl restart redis-server mariadb

pip install requests beautifulsoup4 pymysql redis progress


