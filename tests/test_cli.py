from xiangqi.cli import main


INITIAL_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def test_validate_command(capsys):
    assert main(["validate", INITIAL_FEN]) == 0
    assert "有效" in capsys.readouterr().out


def test_invalid_validate_command(capsys):
    assert main(["validate", "invalid"]) == 1
    assert "非法" in capsys.readouterr().out

