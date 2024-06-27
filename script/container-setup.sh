#!/bin/sh

DOJO_DIR=/opt/pwn.college

>> $DOJO_DIR/data/config.env

> $DOJO_DIR/data/.config.env
define () {
    name="$1"
    default="$2"
    re="^${name}=\K.*"
    current="$(env | grep -oP ${re})"
    defined="$(grep -oP ${re} $DOJO_DIR/data/config.env)"
    value="${current:-${defined:-$default}}"
    echo "${name}=${value}" >> $DOJO_DIR/data/.config.env
}
define DOJO_HOST localhost.pwn.college
define DOJO_ENV development
define DOJO_CHALLENGE challenge-granular
define WINDOWS_VM none
define SECRET_KEY $(openssl rand -hex 16)
define DOCKER_PSLR $(openssl rand -hex 16)
define UBUNTU_VERSION 20.04
define INTERNET_FOR_ALL False
define MAIL_SERVER
define MAIL_PORT
define MAIL_USERNAME
define MAIL_PASSWORD
define MAIL_ADDRESS
define ARCH $(dpkg --print-architecture)
define INSTALL_AFL no # needs compilation
define INSTALL_ANGR_MANAGEMENT no
define INSTALL_BURPSUITE no
define INSTALL_BUSYBOX no # needs compilation
define INSTALL_CAPSTONE no
define DEFAULT_INSTALL_SELECTION no # default to not installing tools
define INSTALL_DESKTOP_BASE yes # matches the challenge-mini configuration
define INSTALL_IDA_FREE no # explicitly disable -- only for free dojos

mv $DOJO_DIR/data/.config.env $DOJO_DIR/data/config.env
. $DOJO_DIR/data/config.env

if [ ! -f $DOJO_DIR/data/homes/homefs ]; then
    echo "[+] Creating user home structure."
    mkdir -p $DOJO_DIR/data/homes
    mkdir -p $DOJO_DIR/data/homes/data
    mkdir -p $DOJO_DIR/data/homes/nosuid
    dd if=/dev/zero of=$DOJO_DIR/data/homes/homefs bs=1M count=0 seek=1000
    mkfs.ext4 -O ^has_journal $DOJO_DIR/data/homes/homefs
    mount $DOJO_DIR/data/homes/homefs -o X-mount.mkdir $DOJO_DIR/data/homes/homefs_mount
    rm -rf $DOJO_DIR/data/homes/homefs_mount/lost+found/
    cp -a /etc/skel/. $DOJO_DIR/data/homes/homefs_mount
    chown -R 1000:1000 $DOJO_DIR/data/homes/homefs_mount
    umount $DOJO_DIR/data/homes/homefs_mount
    rm -rf $DOJO_DIR/data/homes/homefs_mount
fi

echo "[+] Creating loopback devices for home mounts. This might take a while."
for i in $(seq 1 4096); do
    if [ -e /dev/loop$i ]; then
        continue
    fi
    mknod /dev/loop$i b 7 $i
    chown --reference=/dev/loop0 /dev/loop$i
    chmod --reference=/dev/loop0 /dev/loop$i
done

if [ ! -d $DOJO_DIR/data/ssh_host_keys ]; then
    mkdir -p $DOJO_DIR/data/ssh_host_keys
    rm /etc/ssh/ssh_host_*_key*
    ssh-keygen -A -m PEM
    for key in $(ls /etc/ssh/ssh_host_*_key*); do
        cp -a $key $DOJO_DIR/data/ssh_host_keys
    done
fi
ssh-keyscan github.com > $DOJO_DIR/data/ssh_host_keys/ssh_known_hosts
for file in $(ls $DOJO_DIR/data/ssh_host_keys/*); do
    cp -a $file /etc/ssh
done

mkdir -p $DOJO_DIR/data/logging

sysctl -w kernel.pty.max=1048576
echo core > /proc/sys/kernel/core_pattern

iptables -N DOCKER-USER
iptables -I DOCKER-USER -i user_network -j DROP
for host in $(cat $DOJO_DIR/user_firewall.allowed); do
    iptables -I DOCKER-USER -i user_network -d $(host $host | awk '{print $NF; exit}') -j ACCEPT
done
iptables -I DOCKER-USER -i user_network -s 10.0.0.0/24 -m conntrack --ctstate NEW -j ACCEPT
iptables -I DOCKER-USER -i user_network -d 10.0.0.0/8 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
