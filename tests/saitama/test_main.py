from unittest import mock

from saitama.__main__ import main


@mock.patch(
    "saitama.__main__.parse_args",
    return_value=mock.MagicMock(
        common=mock.MagicMock(),
        migrate_subcommand=mock.MagicMock(),
        test_subcommand=None,
    ),
)
@mock.patch("saitama.__main__.Migrations", return_value=mock.MagicMock())
def test_migrate(mock_migrate: mock.MagicMock, mock_args: mock.MagicMock) -> None:
    mock_runner = mock.MagicMock()
    mock_migrate.return_value = mock.MagicMock(run=mock_runner)
    main()
    assert mock_migrate.call_count == 1
    calls = [
        mock.call(
            mock_args.return_value.common,
            migrate_args=mock_args.return_value.migrate_subcommand,
        )
    ]
    assert mock_migrate.call_args_list == calls
    assert mock_runner.call_count == 1
    assert mock_runner.call_args_list == [mock.call()]


@mock.patch(
    "saitama.__main__.parse_args",
    return_value=mock.MagicMock(
        common=mock.MagicMock(),
        migrate_subcommand=None,
        test_subcommand=mock.MagicMock(),
    ),
)
@mock.patch("saitama.__main__.UnitTest")
def test_unittest(mock_unittest: mock.MagicMock, mock_args: mock.MagicMock) -> None:
    mock_runner = mock.MagicMock()
    mock_unittest.return_value = mock.MagicMock(run=mock_runner)
    main()
    assert mock_unittest.call_count == 1
    calls = [mock.call(mock_args.return_value.common)]
    assert mock_unittest.call_args_list == calls
    assert mock_runner.call_count == 1
    assert mock_runner.call_args_list == [mock.call()]
