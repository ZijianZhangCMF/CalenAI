#!/bin/bash
# CalenAI 安装脚本
# 运行: bash setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CALENAI_SH="$SCRIPT_DIR/calenai.sh"

echo ""
echo "╔════════════════════════════════════╗"
echo "║        CalenAI 安装向导            ║"
echo "╚════════════════════════════════════╝"
echo ""

# ─── 检查 Python3 ─────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "✗ 未找到 python3，请先安装:"
    echo "  https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
echo "✓ $PYTHON_VER"

# ─── 检查 osascript ───────────────────────────────────────────────────────────
if ! command -v osascript &>/dev/null; then
    echo "✗ 未找到 osascript，此工具仅支持 macOS"
    exit 1
fi
echo "✓ macOS AppleScript 可用"

# ─── 首次配置 ─────────────────────────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo ""
    python3 "$SCRIPT_DIR/calenai.py" --setup
else
    echo "✓ config.json 已存在（如需重新配置请运行: python3 calenai.py --setup）"
fi

# ─── 赋予脚本执行权限 ─────────────────────────────────────────────────────────
chmod +x "$CALENAI_SH"
chmod +x "$SCRIPT_DIR/calenai.py"
echo "✓ 执行权限已设置"

# ─── 写入 ~/.zshrc 别名（可选）───────────────────────────────────────────────
SHELL_RC="$HOME/.zshrc"
[ -n "$BASH_VERSION" ] && SHELL_RC="$HOME/.bashrc"

ALIAS_LINE="alias calenai='python3 $SCRIPT_DIR/calenai.py'"

if grep -q "alias calenai=" "$SHELL_RC" 2>/dev/null; then
    echo "✓ Shell 别名已存在（calenai）"
else
    read -rp "是否添加 'calenai' 命令别名到 $SHELL_RC? [Y/n]: " yn
    if [[ "$yn" != "n" && "$yn" != "N" ]]; then
        echo "" >> "$SHELL_RC"
        echo "# CalenAI" >> "$SHELL_RC"
        echo "$ALIAS_LINE" >> "$SHELL_RC"
        echo "✓ 别名已添加，请运行 'source $SHELL_RC' 生效"
    fi
fi

# ─── 完成 ────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "  安装完成！"
echo ""
echo "  终端使用:"
echo "    python3 $SCRIPT_DIR/calenai.py \"明天下午3点开会\""
echo ""
echo "  快捷指令配置（Shortcuts App）:"
echo "    操作：运行 Shell 脚本"
echo "    Shell: /bin/bash"
echo "    传入输入内容: 作为参数"
echo "    脚本内容:"
echo "      $CALENAI_SH \"\$1\""
echo "════════════════════════════════════"
echo ""
