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

## 每日股票快照展示

用户选择先恢复每日行情页面后，本机 override 设置 `INSTOCK_DAILY_SNAPSHOT: "1"`。
`/instock/data?table_name=cn_stock_spot` 只读投影 `cn_stock_selection` 中的同名字段，
不写入或覆盖 `cn_stock_spot`，不向指标/策略计算输入缺失快照。
默认日期取快照表最新日期；日期筛选按源数据日期执行，找不到该日期则为空。
页面顶部显示来源和缺失字段；导出文件名带有“东方财富选股快照-含缺失字段”。
接口响应头 `X-InStock-Data-Source` 为 `eastmoney-selection-snapshot`。
成交量跨接口单位未核实，因此留空；其余无同名字段也留空，不填 0 或推算。
将开关改为 "0" 并重新创建 Web 容器，可恢复原行情表展示。
验证时 4529 条，数据日期 2026-11-19；这不表示实时采集、ETF、指标和策略已恢复。

总任务现在统计运行期间 ERROR 日志：存在错误则以非零状态退出。
启动脚本使用 exec 保留 Python 退出码；不会因脚本尾部 echo 掩盖失败。
