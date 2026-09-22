# 中国象棋 Python 库

这是一个面向棋友和开发者的小型中国象棋开源库，包含规则引擎、FEN、轻量 AI 和命令行人机对战。

项目定位是“实用、好玩、容易读懂和二次开发”，核心运行时不依赖第三方库。

安装：

```bash
pip install -e .
xiangqi play --level normal
```

仓库的 `media/` 目录包含 AI 对战和 Python API 实机演示视频；使用 `requirements-demo.txt` 与 `scripts/create_demo_videos.py` 可以重新生成。

公共入口：

```python
from xiangqi import Board, Engine

board = Board.initial()
board.push("h2e2")
move = Engine("normal").choose_move(board, time_limit=2)
board.push(move)
```

坐标使用 `a0` 到 `i9`，从红方底线向黑方底线编号；因此红方右炮的开局位置是 `h2`。当前版本采用实用标准规则，AI 是轻量 Minimax/Alpha-Beta 引擎，适合教学、脚本、小游戏和规则实验，不替代专业象棋引擎。
