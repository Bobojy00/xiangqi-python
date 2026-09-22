"""Command-line interface for playing and inspecting Xiangqi positions."""

from __future__ import annotations

import argparse
import sys

from .board import Board, Color, Move
from .engine import Engine


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xiangqi", description="Play and analyze Chinese chess.")
    sub = parser.add_subparsers(dest="command", required=True)
    play = sub.add_parser("play", help="play a local human-vs-AI game")
    play.add_argument("--side", choices=("red", "black"), default="red")
    play.add_argument("--level", choices=("easy", "normal", "hard"), default="normal")
    play.add_argument("--time-limit", type=float, default=2.0)
    analyze = sub.add_parser("analyze", help="show legal moves and the engine suggestion")
    analyze.add_argument("fen", help="quoted Xiangqi FEN")
    analyze.add_argument("--level", choices=("easy", "normal", "hard"), default="normal")
    analyze.add_argument("--time-limit", type=float, default=2.0)
    validate = sub.add_parser("validate", help="validate a Xiangqi FEN")
    validate.add_argument("fen", help="quoted Xiangqi FEN")
    return parser


def _play(args: argparse.Namespace) -> int:
    board = Board.initial()
    engine = Engine(args.level)
    human = Color.RED if args.side == "red" else Color.BLACK
    print(board)
    print("输入走法，例如 h2e2；输入 undo 悔棋，输入 quit 退出。")
    while True:
        result = board.result()
        if result.terminal:
            print(f"对局结束：{result.status}，胜方：{result.winner.value if result.winner else '和棋'}")
            return 0
        if board.side_to_move is human:
            try:
                text = input("你的走法> ").strip()
            except EOFError:
                print()
                return 0
            if text.lower() in {"quit", "exit", "q"}:
                return 0
            if text.lower() == "undo":
                board.undo()
                board.undo()
                print(board)
                continue
            try:
                board.push(Move.from_uci(text))
            except ValueError as exc:
                print(f"无效走法：{exc}")
        else:
            move = engine.choose_move(board, args.time_limit)
            board.push(move)
            print(f"AI 走：{move}")
        print(board)


def _analyze(args: argparse.Namespace) -> int:
    try:
        board = Board.from_fen(args.fen)
    except ValueError as exc:
        print(f"非法 FEN：{exc}", file=sys.stderr)
        return 2
    legal = board.legal_moves()
    print(board)
    print(f"状态：{board.result().status}")
    print(f"合法走法（{len(legal)}）：{' '.join(map(str, legal))}")
    if legal:
        print(f"AI 建议：{Engine(args.level).choose_move(board, args.time_limit)}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    try:
        board = Board.from_fen(args.fen)
        board.legal_moves()
    except (ValueError, IndexError) as exc:
        print(f"非法 FEN：{exc}")
        return 1
    print("FEN 有效")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "play":
        return _play(args)
    if args.command == "analyze":
        return _analyze(args)
    return _validate(args)


if __name__ == "__main__":
    raise SystemExit(main())

