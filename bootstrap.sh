
ssh root@192.168.0.x "mkdir -p /mnt/us/projects/wireguard-go /mnt/us/projects/cloudflared"

scp -C kindle/mnt/us/documents/start_wg.sh root@192.168.0.x:/mnt/us/documents/
scp -C kindle/mnt/us/watch.py root@192.168.0.x:/mnt/us/
scp -C kindle/etc/upstart/*.conf root@192.168.0.x:/tmp/

ssh root@192.168.0.x '
  mntroot rw
  mv /tmp/kindle-*.conf /etc/upstart/
  mntroot ro
  chmod +x /mnt/us/documents/start_wg.sh
'

sh mac/generate-wireguard-go.sh
scp -C ./wireguard-go root@192.168.0.x:/mnt/us/projects/wireguard-go

sh mac/generate-wg-relay.sh
scp -C ./wg-relay-arm root@192.168.0.x:/mnt/us/projects/cloudflared/wg-relay

sh mac/download-cloudflared.sh
scp -C ./cloudflared root@192.168.0.x:/mnt/us/projects/cloudflared/cloudflared

sh mac/setup-tooling.sh

sh mac/setup-wireguard-keys.sh