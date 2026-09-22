"""Generate short MP4 demos from real xiangqi library execution.

This is intentionally separate from the zero-dependency core package. Install
requirements-demo.txt, then run:

    python scripts/create_demo_videos.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from xiangqi import Board, Color, Engine
from xiangqi.board import FILES, PieceType, row_col


WIDTH, HEIGHT = 1280, 720
BG = (20, 24, 32)
PANEL = (31, 37, 49)
WOOD = (225, 176, 105)
GRID = (76, 48, 28)
RED = (181, 48, 48)
BLACK = (30, 30, 34)
GOLD = (255, 208, 92)
WHITE = (245, 247, 250)
MUTED = (165, 175, 191)


def font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"]
        if mono
        else [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, fill=WHITE, mono=False) -> None:
    draw.text(xy, value, font=font(size, mono), fill=fill)


def board_frame(board: Board, title: str, subtitle: str, moves: list[str], code: list[str] | None = None) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    text(draw, (42, 24), title, 30, GOLD)
    text(draw, (44, 63), subtitle, 16, MUTED)

    left, top, step, radius = 60, 142, 52, 21
    draw.rectangle((left - 28, top - 28, left + 8 * step + 28, top + 9 * step + 28), fill=WOOD)
    for col in range(9):
        x = left + col * step
        draw.line((x, top, x, top + 9 * step), fill=GRID, width=2)
    for row in range(10):
        y = top + row * step
        draw.line((left, y, left + 8 * step, y), fill=GRID, width=2)
    draw.line((left + 3 * step, top, left + 5 * step, top + 2 * step), fill=GRID, width=2)
    draw.line((left + 5 * step, top, left + 3 * step, top + 2 * step), fill=GRID, width=2)
    draw.line((left + 3 * step, top + 7 * step, left + 5 * step, top + 9 * step), fill=GRID, width=2)
    draw.line((left + 5 * step, top + 7 * step, left + 3 * step, top + 9 * step), fill=GRID, width=2)
    text(draw, (left + 142, top + 4 * step - 11), "楚河                 汉界", 17, GRID)
    for col, file_name in enumerate(FILES):
        text(draw, (left + col * step - 5, top + 9 * step + 34), file_name, 14, MUTED, True)

    for index, piece in enumerate(board.grid):
        if piece is None:
            continue
        row, col = row_col(index)
        cx, cy = left + col * step, top + row * step
        outline = RED if piece.color is Color.RED else BLACK
        fill = (255, 236, 182) if piece.color is Color.RED else (238, 231, 207)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill, outline=outline, width=3)
        glyphs = {
            (Color.RED, PieceType.GENERAL): "帅", (Color.RED, PieceType.ADVISOR): "仕",
            (Color.RED, PieceType.ELEPHANT): "相", (Color.RED, PieceType.HORSE): "马",
            (Color.RED, PieceType.ROOK): "车", (Color.RED, PieceType.CANNON): "炮",
            (Color.RED, PieceType.PAWN): "兵", (Color.BLACK, PieceType.GENERAL): "将",
            (Color.BLACK, PieceType.ADVISOR): "士", (Color.BLACK, PieceType.ELEPHANT): "象",
            (Color.BLACK, PieceType.HORSE): "马", (Color.BLACK, PieceType.ROOK): "车",
            (Color.BLACK, PieceType.CANNON): "炮", (Color.BLACK, PieceType.PAWN): "卒",
        }
        glyph = glyphs[(piece.color, piece.kind)]
        box = draw.textbbox((0, 0), glyph, font=font(25))
        draw.text((cx - (box[2] - box[0]) / 2, cy - (box[3] - box[1]) / 2 - 3), glyph, font=font(25), fill=outline)

    draw.rounded_rectangle((600, 112, 1238, 666), radius=18, fill=PANEL)
    text(draw, (630, 140), "实机运行状态", 22, WHITE)
    text(draw, (630, 180), f"回合：{'红方' if board.side_to_move is Color.RED else '黑方'}", 18, GOLD)
    text(draw, (630, 214), f"FEN：{board.to_fen().split(' w ')[0].split(' b ')[0]}", 13, MUTED, True)
    text(draw, (630, 246), "走法记录", 17, WHITE)
    for idx, move in enumerate(moves[-10:], 1):
        text(draw, (640, 278 + (idx - 1) * 27), move, 16, (221, 228, 240), True)
    if code:
        y = 278
        for line in code:
            text(draw, (640, y), line, 15, (160, 220, 180), True)
            y += 26
    return image


def write_video(path: Path, frames: list[Image.Image], seconds_per_frame: float = 0.65) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fps = 12
    repeat = max(1, round(seconds_per_frame * fps))
    with imageio.get_writer(path, fps=fps, codec="libx264", quality=8, pixelformat="yuv420p") as writer:
        for frame in frames:
            for _ in range(repeat):
                writer.append_data(np.asarray(frame))


def make_ai_match(out_dir: Path) -> Path:
    board = Board.initial()
    engine = Engine("easy")
    frames = [board_frame(board, "XIANGQI · AI MATCH", "真实 Board + Engine 执行 · easy difficulty", [])]
    moves: list[str] = []
    for _ in range(10):
        if board.result().terminal:
            break
        side = "红" if board.side_to_move is Color.RED else "黑"
        move = engine.choose_move(board, time_limit=0.25)
        board.push(move)
        moves.append(f"{len(moves):02d}  {side}方  {move}")
        frames.append(board_frame(board, "XIANGQI · AI MATCH", "真实 Board + Engine 执行 · easy difficulty", moves))
    path = out_dir / "xiangqi-ai-match.mp4"
    write_video(path, frames)
    return path


def make_api_demo(out_dir: Path) -> Path:
    board = Board.initial()
    frames = [board_frame(board, "XIANGQI · PYTHON API", "从代码到可用棋局状态", [], [
        "board = Board.initial()",
        "print(board)",
    ])]
    board.push("h2e2")
    frames.append(board_frame(board, "XIANGQI · PYTHON API", "执行真实走法：红炮 h2e2", ["01  红方  h2e2"], [
        'board.push("h2e2")',
        "print(board.to_fen())",
    ]))
    move = Engine("normal").choose_move(board, time_limit=0.5)
    board.push(move)
    frames.append(board_frame(board, "XIANGQI · PYTHON API", f"AI 返回合法走法：{move}", ["01  红方  h2e2", f"02  黑方  {move}"], [
        'engine = Engine("normal")',
        "move = engine.choose_move(board)",
    ]))
    path = out_dir / "xiangqi-python-api.mp4"
    write_video(path, frames)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("media"))
    args = parser.parse_args()
    for path in (make_ai_match(args.out_dir), make_api_demo(args.out_dir)):
        print(f"created {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

