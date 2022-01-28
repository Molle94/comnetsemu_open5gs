#!/bin/bash

export DB_URI="mongodb://localhost/open5gs"

mongod --smallfiles --dbpath /var/lib/mongodb --logpath /open5gs/install/var/log/open5gs/mongodb.log --logRotate reopen --logappend &

sleep 6 && cd /open5gs/webui && npm run dev &

if ! grep "ogstun" /proc/net/dev > /dev/null; then
    ip tuntap add name ogstun mode tun
    ip addr add 10.45.0.1/16 dev ogstun
    ip link set ogstun up
    iptables -t nat -A POSTROUTING -s 10.45.0.1/16 ! -o ogstun -j MASQUERADE
fi

iperf3 -s -D -B 10.45.0.1

./install/bin/open5gs-nrfd & 
sleep 3
./install/bin/open5gs-smfd &
./install/bin/open5gs-amfd & 
./install/bin/open5gs-ausfd &
./install/bin/open5gs-udmd &
./install/bin/open5gs-udrd &
./install/bin/open5gs-pcfd &
./install/bin/open5gs-bsfd &
./install/bin/open5gs-nssfd &
./install/bin/open5gs-upfd
