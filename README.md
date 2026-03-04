# CalenAI

通过自然语言，自动在 macOS 原生日历中创建日程事件。支持所有兼容 OpenAI 格式的 LLM API。

## 功能

- 自然语言解析日程（时k、Moonshot、通义千问、本地 Ollama 等所有兼容接口
间、地点、备注）
- 根据内容自动选择日历（科研 / 工作 / 个人等）
- 支持单次创建多个日程
- 接入 Apple 快捷指令，通过 Siri / 快捷键触发
- 支持 OpenAI、DeepSee
## 快速安装

```bash
git clone https://github.com/ZijianZhangCMF/CalenAI.git
cd CalenAI
bash setup.sh
```

`setup.sh` 会自动：检测 Python 版本、读取你的日历列表、引导配置 API 信息、可选添加 `calenai` 命令别名。

已下载 zip 的用户：解压后进入目录，同样运行 `bash setup.sh`。

## 手动配置

复制模板并编辑：

```bash
cp config.example.json config.json
# 用任意编辑器打开 config.json 填写以下字段
```

```json
{
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4o",
  "default_calendar": "个人",
  "calendars": ["工作", "个人", "学习"],
  "default_alert_minutes": 15
}
```

| 字段 | 说明 |
|------|------|
| `api_url` | API 地址，填到 `/v1` 即可，脚本自动补全路径 |
| `api_key` | 对应平台的 API 密钥 |
| `model` | 模型名称 |
| `default_calendar` | 默认写入的日历（必须是日历 App 中已有的名称） |
| `calendars` | 供 AI 自动分类选择的日历列表（可选） |
| `default_alert_minutes` | 提前提醒分钟数，默认 15 |

> 查看日历名称：打开「日历」App → 左侧边栏。

也可以随时重新运行引导：

```bash
python3 calenai.py --setup
```

## 使用

### 终端

```bash
python3 calenai.py "明天下午3点开会"
python3 calenai.py "周五10点在会议室A评审，下周一全天出差"
python3 calenai.py "3月20日晚上7点聚餐，在外滩18号"
```

### Apple 快捷指令（推荐）

设置完成后可通过 Siri、菜单栏、快捷键一键呼出。

**在「快捷指令」App 中新建快捷指令，依次添加：**

**① 要求输入**
- 提示语：`请描述你的日程`

**② 运行 Shell 脚本**
- Shell：`/bin/bash`
- 传入输入内容：`作为参数`
- 脚本（把路径替换为你的实际路径）：
  ```bash
  /你的路径/CalenAI/calenai.sh "$1"
  ```

**③ 显示通知**
- 标题：`CalenAI`
- 内容：选择「Shell 脚本的结果」

保存命名为 `CalenAI`，在右上角 ℹ️ 中可绑定键盘快捷键。

## 自然语言示例

| 输入 | 效果 |
|------|------|
| 明天下午3点开会 | 明天 15:00–16:00，标题「开会」 |
| 周五10点在3号会议室评审 | 本周五 10:00–11:00，地点「3号会议室」 |
| 后天全天出差 | 后天全天事件 |
| 下周一9点站会，下周三2点分享 | 自动创建两个独立事件 |
| 明晚7点聚餐，在海底捞，记得带礼物 | 地点「海底捞」，备注「记得带礼物」 |

## 兼容的 API

| 服务 | api_url | 推荐模型 |
|------|---------|---------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Moonshot (Kimi) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| Ollama（本地） | `http://localhost:11434/v1` | `qwen2.5` |

## 权限说明

首次运行时 macOS 会弹出「是否允许访问日历」，选择「允许」即可。
若未弹窗但创建失败：**系统设置 → 隐私与安全性 → 日历** 确认权限。

## 文件结构

```
CalenAI/
├── calenai.py          # 主程序
├── calenai.sh          # Shortcuts 调用入口
├── setup.sh            # 安装向导
├── config.json         # 你的配置（本地保存，不会上传）
├── config.example.json # 配置模板
├── .gitignore          # 排除 config.json 等私密文件
└── README.md
```

## License

MIT
