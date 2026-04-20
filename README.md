[English coming later] | **中文**

# Follow ScoutX

一个参考 `follow-good-builders` 使用方式的安装型 skill。

它的目标不是让用户自己维护 RSS、配置后端参数或理解采集系统，而是：

- 在 OpenClaw 或 Claude Code 中安装 skill
- 通过对话配置“看什么、什么时候推、用什么语言、推到哪里”
- 从中心化 ScoutX feed 获取候选内容
- 可选择 ScoutX 定制优质媒体源，或一手信息源（X 平台与播客）
- 在本地根据用户偏好生成个性化 digest

## 你会得到什么

安装后，你可以得到一份持续更新的个性化信息摘要，内容方向由你自己决定，例如：

- AI Agent
- OpenAI / Anthropic / Cursor
- 编程工具
- 模型发布
- 产品更新

你可以设置：

- 信息源：ScoutX 定制优质媒体源、一手信息源，或两者都看
- 一手信息源类型：X 平台、播客，或两者都看
- 推送条数：混合源默认一手信息源和 ScoutX 优质自媒体各占一半，也可以分别设置上限
- 每日或每周推送
- 中文、英文或双语
- 在聊天中显示，或推送到指定渠道
- 更简短或更偏分析的摘要风格

## 快速开始

1. 安装这个 skill 到你的 agent
2. 对 agent 说 `set up follow scoutx`
3. 按对话提示回答你的偏好
4. 立即预览第一份 digest

你不应该被要求手动配置：

- 服务地址
- API token
- JSON 过滤规则

这些细节都应该被 skill 隐藏。

## 安装

### OpenClaw

```bash
clawhub install follow-scoutx
```

如果没有上架，也可以手动安装：

```bash
git clone https://github.com/yangchao228/follow-scoutx.git ~/skills/follow-scoutx
```

### Claude Code

```bash
git clone https://github.com/yangchao228/follow-scoutx.git ~/.claude/skills/follow-scoutx
```

## 第一次设置

安装完成后，直接对 agent 说：

```text
set up follow scoutx
```

或者：

```text
/follow-scoutx
```

agent 应该只问你这些问题：

- 你想每天还是每周收到摘要
- 你想几点收到
- 你想看 ScoutX 定制优质媒体源、一手信息源，还是都看
- 如果选择一手信息源，你想看 X 平台、播客，还是都看
- 你想看哪些方向
- 你想用中文、英文还是双语
- 你想推送到哪里

例如你可以直接说：

- `我想每天早上 9 点看 AI Agent 摘要`
- `主要关注 OpenAI、Anthropic、Cursor`
- `只看一手信息源`
- `X 和播客都看，不看媒体源`
- `ScoutX 优质媒体源和一手信息源都看`
- `不要融资新闻`
- `中文，尽量短一点`
- `先直接在聊天里显示`

## 修改设置

后续继续通过对话修改即可：

- `改成每周一和周四早上推送`
- `只看 OpenAI 和 Anthropic`
- `切到一手信息源`
- `只看 X 平台`
- `切回 ScoutX 定制优质媒体源`
- `一手信息源最多 6 条，ScoutX 优质自媒体最多 4 条`
- `把摘要写得更短一点`
- `多关注编程工具`
- `显示我当前的设置`

## 本地保存的内容

skill 会把用户偏好保存在本地：

```text
~/.follow_scoutx/
```

常见文件包括：

- `profile.json`
- `state.json`
- `prompts/`

其中：

- `profile.json` 保存订阅偏好
- `state.json` 保存本地运行状态
- `prompts/` 用于长期调整摘要风格

## 高级用户

如果你是高级用户，可以直接编辑：

- `prompts/digest_intro.md`
- `prompts/summarize_content.md`
- `prompts/translate.md`

来改变摘要的格式、语气和翻译方式。

## 工作方式

1. ScoutX 后端集中采集和清洗内容
2. 一手信息源 feed 集中提供 X 平台内容和播客转写内容
3. 中心服务输出只读公共 feed
4. skill 在手动执行或定时任务触发时实时拉取用户选择的 feed
5. skill 根据本地偏好筛选内容
6. agent 将结果组织成易读 digest

也就是说：

- `ScoutX` 提供中心内容源
- `ScoutX 定制优质媒体源` 提供已筛过的媒体内容
- `X 平台` 与 `播客` 作为一手信息源，由中心 feed 提供原始帖子和转写文本
- `Follow ScoutX` 负责按时拉取用户选择的信息源、筛选和整理
- `OpenClaw` 负责定时触发，并把结果通过明确配置的 channel/target 发回当前聊天或飞书
- 如果同时订阅一手信息源和 ScoutX 优质自媒体，OpenClaw recurring delivery 会拆成两次推送，避免两类内容混在同一条消息里

它不是：

- ScoutX 主动给每个用户推送消息
- skill 自己维护一套独立内容库存

OpenClaw 场景下，`follow_scoutx.py deliver` 只负责把 digest 输出到 stdout；真正的飞书发送由 OpenClaw cron 的 `--announce --channel feishu --to <target>` 完成。不要把飞书定时任务配置成 `delivery.mode=session` + `sessionTarget=isolated`，因为 isolated session 没有可继承的当前聊天通道。

为了让定时任务稳定，安装前先 dry run：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron
```

确认输出里的 `delivery_diagnostics.stable` 为 `true` 后，再执行：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --apply
```

如果诊断显示投递目标解析成 `channel=last`，默认不会直接安装。默认稳定方案是先保存明确的飞书投递目标，例如：

```bash
python3 scripts/follow_scoutx.py configure \
  --delivery-channel feishu \
  --delivery-target "ou_xxx"
```

如果目标是当前聊天，而不是飞书 open_id / chat_id，不要依赖 `channel=last`。使用 OpenClaw 的主会话 system event 路径：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --main-session-system-event
python3 scripts/follow_scoutx.py install-openclaw-cron --main-session-system-event --apply
```

只有在内部测试并确认当前 OpenClaw 安装能稳定路由 `last` 时，才使用 `install-openclaw-cron --apply --allow-channel-last`。

如果需要替换已有定时任务，OpenClaw cron 不按 name 更新。可以用：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --replace-existing --apply
```

它会先执行 `openclaw cron list --json`，按生成的 job name 找到 id，再用 `openclaw cron rm <id>` 删除后重新安装。也可以手动执行这两步。

## 当前仓库结构

最关键的文件有：

- `SKILL.md`
- `service.json`
- `scripts/follow_scoutx.py`
- `prompts/*.md`

## 作为服务提供方你需要做什么

如果你打算把这个 skill 发给别人用，你至少需要：

1. 部署一个稳定的中心 ScoutX public feed
2. 如果要提供一手信息源，部署或配置稳定的 X feed 和 podcast feed
3. 把 `service.json` 改成你的真实中心地址
4. 再把这个 skill 仓库发给外部用户

## 相关文件

- `SKILL.md`
- `service.json`
- `scripts/follow_scoutx.py`

## License

按你的实际仓库策略决定。
