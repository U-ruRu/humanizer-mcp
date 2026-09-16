#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR=${1:-$(pwd)}
RELEASE=${2:-$(date -u +%Y%m%dT%H%M%SZ)}
TARGET=/opt/humanizer-mcp/releases/$RELEASE

getent group humanizer-readers >/dev/null || groupadd --system humanizer-readers
id humanizer-mcp >/dev/null 2>&1 || useradd --system --home /nonexistent --shell /usr/sbin/nologin humanizer-mcp
usermod -a -G humanizer-readers humanizer-mcp

# Humanizer stays root-owned; the MCP receives read-only group access.
chgrp -R humanizer-readers /opt/humanizer-ru
chmod -R g+rX /opt/humanizer-ru
find /opt/humanizer-ru -type d -exec chmod g+s {} +

install -d -m 0755 /opt/humanizer-mcp/releases
install -d -m 0700 -o humanizer-mcp -g humanizer-mcp /var/lib/humanizer-mcp
install -d -m 0750 -o root -g humanizer-mcp /etc/humanizer-mcp
install -d -m 0755 "$TARGET"
rsync -a --delete --exclude .git --exclude .venv "$SOURCE_DIR/" "$TARGET/"
python3 -m venv "$TARGET/.venv"
"$TARGET/.venv/bin/pip" install -q "$TARGET"
chown -R root:root "$TARGET"
ln -sfn "$TARGET" /opt/humanizer-mcp/current.new
mv -Tf /opt/humanizer-mcp/current.new /opt/humanizer-mcp/current
install -m 0644 "$TARGET/deploy/humanizer-mcp.service" /etc/systemd/system/humanizer-mcp.service
systemctl daemon-reload
