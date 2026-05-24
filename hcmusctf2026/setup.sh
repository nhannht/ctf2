#!/usr/bin/env bash
#
# HCMUS-CTF 2026 toolkit installer - Manjaro / Arch native.
# Idempotent: all package steps use --needed; safe to re-run.
#
# Usage:  bash setup.sh
# Needs:  an AUR helper (yay or paru) for the AUR section.
#
set -u

echo "==> HCMUS-CTF 2026 toolkit - Manjaro/Arch"

# --- 1. Official repos (pacman) -------------------------------------------
echo "==> pacman packages"
sudo pacman -S --needed --noconfirm \
  wireshark-qt binwalk foremost perl-image-exiftool audacity \
  gdb radare2 nmap sqlmap john hashcat \
  sagemath python-gmpy2 python-pycryptodome python-numpy \
  python-pytorch python-pipx docker ffuf \
  distrobox podman

# --- 2. AUR (yay or paru) -------------------------------------------------
AUR=""
command -v yay  >/dev/null 2>&1 && AUR="yay"
command -v paru >/dev/null 2>&1 && AUR="paru"

if [ -n "$AUR" ]; then
  echo "==> AUR packages via $AUR"
  "$AUR" -S --needed --noconfirm \
    ghidra jadx avaloniailspy autopsy \
    pwndbg ropgadget-git rsactftool
else
  echo "!! No AUR helper found. Install yay or paru, then run:"
  echo "   yay -S --needed ghidra jadx avaloniailspy autopsy pwndbg ropgadget-git rsactftool"
fi

# --- 3. pipx: isolated Python CLI tools -----------------------------------
echo "==> pipx tools"
pipx install pwntools     2>/dev/null || pipx upgrade pwntools
pipx install volatility3  2>/dev/null || pipx upgrade volatility3

# --- 4. Ruby gems: stego + pwn helpers ------------------------------------
if command -v gem >/dev/null 2>&1; then
  echo "==> ruby gems"
  gem install --user-install zsteg one_gadget
else
  echo "!! ruby not found - skipping zsteg / one_gadget (pacman -S ruby)"
fi

# --- 5. Notes -------------------------------------------------------------
cat <<'EOF'

==> Done. Manual follow-ups:
  - Add yourself to the wireshark group:  sudo usermod -aG wireshark $USER
  - Enable docker:                        sudo systemctl enable --now docker
  - Isolation container for untrusted CTF binaries:
        distrobox create --name ctf --image archlinux:latest
        distrobox enter ctf
  - GEF (alternative to pwndbg):
        bash -c "$(curl -fsSL https://gef.blah.cat/sh)"
  - .NET reversing on Linux uses avaloniailspy (ILSpy); dnSpy is Windows-only.
  - Run CyberChef locally; do not paste challenge data into the public instance.
EOF
