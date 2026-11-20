WG_PKG=$(curl -s https://dl-cdn.alpinelinux.org/alpine/edge/main/armv7/APKINDEX.tar.gz \
  | tar -xzO APKINDEX \
  | awk -F: '/^P:wireguard-tools-wg$/{found=1} found && /^V:/{print "wireguard-tools-wg-"$2".apk"; exit}')
curl -LO "https://dl-cdn.alpinelinux.org/alpine/edge/main/armv7/${WG_PKG}"

scp -C ./"${WG_PKG}" root@192.168.0.x:/mnt/us/projects/wireguard-go



MUSL_PKG=$(curl -s https://dl-cdn.alpinelinux.org/alpine/edge/main/armv7/APKINDEX.tar.gz \
  | tar -xzO APKINDEX \
  | awk -F: '/^P:musl$/{found=1} found && /^V:/{print "musl-"$2".apk"; exit}')
curl -LO "https://dl-cdn.alpinelinux.org/alpine/edge/main/armv7/${MUSL_PKG}"

scp -C ./"${MUSL_PKG}" root@192.168.0.x:/mnt/us/projects/wireguard-go