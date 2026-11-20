# Kindle Digital Photo Frame

Transforms an **11th Gen Kindle (MT8110)** into an automated, always-on digital photo frame with a custom 3D-printed enclosure, on-demand grayscale image processing, and persistent remote SSH access over WireGuard and Cloudflare Tunnel for maintenance.

PHOTO_HERE


## Context

This project turns a jailbroken Kindle into a dedicated E-Ink display frame:

* **3D-Printed Enclosure:** [Custom `.stl` models](3d_print) provide a physical frame and stand tailored to the Kindle 11th Gen chassis.
* **On-Demand Image Processing (`watch.py`):** Monitors a local sync folder on the Kindle for incoming photos (HEIC, JPEG, PNG). When a new image arrives, it sends the file to an external processing API via the `/process` endpoint, receives a resized, auto-oriented `1072x1448` grayscale image, and cycles the Kindle's power/screensaver state to refresh the display immediately.
* **Persistent Remote Access (`wireguard-go` + `wg-relay` + `cloudflared`):** Establishes a bidirectional WireGuard VPN tunnel over a Cloudflare Tunnel (framing UDP packets over TCP via a lightweight Go relay) so you can SSH into the device (`10.66.66.1`) from any network behind NAT/CGNAT, while holding a kernel `wake_lock` to keep Wi-Fi active during screensaver mode.

---

## Prerequisites

* **Hardware:**
  * Jailbroken 11th Gen Kindle (MT8110) with USBNet/Wi-Fi SSH access and `mntroot` available.
  * FDM 3D printer (PLA filament) to print the enclosure `.stl` files.
* **Host / Client (macOS):**
  * Go (`>= 1.21`)
  * `cloudflared` (`brew install cloudflared`)
  * `openssl`
  * Official **WireGuard** desktop client
* **Infrastructure:**
  * A **Cloudflare Zero Trust Tunnel** routing a Public Hostname (e.g., `ssh-into-kindle.example.com`) to `tcp://localhost:51820`.
  * An image processing server exposing the `POST /process` endpoint that receives HEIC, JPEG, or PNG images and returns `1072x1448` grayscale PNGs.

---

## Install & Setup

### 1. Print the Enclosure

Slice and print the `.stl` files included in the repository using standard PLA settings.

### 2. Turn on your Kindle and Run Setup Scripts

```bash
sh ./bootstrap.sh
```