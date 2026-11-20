git clone https://git.zx2c4.com/wireguard-go && cd wireguard-go
GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0 go build -ldflags="-s -w" -o wireguard-go