from argon import Interface, CommandUsageError, CommandNotFound

def build_cli():
    cli = Interface(name="t", version="0.1.0")

    @cli.command(help="Echo message", aliases=["repeat"])
    def echo(ctx, msg: str, times: int = 1):
        return " ".join([msg] * times)

    grp = cli.group("math")

    @grp.command(help="Add numbers", min_positionals=2)
    def add(ctx, *nums: str):
        return sum(int(n) for n in nums)

    return cli

def test_basic_command():
    cli = build_cli()
    out = cli.run_line("echo hello --times=2")
    assert out == "hello hello"

def test_alias():
    cli = build_cli()
    out = cli.run_line("repeat hi --times=3")
    assert out == "hi hi hi"

def test_group_command():
    cli = build_cli()
    out = cli.run_line("math add 2 3 4")
    assert out == 9

def test_missing_command():
    cli = build_cli()
    try:
        cli.run_line("bogus")
    except CommandNotFound:
        pass
    else:
        assert False, "Expected CommandNotFound"

def test_usage_error():
    cli = build_cli()
    try:
        cli.run_line("math add 5")  # needs at least 2
    except CommandUsageError:
        pass
    else:
        assert False, "Expected CommandUsageError"


def test_run_argv():
    cli = build_cli()
    out = cli.run_argv(["echo", "hi", "--times", "2"])
    assert out == "hi hi"
