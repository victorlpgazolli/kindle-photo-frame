GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0 go build -ldflags="-s -w" -o wg-relay-arm main.go
go build -ldflags="-s -w" -o wg-relay-mac main.go