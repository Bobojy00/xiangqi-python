# xiangqi-python

一个标准库优先、可复用且带命令行对弈的中国象棋（Xiangqi）Python 库。

`xiangqi-python` 适合棋友直接玩，也适合开发者把棋盘、规则和轻量 AI 集成到自己的项目中。

## Features

- 完整 9×10 棋盘与七类棋子走法
- 将军、将死、困毙、飞将和实用重复/长将判定
- FEN 读取与输出
- `push` / `undo` 和合法走法生成
- 标准库实现的 Minimax + Alpha-Beta AI
- `easy`、`normal`、`hard` 三档难度
- 无第三方运行依赖
- Python 3.11+

## Install

```bash
pip install -e .
```

## Quick start

```python
from xiangqi import Board, Engine

board = Board.initial()
print(board)

board.push("h2e2")
engine = Engine(level="normal")
ai_move = engine.choose_move(board, time_limit=2.0)
board.push(ai_move)
print(board.to_fen())
```

坐标采用 `a0` 到 `i9`：文件从左到右，行号从红方底线的 `0` 到黑方底线的 `9`；因此红方右炮的开局位置是 `h2`。

## CLI

```bash
xiangqi play
xiangqi play --side black --level hard
xiangqi analyze "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
xiangqi validate "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
```

## Architecture

- `xiangqi.board`: 棋盘、棋子、走法和规则判定
- `xiangqi.notation`: FEN 与走法转换
- `xiangqi.engine`: 轻量 AI
- `xiangqi.cli`: 命令行入口

AI 的目标是启动快、可玩、容易阅读和扩展，不与专业引擎的棋力竞争。

## Development

```bash
python -m pytest
python -m xiangqi validate "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
```

详细中文说明见仓库后续文档和源码中的类型注释。

## License

MIT
