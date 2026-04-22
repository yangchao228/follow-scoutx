[English coming later] | **中文**

# 谛听.skill

> 听八方一线信号，辨信息轻重真伪，为你生成可持续交付的 AI digest。

**Follow ScoutX** 是 `谛听.skill` 的仓库名与英文识别名。

> 不是再造一套 RSS，也不是堆更多信息源，而是把一线 AI builder 信号、播客长内容和中文优质媒体整理成一个可对话配置、可持续交付的信息系统。

`谛听.skill` 是一个面向 OpenClaw 和 Claude Code 的安装型信息订阅 skill。

它解决的问题很具体：

- AI 相关信息，优先看一手，尤其是国外一线 builder 的原始表达
- 但只看一手不够，中文语境下还需要国内公司、产品落地和行业变化的持续跟踪
- 用户不应该自己维护 RSS、理解抓取链路、配置一堆参数，应该直接通过对话完成订阅

所以这个项目的做法是：

- 从中心化 ScoutX feed 获取候选内容
- 同时提供 `ScoutX 定制优质媒体源` 和 `一手信息源`
- 一手信息源当前包括 `X / Twitter` 和 `播客转写`
- 在本地保存用户偏好，并在执行时实时拉取、筛选、生成 digest

看效果 · 安装 · 第一次设置 · 定时投递 · 工作方式 · 背后的判断

---

## 你会得到什么

安装后，你得到的不是“一个源列表”，而是一份按你偏好持续更新的个性化摘要。

你可以自己决定：

- 看什么：`AI Agent`、`OpenAI / Anthropic / Cursor`、编程工具、模型发布、产品更新
- 看哪些源：`ScoutX 定制优质媒体源`、`一手信息源`，或者两者都看
- 一手信息源看哪些：`X`、`播客`，或者两者都看
- 推送频率：每日或每周
- 摘要语言：中文、英文、双语
- 摘要风格：更短，或更偏分析
- 递送方式：当前聊天，或指定渠道

默认目标不是让用户先想清楚一切，而是先跑起来。你完全可以从这些最小组合开始：

- `只看一手信息源`
- `只看 X，不看播客`
- `ScoutX 优质媒体 + 一手信息源都看`
- `先混合看，后面再切成只看一手或只看媒体`

---

## 为什么这样设计

这个项目的核心判断很简单：AI 信息获取，应该优先接触原始表达，再用经过筛选的中文媒体补齐本地语境。

### 一手信息为什么重要

- `X / Twitter` 更适合跟踪研究员、创始人、产品负责人和工程师的即时表达，能更早看到产品方向、模型更新、内部判断和真实使用反馈
- `播客` 更适合补充长表达，能拿到公开帖子之外的上下文，比如产品取舍、组织判断、研发路径和行业分歧

也就是说，这个项目不想让用户只看“别人怎么转述 AI 圈发生了什么”，而是尽量直接接触一线 builder 的原始表达。

### 为什么还要补中文媒体

很多用户除了想看一手信息，还需要中文世界里对国内公司、产品进展、产业动态和工程落地的持续跟踪，所以项目同时提供 `ScoutX 定制优质媒体源`。

当前公开 feed 已覆盖的国内来源类型包括这些方向（以实际中心 feed 为准）：

- `36氪`：创业公司、产品发布、融资、行业快讯
- `InfoQ 中文`：技术与工程实践、基础设施、开发者工具
- `钛媒体 AGI`：产业和商业分析、公司竞争格局、商业化进展
- `量子位`：前沿产品、模型更新、热点追踪

两层信息源不是互斥关系，而是不同用途：

- 只看一手信息源：适合更重视原始表达、产品信号和前线判断
- 只看 ScoutX 定制优质媒体源：适合更想快速掌握中文行业动态
- 两者都看：适合既想看一线 builder 在说什么，也想补齐国内媒体整理与背景信息

---

## 效果示例

用户真正应该感受到的是“我直接说需求，系统替我把信息结构搭好”。

```text
用户    ❯ 我想每天早上 9 点看 AI Agent 摘要，重点看 OpenAI、Anthropic、Cursor。
         先用中文，尽量短一点。ScoutX 优质媒体和一手信息源都看。

Agent   ❯ 已记录：
         - 频率：每天
         - 时间：09:00
         - 语言：中文
         - 风格：short
         - 信息源：ScoutX + 一手信息源
         - 一手信息源：X + 播客
         - 关注主题：AI Agent
         - 关键词：OpenAI、Anthropic、Cursor

         我现在为你生成第一份预览 digest。
```

```text
用户    ❯ 改一下。不要融资新闻，只看 X，不看播客。

Agent   ❯ 已更新：
         - 排除：融资新闻
         - 一手信息源：仅 X

         其他设置保持不变。
```

这类对话的关键不是“能不能调参数”，而是用户不用理解底层采集、接口地址、JSON 过滤规则，也能完成订阅。

---

## 快速开始

1. 安装这个 skill
2. 对 agent 说 `set up follow scoutx`
3. 按提示回答偏好
4. 立即预览第一份 digest

正常用户不应该被要求手动配置这些内容：

- 服务地址
- API token
- feed endpoint
- JSON 过滤规则

这些都应该被 skill 隐藏。

---

## 安装

### OpenClaw

```bash
clawhub install follow-scoutx
```

如果还没上架，也可以手动安装：

```bash
git clone https://github.com/yangchao228/follow-scoutx.git ~/skills/follow-scoutx
```

### Claude Code

```bash
git clone https://github.com/yangchao228/follow-scoutx.git ~/.claude/skills/follow-scoutx
```

---

## 第一次设置

安装完成后，直接对 agent 说：

```text
set up follow scoutx
```

或者：

```text
/follow-scoutx
```

agent 理想情况下只需要确认这些用户偏好：

- 你想每天还是每周收到摘要
- 你想几点收到
- 你想看 ScoutX 定制优质媒体源、一手信息源，还是都看
- 如果选择一手信息源，你想看 X、播客，还是都看
- 你想看哪些方向
- 你想用中文、英文还是双语
- 你想推送到哪里

你可以直接这么说：

- `我想每天早上 9 点看 AI Agent 摘要`
- `主要关注 OpenAI、Anthropic、Cursor`
- `只看一手信息源`
- `X 和播客都看，不看媒体源`
- `ScoutX 优质媒体源和一手信息源都看`
- `不要融资新闻`
- `中文，尽量短一点`
- `先直接在聊天里显示`

---

## 修改设置

后续继续通过对话修改即可：

- `改成每周一和周四早上推送`
- `只看 OpenAI 和 Anthropic`
- `切到一手信息源`
- `只看 X`
- `切回 ScoutX 定制优质媒体源`
- `一手信息源最多 6 条，ScoutX 优质媒体最多 4 条`
- `把摘要写得更短一点`
- `多关注编程工具`
- `显示我当前的设置`

---

## 命令行能力

这个仓库也提供了本地脚本，方便调试、预览、落盘配置和安装 OpenClaw 定时任务。

常用命令：

```bash
python3 scripts/follow_scoutx.py configure
python3 scripts/follow_scoutx.py show-profile
python3 scripts/follow_scoutx.py preview
python3 scripts/follow_scoutx.py deliver --json
python3 scripts/follow_scoutx.py show-openclaw-cron
python3 scripts/follow_scoutx.py install-openclaw-cron
```

一个典型的配置示例：

```bash
python3 scripts/follow_scoutx.py configure \
  --frequency daily \
  --time 09:00 \
  --language zh-CN \
  --source-types scoutx,x,podcast \
  --delivery-channel in_chat \
  --topics "AI Agent,编程工具" \
  --keywords-include "OpenAI,Anthropic,Cursor" \
  --max-items 10 \
  --max-first-party-items 6 \
  --max-scoutx-items 4 \
  --length short
```

如果你只想看一手信息源：

```bash
python3 scripts/follow_scoutx.py configure \
  --source-mode first_party \
  --topics "AI Agent,模型发布"
```

---

## 本地保存的内容

skill 会把用户偏好和本地状态保存在：

```text
~/.follow_scoutx/
```

常见文件包括：

- `profile.json`：订阅偏好
- `state.json`：本地运行状态
- `prompt_sync_state.json`：本地 prompt 与内置 prompt 的同步状态
- `service.json`：本地 service endpoint override
- `prompts/`：本地 prompt 目录

脚本运行时会自动同步内置 prompt 更新；旧版本会先备份到 `prompts/backups/`。如果你长期定制摘要风格，可以直接编辑这些文件：

- `prompts/digest_intro.md`
- `prompts/summarize_content.md`
- `prompts/summarize_tweets.md`
- `prompts/summarize_podcast.md`
- `prompts/translate.md`

---

## 定时投递

OpenClaw 场景下，`follow_scoutx.py deliver` 只负责把 digest 输出到 stdout；真正的消息投递由 OpenClaw cron 的 `--announce --channel <channel> --to <target>` 完成。

安装前先 dry run：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron
```

确认输出里的 `delivery_diagnostics.stable` 为 `true` 后，再执行：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --apply
```

### 当前聊天的稳定方案

如果目标是“发回当前聊天”，不要依赖 `channel=last`。优先使用 OpenClaw 主会话 system event：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --main-session-system-event
python3 scripts/follow_scoutx.py install-openclaw-cron --main-session-system-event --apply
```

### 飞书的稳定方案

如果目标是飞书，先保存明确的投递目标：

```bash
python3 scripts/follow_scoutx.py configure \
  --delivery-channel feishu \
  --delivery-target "ou_xxx"
```

然后再安装定时任务。

注意两点：

- `--main-session-system-event` 只适用于“发回当前聊天”
- 如果 `delivery.channel=feishu`，安装时必须使用显式 `--channel feishu --to <ou_xxx|oc_xxx>`，不要把 system event 当成飞书投递链路

### 替换已有定时任务

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --replace-existing --apply
```

OpenClaw cron 不按 name 更新。这个命令会先找旧 job id，再删除后重新安装，也会顺手清理旧版本留下的 `follow-scoutx-daily-first-party` / `follow-scoutx-daily-scoutx` 遗留任务。

只有在内部测试并确认当前 OpenClaw 安装能稳定路由 `last` 时，才使用：

```bash
python3 scripts/follow_scoutx.py install-openclaw-cron --apply --allow-channel-last
```

---

## 工作方式

输入到输出的链路是这样的：

1. ScoutX 后端集中采集和清洗内容
2. 一手信息源 feed 提供 X 内容和播客转写内容
3. 中心服务输出只读公共 feed
4. skill 在手动执行或定时任务触发时实时拉取用户选择的 feed
5. skill 根据本地偏好筛选内容
6. agent 把结果组织成易读 digest

也就是说：

- `ScoutX` 提供中心内容源
- `ScoutX 定制优质媒体源` 提供筛过的媒体内容
- `X` 与 `播客` 作为一手信息源，由中心 feed 提供原始帖子和转写文本
- `Follow ScoutX` 负责按用户偏好拉取、筛选和整理
- `OpenClaw` 负责定时触发，并把结果发回当前聊天或飞书
- mixed 模式默认只安装一个 recurring job，digest 内部分区排版；如果内容过长，会在投递前拆成多条连续消息

它不是：

- ScoutX 主动给每个用户推送消息
- skill 自己维护一套独立内容库存

---

## 当前仓库结构

```text
follow-scoutx/
├── SKILL.md
├── AGENT.md
├── CLAUDE.md
├── service.json
├── scripts/
│   └── follow_scoutx.py
├── prompts/
│   ├── digest_intro.md
│   ├── summarize_content.md
│   ├── summarize_tweets.md
│   ├── summarize_podcast.md
│   └── translate.md
└── dist/
```

最关键的文件是：

- `SKILL.md`：skill 行为定义
- `service.json`：中心 feed 配置
- `scripts/follow_scoutx.py`：本地配置、预览、递送、cron 安装入口
- `prompts/*.md`：摘要与翻译 prompt

---

## 作为服务提供方你需要做什么

如果你打算把这个 skill 发给别人用，至少要完成这些事情：

1. 部署一个稳定的中心 ScoutX public feed
2. 如果要提供一手信息源，部署或配置稳定的 X feed 和 podcast feed
3. 把 `service.json` 改成真实中心地址
4. 再把这个 skill 仓库发给外部用户

正常终端用户不应该被要求自己改 `service.json`。如果安装包里的 `service.json` 还是占位地址，那是打包或运维问题，不是用户配置问题。

---

## 背后的判断

这不是一个“多加几个 feed 源”的小工具，而是一个信息获取方式的取舍。

过去很多 AI 信息流产品，默认假设是：

- 用户自己会维护源
- 用户愿意理解订阅结构
- 用户能接受 RSS、抓取、接口、过滤规则这些概念

但大多数真正需要持续获取 AI 一手信息的人，想要的是更简单的东西：

- 直接说“我要看什么”
- 不自己维护一堆源
- 不在底层配置里迷路
- 最终稳定收到一份可读、可用、可继续调整的 digest

Follow ScoutX 想做的，就是把这条链路收口成一个更像产品而不是脚本集合的 skill。

它服务的不是“信息越多越好”，而是“把真正值得跟踪的一线信号和中文上下文，持续交到用户手里”。

---

## 背后的故事

这类项目表面上看是在做“信息订阅”，但我真正想解决的不是订阅本身，而是信息获取方式的问题。

现在很多 AI 信息流，要么太偏热点搬运，要么太偏工具拼装。前者的问题是信息浅、重复高、看完很快失效；后者的问题是普通用户要先学会 RSS、抓取、过滤、自动化，最后还得自己维护一套脆弱系统。

但真正有长期价值的信息获取，不应该是这样。

更合理的路径应该是：

- 先尽量接触一线 builder 的原始表达
- 再用经过筛选的中文媒体补齐国内语境
- 最后把这一切收敛成一个用户几乎不用维护的稳定产品形态

所以 Follow ScoutX 没有把重点放在“让用户自己配置更多源”，而是放在另一件事上：

把信息源选择、偏好保存、定时拉取、摘要整理、递送链路这些复杂度尽量留在系统内部，让用户只需要表达自己的关注方向。

你可以把它理解成一个很克制的判断：

- 不是信息越多越好
- 不是自动化越重越好
- 不是配置越细越专业

而是应该尽量把真正有价值的信息，持续、稳定、低摩擦地交到人手里。

这也是为什么这个项目同时保留了两类源：

- `一手信息源`，解决原始判断和前线信号
- `ScoutX 定制优质媒体源`，解决中文语境和国内动态补充

如果只做前者，很多中文用户会缺上下文；如果只做后者，又容易失去一手信号。两者一起，才更接近一个真正能长期使用的信息系统。

---

## 关于作者

`作者名(全网同名)`：AI生命克劳德

`微信公众号`：AI生命克劳德

![微信公众号二维码](https://images.reai.group/images/2026/04/22/%7B20260422-235508_WMLwQt.jpg)

`小红书`：AI生命克劳德

![小红书二维码](https://images.reai.group/images/2026/04/22/%7B20260422-235508_5JImsn.jpg)

`知乎`：AI生命克劳德

![知乎二维码](https://images.reai.group/images/2026/04/22/%7B20260422-235508_XcD04C.png)

`GITHUB`：

---

## License

本仓库当前使用 [MIT License](LICENSE)。
