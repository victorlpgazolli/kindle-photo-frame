
brew install wireguard-tools

wg genkey | tee kindle_priv.key | wg pubkey > kindle_pub.key
chmod 600 kindle_priv.key

scp -C kindle_priv.key root@192.168.0.x:/mnt/us/projects/wireguard-go/kindle_priv.key
ssh root@192.168.0.x "chmod 600 /mnt/us/projects/wireguard-go/kindle_priv.key"

ssh root@192.168.0.x "/var/tmp/wg-bin/wg-cmd pubkey < /mnt/us/projects/wireguard-go/kindle_priv.key" > kindle_pub.key

