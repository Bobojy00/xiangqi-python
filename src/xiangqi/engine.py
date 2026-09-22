"""A dependency-free, intentionally lightweight Xiangqi engine."""

from __future__ import annotations

import time

from .board import Board, Color, Move, PIECE_VALUES, PieceType, row_col


class SearchTimeout(Exception):
    pass


class Engine:
    """Minimax/Alpha-Beta engine with three friendly strength levels."""

    DEPTHS = {"easy": 1, "normal": 2, "hard": 3}

    def __init__(self, level: str = "normal") -> None:
        if level not in self.DEPTHS:
            raise ValueError("level must be easy, normal, or hard")
        self.level = level
        self._deadline = 0.0
        self._table: dict[tuple[tuple[str | None, ...], int], int] = {}
        self.nodes = 0

    def choose_move(self, board: Board, time_limit: float | None = None) -> Move:
        legal = board.legal_moves()
        if not legal:
            raise ValueError("position has no legal moves")
        self.nodes = 0
        self._table.clear()
        self._deadline = time.monotonic() + time_limit if time_limit is not None else float("inf")
        best = self._order_moves(board, legal)[0]
        target_depth = self.DEPTHS[self.level]
        for depth in range(1, target_depth + 1):
            try:
                score, candidate = self._root_search(board, depth)
                if candidate is not None:
                    best = candidate
            except SearchTimeout:
                break
        return best

    def _root_search(self, board: Board, depth: int) -> tuple[int, Move | None]:
        best_score = -10**9
        best_move: Move | None = None
        alpha, beta = -10**9, 10**9
        for move in self._order_moves(board, board.legal_moves()):
            self._check_time()
            board.push(move)
            try:
                score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            finally:
                board.undo()
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, score)
        return best_score, best_move

    def _negamax(self, board: Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        self._check_time()
        self.nodes += 1
        key = (board.position_key(), depth)
        if key in self._table:
            return self._table[key]
        moves = board.legal_moves()
        if not moves:
            score = -900_000 + ply if board.is_in_check(board.side_to_move) else 0
            return score
        if depth == 0:
            score = self._evaluate(board, board.side_to_move)
            self._table[key] = score
            return score
        best = -10**9
        for move in self._order_moves(board, moves):
            board.push(move)
            try:
                score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            finally:
                board.undo()
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        self._table[key] = best
        return best

    def _evaluate(self, board: Board, perspective: Color) -> int:
        score = 0
        for index, piece in enumerate(board.grid):
            if piece is None:
                continue
            row, _ = row_col(index)
            value = PIECE_VALUES[piece.kind]
            if piece.kind is PieceType.PAWN:
                progress = (6 - row) if piece.color is Color.RED else (row - 3)
                value += max(0, progress) * 8
                if (piece.color is Color.RED and row <= 4) or (piece.color is Color.BLACK and row >= 5):
                    value += 25
            score += value if piece.color is Color.RED else -value
        score += (len(board.legal_moves(Color.RED)) - len(board.legal_moves(Color.BLACK))) * 2
        return score if perspective is Color.RED else -score

    def _order_moves(self, board: Board, moves: list[Move]) -> list[Move]:
        def priority(move: Move) -> int:
            target = board.grid[move.to_sq]
            source = board.grid[move.from_sq]
            capture = PIECE_VALUES[target.kind] if target else 0
            source_value = PIECE_VALUES[source.kind] if source else 0
            return capture * 10 - source_value

        return sorted(moves, key=priority, reverse=True)

    def _check_time(self) -> None:
        if time.monotonic() >= self._deadline:
            raise SearchTimeout
