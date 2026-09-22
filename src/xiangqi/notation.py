"""Notation helpers for public API consumers."""

from .board import Board, Move


def move_from_uci(value: str) -> Move:
    return Move.from_uci(value)


def move_to_uci(move: Move) -> str:
    return move.to_uci()


def fen_to_board(fen: str) -> Board:
    return Board.from_fen(fen)

