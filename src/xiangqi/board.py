"""Board representation and Xiangqi rules.

Coordinates use files ``a``-``i`` from left to right and ranks ``0``-``9``
from Red's side to Black's side.  For example, Red's right cannon starts on
``h2`` and Red's right horse starts on ``h0``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator


class Color(str, Enum):
    RED = "red"
    BLACK = "black"

    @property
    def opponent(self) -> "Color":
        return Color.BLACK if self is Color.RED else Color.RED

    @property
    def forward(self) -> int:
        return -1 if self is Color.RED else 1


class PieceType(str, Enum):
    GENERAL = "general"
    ADVISOR = "advisor"
    ELEPHANT = "elephant"
    HORSE = "horse"
    ROOK = "rook"
    CANNON = "cannon"
    PAWN = "pawn"


@dataclass(frozen=True, slots=True)
class Piece:
    color: Color
    kind: PieceType

    @property
    def symbol(self) -> str:
        symbols = {
            PieceType.GENERAL: "k",
            PieceType.ADVISOR: "a",
            PieceType.ELEPHANT: "b",
            PieceType.HORSE: "n",
            PieceType.ROOK: "r",
            PieceType.CANNON: "c",
            PieceType.PAWN: "p",
        }
        value = symbols[self.kind]
        return value.upper() if self.color is Color.RED else value


@dataclass(frozen=True, slots=True)
class Move:
    from_sq: int
    to_sq: int

    @classmethod
    def from_uci(cls, value: str) -> "Move":
        value = value.strip().lower()
        if len(value) != 4:
            raise ValueError("move must look like 'h2e2'")
        return cls(parse_square(value[:2]), parse_square(value[2:]))

    def to_uci(self) -> str:
        return square_name(self.from_sq) + square_name(self.to_sq)

    def __str__(self) -> str:
        return self.to_uci()


@dataclass(frozen=True, slots=True)
class GameResult:
    status: str
    winner: Color | None = None

    @property
    def terminal(self) -> bool:
        return self.status != "ongoing"


PIECE_VALUES = {
    PieceType.GENERAL: 10_000,
    PieceType.ROOK: 900,
    PieceType.CANNON: 500,
    PieceType.HORSE: 450,
    PieceType.ELEPHANT: 250,
    PieceType.ADVISOR: 250,
    PieceType.PAWN: 100,
}

FILES = "abcdefghi"
UNICODE_PIECES = {
    (Color.RED, PieceType.GENERAL): "帅",
    (Color.RED, PieceType.ADVISOR): "仕",
    (Color.RED, PieceType.ELEPHANT): "相",
    (Color.RED, PieceType.HORSE): "马",
    (Color.RED, PieceType.ROOK): "车",
    (Color.RED, PieceType.CANNON): "炮",
    (Color.RED, PieceType.PAWN): "兵",
    (Color.BLACK, PieceType.GENERAL): "将",
    (Color.BLACK, PieceType.ADVISOR): "士",
    (Color.BLACK, PieceType.ELEPHANT): "象",
    (Color.BLACK, PieceType.HORSE): "马",
    (Color.BLACK, PieceType.ROOK): "车",
    (Color.BLACK, PieceType.CANNON): "炮",
    (Color.BLACK, PieceType.PAWN): "卒",
}


def square(row: int, col: int) -> int:
    if not (0 <= row < 10 and 0 <= col < 9):
        raise ValueError("square outside the 9x10 board")
    return row * 9 + col


def row_col(index: int) -> tuple[int, int]:
    if not 0 <= index < 90:
        raise ValueError("square index must be between 0 and 89")
    return divmod(index, 9)


def parse_square(value: str) -> int:
    if len(value) != 2 or value[0] not in FILES or not value[1].isdigit():
        raise ValueError(f"invalid square: {value!r}")
    return square(9 - int(value[1]), FILES.index(value[0]))


def square_name(index: int) -> str:
    row, col = row_col(index)
    return f"{FILES[col]}{9 - row}"


def _inside(row: int, col: int) -> bool:
    return 0 <= row < 10 and 0 <= col < 9


def _same_color(piece: Piece | None, color: Color) -> bool:
    return piece is not None and piece.color is color


class Board:
    """Mutable Xiangqi position with legal move generation and history."""

    def __init__(
        self,
        grid: list[Piece | None] | None = None,
        side_to_move: Color = Color.RED,
        *,
        halfmove_clock: int = 0,
        fullmove_number: int = 1,
    ) -> None:
        self.grid = list(grid) if grid is not None else self._initial_grid()
        if len(self.grid) != 90:
            raise ValueError("grid must contain 90 squares")
        self.side_to_move = side_to_move
        self.halfmove_clock = halfmove_clock
        self.fullmove_number = fullmove_number
        self._history: list[tuple[tuple[str | None, ...], Color, bool, Color]] = [
            (self.position_key(), self.side_to_move, False, self.side_to_move.opponent)
        ]
        self._undo_stack: list[tuple[list[Piece | None], Color, int, int, list[tuple[tuple[str | None, ...], Color, bool, Color]]]] = []

    @classmethod
    def initial(cls) -> "Board":
        return cls()

    @staticmethod
    def _initial_grid() -> list[Piece | None]:
        grid: list[Piece | None] = [None] * 90
        back = [
            PieceType.ROOK,
            PieceType.HORSE,
            PieceType.ELEPHANT,
            PieceType.ADVISOR,
            PieceType.GENERAL,
            PieceType.ADVISOR,
            PieceType.ELEPHANT,
            PieceType.HORSE,
            PieceType.ROOK,
        ]
        for col, kind in enumerate(back):
            grid[square(0, col)] = Piece(Color.BLACK, kind)
            grid[square(9, col)] = Piece(Color.RED, kind)
        for col in (1, 7):
            grid[square(2, col)] = Piece(Color.BLACK, PieceType.CANNON)
            grid[square(7, col)] = Piece(Color.RED, PieceType.CANNON)
        for col in (0, 2, 4, 6, 8):
            grid[square(3, col)] = Piece(Color.BLACK, PieceType.PAWN)
            grid[square(6, col)] = Piece(Color.RED, PieceType.PAWN)
        return grid

    def copy(self) -> "Board":
        other = Board(
            self.grid,
            self.side_to_move,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        )
        other._history = list(self._history)
        other._undo_stack = []
        return other

    def piece_at(self, location: int | str) -> Piece | None:
        index = parse_square(location) if isinstance(location, str) else location
        return self.grid[index]

    def position_key(self) -> tuple[str | None, ...]:
        return tuple(None if piece is None else piece.color.value[0] + piece.kind.value[0] for piece in self.grid) + (self.side_to_move.value[0],)

    def _snapshot(self) -> tuple[list[Piece | None], Color, int, int, list[tuple[tuple[str | None, ...], Color, bool, Color]]]:
        return (list(self.grid), self.side_to_move, self.halfmove_clock, self.fullmove_number, list(self._history))

    def push(self, move: Move | str) -> Move:
        if isinstance(move, str):
            move = Move.from_uci(move)
        legal = next((candidate for candidate in self.legal_moves() if candidate == move), None)
        if legal is None:
            raise ValueError(f"illegal move: {move}")
        self._undo_stack.append(self._snapshot())
        moving = self.grid[move.from_sq]
        captured = self.grid[move.to_sq]
        assert moving is not None
        self.grid[move.to_sq] = moving
        self.grid[move.from_sq] = None
        self.halfmove_clock = 0 if captured is not None or moving.kind is PieceType.PAWN else self.halfmove_clock + 1
        if self.side_to_move is Color.BLACK:
            self.fullmove_number += 1
        mover = self.side_to_move
        self.side_to_move = self.side_to_move.opponent
        gave_check = self.is_in_check(self.side_to_move)
        self._history.append((self.position_key(), self.side_to_move, gave_check, mover))
        return move

    def undo(self) -> Move | None:
        if not self._undo_stack:
            return None
        grid, side, halfmove, fullmove, history = self._undo_stack.pop()
        self.grid = grid
        self.side_to_move = side
        self.halfmove_clock = halfmove
        self.fullmove_number = fullmove
        self._history = history
        return None

    def legal_moves(self, color: Color | None = None) -> list[Move]:
        color = color or self.side_to_move
        moves: list[Move] = []
        for from_sq, piece in enumerate(self.grid):
            if piece is None or piece.color is not color:
                continue
            for move in self._pseudo_moves(from_sq, piece):
                captured = self.grid[move.to_sq]
                self.grid[move.from_sq] = None
                self.grid[move.to_sq] = piece
                safe = not self.is_in_check(color)
                self.grid[move.from_sq] = piece
                self.grid[move.to_sq] = captured
                if safe:
                    moves.append(move)
        return moves

    def _pseudo_moves(self, from_sq: int, piece: Piece) -> Iterator[Move]:
        row, col = row_col(from_sq)
        if piece.kind is PieceType.ROOK:
            yield from self._ray_moves(from_sq, piece, ((1, 0), (-1, 0), (0, 1), (0, -1)))
        elif piece.kind is PieceType.CANNON:
            yield from self._cannon_moves(from_sq, piece)
        elif piece.kind is PieceType.HORSE:
            for dr, dc, lr, lc in ((-2, -1, -1, 0), (-2, 1, -1, 0), (2, -1, 1, 0), (2, 1, 1, 0), (-1, -2, 0, -1), (-1, 2, 0, 1), (1, -2, 0, -1), (1, 2, 0, 1)):
                if _inside(row + lr, col + lc) and self.grid[square(row + lr, col + lc)] is None:
                    yield from self._single_target(from_sq, piece, row + dr, col + dc)
        elif piece.kind is PieceType.ELEPHANT:
            for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
                eye_r, eye_c = row + dr // 2, col + dc // 2
                target_r, target_c = row + dr, col + dc
                if not _inside(target_r, target_c) or self.grid[square(eye_r, eye_c)] is not None:
                    continue
                if piece.color is Color.RED and target_r < 5:
                    continue
                if piece.color is Color.BLACK and target_r > 4:
                    continue
                yield from self._single_target(from_sq, piece, target_r, target_c)
        elif piece.kind is PieceType.ADVISOR:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yield from self._single_target(from_sq, piece, row + dr, col + dc, palace_only=True)
        elif piece.kind is PieceType.GENERAL:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yield from self._single_target(from_sq, piece, row + dr, col + dc, palace_only=True)
            # Flying general capture is represented as an attack, but not as a
            # legal move: a game ends by checkmate rather than capturing generals.
        elif piece.kind is PieceType.PAWN:
            yield from self._single_target(from_sq, piece, row + piece.color.forward, col)
            crossed = row <= 4 if piece.color is Color.RED else row >= 5
            if crossed:
                yield from self._single_target(from_sq, piece, row, col - 1)
                yield from self._single_target(from_sq, piece, row, col + 1)

    def _single_target(self, from_sq: int, piece: Piece, row: int, col: int, *, palace_only: bool = False) -> Iterator[Move]:
        if not _inside(row, col):
            return
        if palace_only and not self._in_palace(piece.color, row, col):
            return
        target = self.grid[square(row, col)]
        if target is None or (target.color is not piece.color and target.kind is not PieceType.GENERAL):
            yield Move(from_sq, square(row, col))

    def _ray_moves(self, from_sq: int, piece: Piece, directions: tuple[tuple[int, int], ...]) -> Iterator[Move]:
        row, col = row_col(from_sq)
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while _inside(r, c):
                target = self.grid[square(r, c)]
                if target is None:
                    yield Move(from_sq, square(r, c))
                else:
                    if target.color is not piece.color and target.kind is not PieceType.GENERAL:
                        yield Move(from_sq, square(r, c))
                    break
                r += dr
                c += dc

    def _cannon_moves(self, from_sq: int, piece: Piece) -> Iterator[Move]:
        row, col = row_col(from_sq)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r, c = row + dr, col + dc
            while _inside(r, c) and self.grid[square(r, c)] is None:
                yield Move(from_sq, square(r, c))
                r += dr
                c += dc
            r += dr
            c += dc
            while _inside(r, c):
                target = self.grid[square(r, c)]
                if target is not None:
                    if target.color is not piece.color and target.kind is not PieceType.GENERAL:
                        yield Move(from_sq, square(r, c))
                    break
                r += dr
                c += dc

    @staticmethod
    def _in_palace(color: Color, row: int, col: int) -> bool:
        return 3 <= col <= 5 and (7 <= row <= 9 if color is Color.RED else 0 <= row <= 2)

    def find_general(self, color: Color) -> int | None:
        for index, piece in enumerate(self.grid):
            if piece is not None and piece.color is color and piece.kind is PieceType.GENERAL:
                return index
        return None

    def is_in_check(self, color: Color) -> bool:
        general = self.find_general(color)
        if general is None:
            return True
        opponent = color.opponent
        for index, piece in enumerate(self.grid):
            if piece is not None and piece.color is opponent and self._piece_attacks(index, piece, general):
                return True
        other_general = self.find_general(opponent)
        if other_general is not None:
            r1, c1 = row_col(general)
            r2, c2 = row_col(other_general)
            if c1 == c2:
                step = 1 if r2 > r1 else -1
                if all(self.grid[square(r, c1)] is None for r in range(r1 + step, r2, step)):
                    return True
        return False

    def _piece_attacks(self, from_sq: int, piece: Piece, target_sq: int) -> bool:
        fr, fc = row_col(from_sq)
        tr, tc = row_col(target_sq)
        dr, dc = tr - fr, tc - fc
        if piece.kind is PieceType.PAWN:
            return (dr == piece.color.forward and dc == 0) or (
                (fr <= 4 if piece.color is Color.RED else fr >= 5) and dr == 0 and abs(dc) == 1
            )
        if piece.kind is PieceType.HORSE:
            if (abs(dr), abs(dc)) not in ((1, 2), (2, 1)):
                return False
            leg = (fr, fc + (dc // 2)) if abs(dc) == 2 else (fr + (dr // 2), fc)
            return self.grid[square(*leg)] is None
        if piece.kind is PieceType.ELEPHANT:
            return abs(dr) == 2 and abs(dc) == 2 and self.grid[square(fr + dr // 2, fc + dc // 2)] is None and ((piece.color is Color.RED and tr >= 5) or (piece.color is Color.BLACK and tr <= 4))
        if piece.kind is PieceType.ADVISOR:
            return abs(dr) == 1 and abs(dc) == 1 and self._in_palace(piece.color, tr, tc)
        if piece.kind is PieceType.GENERAL:
            return abs(dr) + abs(dc) == 1 and self._in_palace(piece.color, tr, tc)
        if piece.kind in (PieceType.ROOK, PieceType.CANNON):
            if dr != 0 and dc != 0:
                return False
            distance = abs(dr) + abs(dc)
            between = 0
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
            r, c = fr + step_r, fc + step_c
            while (r, c) != (tr, tc):
                if self.grid[square(r, c)] is not None:
                    between += 1
                r += step_r
                c += step_c
            return between == (1 if piece.kind is PieceType.CANNON else 0)
        return False

    def is_long_check(self, threshold: int = 3) -> bool:
        if len(self._history) < threshold * 2:
            return False
        recent = self._history[-(threshold * 2 - 1):]
        checking_color = recent[-1][3]
        checking_records = [record for record in recent if record[3] is checking_color]
        return len(checking_records) >= threshold and all(record[2] for record in checking_records[-threshold:])

    def result(self) -> GameResult:
        if self.is_long_check():
            return GameResult("long_check", self.side_to_move)
        current_key = self._history[-1][0]
        if sum(record[0] == current_key for record in self._history) >= 3:
            return GameResult("repetition", None)
        moves = self.legal_moves()
        if moves:
            return GameResult("ongoing", None)
        if self.is_in_check(self.side_to_move):
            return GameResult("checkmate", self.side_to_move.opponent)
        return GameResult("stalemate", self.side_to_move.opponent)

    def to_fen(self) -> str:
        rows: list[str] = []
        for row in range(10):
            empty = 0
            output = ""
            for col in range(9):
                piece = self.grid[square(row, col)]
                if piece is None:
                    empty += 1
                else:
                    if empty:
                        output += str(empty)
                        empty = 0
                    output += piece.symbol
            if empty:
                output += str(empty)
            rows.append(output)
        side = "w" if self.side_to_move is Color.RED else "b"
        return f"{'/'.join(rows)} {side} - - {self.halfmove_clock} {self.fullmove_number}"

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        fields = fen.strip().split()
        if len(fields) < 2:
            raise ValueError("FEN must contain board and side-to-move fields")
        rows = fields[0].split("/")
        if len(rows) != 10:
            raise ValueError("Xiangqi FEN must contain 10 ranks")
        grid: list[Piece | None] = [None] * 90
        kinds = {"k": PieceType.GENERAL, "a": PieceType.ADVISOR, "b": PieceType.ELEPHANT, "n": PieceType.HORSE, "r": PieceType.ROOK, "c": PieceType.CANNON, "p": PieceType.PAWN}
        for row, encoded in enumerate(rows):
            col = 0
            for char in encoded:
                if char.isdigit():
                    col += int(char)
                elif char.lower() in kinds and col < 9:
                    color = Color.RED if char.isupper() else Color.BLACK
                    grid[square(row, col)] = Piece(color, kinds[char.lower()])
                    col += 1
                else:
                    raise ValueError(f"invalid FEN rank: {encoded!r}")
            if col != 9:
                raise ValueError(f"FEN rank does not contain 9 files: {encoded!r}")
        side = {"w": Color.RED, "r": Color.RED, "b": Color.BLACK, "k": Color.BLACK}.get(fields[1].lower())
        if side is None:
            raise ValueError("FEN side must be w/r or b/k")
        halfmove = int(fields[4]) if len(fields) > 4 else 0
        fullmove = int(fields[5]) if len(fields) > 5 else 1
        board = cls(grid, side, halfmove_clock=halfmove, fullmove_number=fullmove)
        if board.find_general(Color.RED) is None or board.find_general(Color.BLACK) is None:
            raise ValueError("FEN must contain both generals")
        return board

    def __str__(self) -> str:
        lines = ["  a b c d e f g h i"]
        for row in range(10):
            cells = []
            for col in range(9):
                piece = self.grid[square(row, col)]
                cells.append(UNICODE_PIECES[(piece.color, piece.kind)] if piece else "·")
            lines.append(f"{row} " + " ".join(cells))
            if row == 4:
                lines.append("  -------- 楚河 --------")
        lines.append(f"回合: {'红' if self.side_to_move is Color.RED else '黑'}")
        return "\n".join(lines)

