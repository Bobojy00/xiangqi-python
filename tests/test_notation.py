from xiangqi import Board, Color, move_from_uci, move_to_uci


INITIAL_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def test_initial_fen_round_trip():
    board = Board.from_fen(INITIAL_FEN)
    assert board.side_to_move is Color.RED
    assert board.to_fen() == INITIAL_FEN


def test_move_notation_round_trip():
    move = move_from_uci("h2e2")
    assert move_to_uci(move) == "h2e2"


def test_invalid_fen_is_rejected():
    try:
        Board.from_fen("9/9/9/9/9/9/9/9/9/9 w - - 0 1")
    except ValueError as exc:
        assert "generals" in str(exc)
    else:
        raise AssertionError("invalid FEN was accepted")

