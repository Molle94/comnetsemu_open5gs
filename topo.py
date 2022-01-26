#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About: Simple networkwork topology with one host running the 5GC (Cp and UP),
another host is running the GNB, and the last one the UE.
"""

import time
import argparse

from comnetsemu.cli import CLI, spawnXtermDocker
from comnetsemu.net import Containernet, VNFManager
from comnetsemu.clean import cleanup
from mininet.log import error, info, setLogLevel
from mininet.link import TCLink
from mininet.node import Controller


def getTopo(interactive):
    bind_dir = "/home/vagrant"
    parent_dir = "/home/vagrant/comnetsemu/comnetsemu_open5gs"

    net = Containernet(controller=Controller, link=TCLink)
    
    try:
        info("*** adding 5GC\n")
        core = net.addDockerHost("5gc",
                                dimage="open5gs",
                                ip="192.168.0.111/24",
                                docker_args={
                                    "ports": { "3000/tcp": 3000 },
                                    "volumes": {
                                        parent_dir + "/open5gs/open5gs/src": {
                                            "bind": "/open5gs/src",
                                            "mode": "rw",
                                        },
                                        parent_dir + "/open5gs/open5gs/lib": {
                                            "bind": "/open5gs/lib",
                                            "mode": "rw",
                                        },
                                        bind_dir + "/log" : {
                                            "bind": "/open5gs/install/var/log/open5gs",
                                            "mode": "rw",
                                        },
                                        bind_dir + "/mongodbdata": {
                                            "bind": "/var/lib/mongodb",
                                            "mode": "rw",
                                        },
                                        parent_dir + "/open5gs/config": {
                                            "bind": "/open5gs/install/etc/open5gs",
                                            "mode": "rw",
                                        },
                                        "/etc/timezone": {
                                            "bind": "/etc/timezone",
                                            "mode": "ro",
                                        },
                                        "/etc/localtime": {
                                            "bind": "/etc/localtime",
                                            "mode": "ro",
                                        },
                                    },
                                    "cap_add": ["NET_ADMIN"],
                                    "sysctls": {"net.ipv4.ip_forward": 1},
                                    "devices": "/dev/net/tun:/dev/net/tun:rwm"
                                })

        # info("*** adding UPF\n")
        # upf = net.addDockerHost("upf",
                                # dimage="open5gs",
                                # ip="192.168.0.112/24",
                                # docker_args={
                                    # "volumes": {
                                        # bind_dir + "/log" : {
                                            # "bind": "/open5gs/install/var/log/open5gs",
                                            # "mode": "rw",
                                        # },
                                        # parent_dir + "/open5gs/config": {
                                            # "bind": "/open5gs/install/etc/open5gs",
                                            # "mode": "rw",
                                        # },
                                        # "/etc/timezone": {
                                            # "bind": "/etc/timezone",
                                            # "mode": "ro",
                                        # },
                                        # "/etc/localtime": {
                                            # "bind": "/etc/localtime",
                                            # "mode": "ro",
                                        # },
                                    # },
                                    # "cap_add": ["NET_ADMIN"],
                                    # "sysctls": {"net.ipv4.ip_forward": 1},
                                    # "devices": "/dev/net/tun:/dev/net/tun:rwm"
                                # })

        info("*** adding gNB\n")
        gnb = net.addDockerHost("gnb",
                                dimage="ueransim",
                                ip="192.168.0.131/24",
                                docker_args={
                                    "volumes": {
                                        parent_dir + "/ueransim/config": {
                                            "bind": "/mnt/ueransim",
                                            "mode": "rw",
                                        },
                                        bind_dir + "/log": {
                                            "bind": "/mnt/log",
                                            "mode": "rw",
                                        },
                                        "/etc/timezone": {
                                            "bind": "/etc/timezone",
                                            "mode": "ro",
                                        },
                                        "/etc/localtime": {
                                            "bind": "/etc/localtime",
                                            "mode": "ro",
                                        },
                                        "/dev": {"bind": "/dev", "mode": "rw"},
                                    },
                                    "cap_add": ["NET_ADMIN"],
                                    "devices": "/dev/net/tun:/dev/net/tun:rwm"
                                })

        info ("*** adding UE\n")
        ue = net.addDockerHost("ue",
                                dimage="ueransim",
                                ip="192.168.0.132/24",
                                docker_args={
                                    "volumes": {
                                        parent_dir + "/ueransim/config": {
                                            "bind": "/mnt/ueransim",
                                            "mode": "rw",
                                        },
                                        bind_dir + "/log": {
                                            "bind": "/mnt/log",
                                            "mode": "rw",
                                        },
                                        "/etc/timezone": {
                                            "bind": "/etc/timezone",
                                            "mode": "ro",
                                        },
                                        "/etc/localtime": {
                                            "bind": "/etc/localtime",
                                            "mode": "ro",
                                        },
                                        "/dev": {"bind": "/dev", "mode": "rw"},
                                    },
                                    "cap_add": ["NET_ADMIN"],
                                    "devices": "/dev/net/tun:/dev/net/tun:rwm"
                                })

        info("*** adding controller\n")
        net.addController("c0")

        info("*** adding switches\n")
        s1 = net.addSwitch("s1")
        # s2 = net.addSwitch("s2")

        info("*** adding links\n")
        # net.addLink(s1, s2,bw=1000, delay="10ms", intfName1="s1-s2", intfName2="s2-s1")

        net.addLink(ue, s1, bw=1000, delay="1ms", intfName1="ue1-s1", intfName2="s1-ue1")
        net.addLink(gnb, s1, bw=1000, delay="1ms", intfName1="gnb1-s1", intfName2="s1-gnb1")
        net.addLink(core, s1, bw=1000, delay="1ms", intfName1="core1-s1", intfName2="s1-core1")

        # net.addLink(core, s2, bw=1000, delay="1ms", inftName1="core1-s2", intfName2="s2-core1")
        # net.addLink(upf, s2, bw=1000, delay="1ms", intfName1="upf1-s2", intfName2="s2-upf1")

        info("*** starting network")
        net.start()
        net.pingAll()

        if interactive:
            spawnXtermDocker("5gc")
            spawnXtermDocker("gnb")
            spawnXtermDocker("ue")

            CLI(net)
        else:
            info("*** booting 5G core\n")
            core.sendCmd("./install/etc/open5gs/start_open5gs.sh")
            time.sleep(10)
    
            info("*** starting gNB\n")
            gnb.sendCmd("./nr-gnb -c /mnt/ueransim/open5gs-gnb.yaml")
            time.sleep(2)
    
            info("*** connecting UE\n")
            ue.sendCmd("./nr-ue -c /mnt/ueransim/open5gs-ue.yaml")
            spawnXtermDocker("ue")
            time.sleep(1)

            input("Emulation setup ready. Press enter to terminate ")


    except Exception as e:
        error("*** emulation has errors: ")
        error(e, "\n")
        net.stop()

    except KeyboardInterrupt:
        info("*** aborted, stopping network\n")
        net.stop()

    finally:
        info("*** stopping network\n")
        if interactive:
            net.stop()
        cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i",
                        default=False,
                        const=True,
                        type=bool,
                        nargs="?",
                        help="Run setup interactively with xterms")
    parser.add_argument("-d",
                        default=False,
                        const=True,
                        type=bool,
                        nargs="?",
                        help="Set log level to debug")

    args = parser.parse_args()

    if args.d:
        setLogLevel("debug")
    else:
        setLogLevel("info")

    getTopo(args.i)
