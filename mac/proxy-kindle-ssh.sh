pkill -f "cloudflared access tcp"
pkill -f "wg-relay-mac"
cloudflared access tcp --hostname my-kindle-ssh-subdomain.example.com --url 127.0.0.1:51821 &
./wg-relay-mac udp2tcp 127.0.0.1:51820 127.0.0.1:51821 &