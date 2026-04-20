# Follow ScoutX 定时任务稳定性优化

## Tasks

- [x] 增加 OpenClaw cron 投递诊断，识别 `--channel last` 等不稳定配置。
- [x] 让 `install-openclaw-cron --apply` 默认阻止不稳定的模糊投递，除非显式放行。
- [x] 增加 `--main-session-system-event`，用于当前聊天稳定投递。
- [x] 增加 `--replace-existing`，按 name 查找旧 job 并通过 id 删除后重装。
- [x] 在 dry run / JSON 输出中暴露稳定性诊断，便于安装前排查。
- [x] 同步更新 `SKILL.md`、`README.md`、`AGENT.md`、`CLAUDE.md` 的安装建议。
- [x] 运行基础验证命令。

## Review

- 默认 `in_chat` 会解析成 `channel=last`，现在 dry run 会标记 `stable=false`，直接 apply 会被阻止。
- 显式 `--delivery-channel feishu --delivery-target ou_xxx` 会通过稳定性诊断，并保留 `--session isolated` 作为干净执行环境。
- 当前聊天使用 `--main-session-system-event` 生成 `--session main --system-event`，不再硬编码 target，也不依赖 `last`。
- OpenClaw cron 不按 name 更新；`--replace-existing` 会用 `list --json` 找到生成 job name 对应的 id，再调用 `cron rm <id>`。
- `--allow-channel-last` 只作为已经验证平台能力后的逃生口，不再是默认路径。
