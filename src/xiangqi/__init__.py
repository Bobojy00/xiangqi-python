"""A small, practical Chinese chess (Xiangqi) library."""

from .board import Board, Color, GameResult, Move, Piece, PieceType
from .engine import Engine
from .notation import fen_to_board, move_from_uci, move_to_uci

__all__ = [
    "Board",
    "Color",
    "Engine",
    "GameResult",
    "Move",
    "Piece",
    "PieceType",
    "fen_to_board",
    "move_from_uci",
    "move_to_uci",
]

__version__ = "0.1.0"

