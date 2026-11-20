#!/bin/sh
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
echo "kindle_vpn" > /sys/power/wake_lock 2>/dev/null

DIR="/mnt/us/projects/wireguard-go"
mkdir -p /var/tmp/wg-bin /var/run/wireguard

cp "$DIR/wireguard-go" /var/tmp/wg-bin/wireguard-go
cp /mnt/us/projects/cloudflared/wg-relay /var/tmp/wg-bin/wg-relay
chmod +x /var/tmp/wg-bin/wireguard-go /var/tmp/wg-bin/wg-relay

tar -xzf "$DIR/musl-1.2.6-r3.apk" -C /var/tmp/wg-bin
tar -xzf "$DIR/wireguard-tools-wg-1.0.20260223-r0.apk" -C /var/tmp/wg-bin usr/bin/wg

cat << 'WRAP' > /var/tmp/wg-bin/wg-cmd
#!/bin/sh
exec /var/tmp/wg-bin/lib/ld-musl-armhf.so.1 /var/tmp/wg-bin/usr/bin/wg "$@"
WRAP
chmod +x /var/tmp/wg-bin/wg-cmd

if ! ip link show wg0 >/dev/null 2>&1; then
  WG_I_PREFER_BUGGY_USERSPACE_TO_POLISHED_KMOD=1 /var/tmp/wg-bin/wireguard-go wg0
  sleep 1
fi

/var/tmp/wg-bin/wg-cmd set wg0 \
  listen-port 51820 \
  private-key "$DIR/kindle_priv.key" \
  peer "MAC_WIREGUARD_PUBLIC_KEY" \
  allowed-ips 10.66.66.2/32

ip addr add 10.66.66.1/24 dev wg0 2>/dev/null
ip link set up dev wg0

sysctl -w net.ipv4.ip_forward=1 >/dev/null
iptables -C INPUT -i wg0 -j ACCEPT 2>/dev/null || iptables -I INPUT -i wg0 -j ACCEPT
iptables -C INPUT -i wlan0 -p udp --dport 51820 -j ACCEPT 2>/dev/null || iptables -I INPUT -i wlan0 -p udp --dport 51820 -j ACCEPT
iptables -C FORWARD -i wg0 -j ACCEPT 2>/dev/null || iptables -I FORWARD -i wg0 -j ACCEPT
iptables -C FORWARD -o wg0 -j ACCEPT 2>/dev/null || iptables -I FORWARD -o wg0 -j ACCEPT
iptables -t nat -C POSTROUTING -s 10.66.66.0/24 -o wlan0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s 10.66.66.0/24 -o wlan0 -j MASQUERADE

pidof wg-relay >/dev/null 2>&1 || /var/tmp/wg-bin/wg-relay tcp2udp 127.0.0.1:51820 127.0.0.1:51820 >/var/tmp/wg-relay.log 2>&1 &
start sshd 2>/dev/null || /usr/sbin/sshd 2>/dev/null

exit 0
