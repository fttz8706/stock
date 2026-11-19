# 本机部署记录（2026-11-19）

使用 `docker/Dockerfile` 的 Python 3.11 / Debian Bookworm 镜像构建。
`docker/docker-compose.override.yml` 将数据库存储设为命名卷 `instockdb_data`。
Web 仅发布到 `127.0.0.1:9988`，数据库不发布宿主机端口。
凭据保存在本机 `~/.config/instock/instock.env`，不得提交到仓库。

## 构建与启动

在仓库根目录运行：

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose --env-file ~/.config/instock/instock.env -f docker/docker-compose.yml -f docker/docker-compose.override.yml build instock
docker compose --env-file ~/.config/instock/instock.env -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d --no-build
docker compose --env-file ~/.config/instock/instock.env -f docker/docker-compose.yml -f docker/docker-compose.override.yml ps
```

## 已确认的数据源限制

检查时综合选股 4529 条、分红 933 条、龙虎榜 348 条、大宗交易 19 条、涨停原因 26 条。
实时行情列表 `push2.eastmoney.com` 及代码使用的编号子域连接被关闭；
宿主机直连、HTTP 代理、SOCKS 代理均复现。具体是上游限制还是出口策略尚未确定。
东方财富网页、数据中心和历史行情接口可以返回 HTTP 200；这不代表所有接口数据完整。

容器能经 `host.docker.internal:8118` 使用现有宿主机 HTTP 代理，不需要开启 Allow LAN。
本次没有新增代理转发或开放局域网监听，也没有因故障更换数据源。
后续应先确认实时接口恢复，再运行完整任务并检查行情表、指标和策略数据。
若需要 Cookie，请按 `security-fixes.md` 的只读文件挂载方式配置，不提交真实 Cookie。

`run_job` 是一次性任务（`autorestart=false`），正常结束后显示 EXITED；
Web 和 cron 应保持 RUNNING。旧任务会记录部分上游错误后继续，因此退出码 0
或“完成任务”日志不能作为完整采集成功的依据，需结合错误日志和数据库数据检查。
