#!/bin/sh

export PYTHONIOENCODING=utf-8
export LANG=zh_CN.UTF-8
export PYTHONPATH=/data/InStock
export LC_CTYPE=zh_CN.UTF-8

# Only persist job configuration, readable by root-owned cron jobs.
/usr/local/bin/python3 - <<'PYENV'
import json
import os
keys = ("db_host", "db_port", "db_user", "db_password", "db_database",
        "EAST_MONEY_COOKIE", "INSTOCK_ALLOW_INSECURE_TDX",
        "PYTHONIOENCODING", "LANG", "PYTHONPATH", "LC_CTYPE")
fd = os.open("/etc/environment", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.fchmod(fd, 0o600)
with os.fdopen(fd, "w") as target:
    for key in keys:
        if key in os.environ:
            target.write(key + "=" + json.dumps(os.environ[key], ensure_ascii=False) + "\n")
PYENV

#启动cron服务。在前台
/usr/sbin/cron -f