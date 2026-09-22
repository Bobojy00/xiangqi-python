from xiangqi import Board, Engine


def test_engine_returns_legal_move_for_each_level():
    board = Board.initial()
    legal = set(board.legal_moves())
    for level in ("easy", "normal", "hard"):
        move = Engine(level).choose_move(board, time_limit=0.2)
        assert move in legal


def test_engine_can_find_a_simple_capture():
    board = Board.from_fen("4k4/9/9/9/9/4R4/9/9/9/4K4 w - - 0 1")
    move = Engine("easy").choose_move(board, time_limit=0.5)
    assert move in board.legal_moves()

