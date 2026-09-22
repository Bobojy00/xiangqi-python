from xiangqi import Board, Color, PieceType


def test_initial_position_and_common_move():
    board = Board.initial()
    assert board.side_to_move is Color.RED
    assert len(board.legal_moves()) == 44
    board.push("h2e2")
    assert board.piece_at("e2").kind is PieceType.CANNON
    assert board.side_to_move is Color.BLACK


def test_horse_leg_is_blocked_in_initial_position():
    board = Board.initial()
    horse_moves = [str(move) for move in board.legal_moves() if str(move).startswith("h0")]
    assert "h0f1" not in horse_moves
    assert "h0g2" in horse_moves


def test_elephant_cannot_cross_river():
    fen = "4k4/9/9/9/9/9/9/9/4B4/4K4 w - - 0 1"
    board = Board.from_fen(fen)
    assert all(int(str(move)[3]) <= 4 for move in board.legal_moves())


def test_flying_general_is_check():
    board = Board.from_fen("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1")
    assert board.is_in_check(Color.RED)
    assert board.is_in_check(Color.BLACK)


def test_cannon_requires_a_screen_to_capture():
    board = Board.from_fen("k3r4/9/4p4/9/4C4/9/9/9/9/4K4 w - - 0 1")
    assert "e5e9" in {str(move) for move in board.legal_moves()}
    board.push("e5e9")
    assert board.piece_at("e9").kind is PieceType.CANNON


def test_checkmate_result():
    board = Board.from_fen("3RkR3/3R1R3/9/9/9/9/9/9/9/4K4 b - - 0 1")
    assert board.result().status == "checkmate"
    assert board.result().winner is Color.RED


def test_push_and_undo_restore_position():
    board = Board.initial()
    initial = board.to_fen()
    board.push("h2e2")
    board.undo()
    assert board.to_fen() == initial
