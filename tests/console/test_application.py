from __future__ import annotations

import re

from typing import TYPE_CHECKING

import pytest

from cleo.testers.application_tester import ApplicationTester
from entrypoints import EntryPoint

from poetry.console.application import Application
from poetry.console.commands.command import Command
from poetry.plugins.application_plugin import ApplicationPlugin


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class FooCommand(Command):
    name = "foo"

    description = "Foo Command"

    def handle(self) -> int:
        self.line("foo called")

        return 0


class AddCommandPlugin(ApplicationPlugin):
    commands = [FooCommand]


def test_application_with_plugins(mocker: MockerFixture):
    mocker.patch(
        "entrypoints.get_group_all",
        return_value=[
            EntryPoint(
                "my-plugin", "tests.console.test_application", "AddCommandPlugin"
            )
        ],
    )

    app = Application()

    tester = ApplicationTester(app)
    tester.execute("")

    assert re.search(r"\s+foo\s+Foo Command", tester.io.fetch_output()) is not None
    assert tester.status_code == 0


def test_application_with_plugins_disabled(mocker: MockerFixture):
    mocker.patch(
        "entrypoints.get_group_all",
        return_value=[
            EntryPoint(
                "my-plugin", "tests.console.test_application", "AddCommandPlugin"
            )
        ],
    )

    app = Application()

    tester = ApplicationTester(app)
    tester.execute("--no-plugins")

    assert re.search(r"\s+foo\s+Foo Command", tester.io.fetch_output()) is None
    assert tester.status_code == 0


def test_application_execute_plugin_command(mocker: MockerFixture):
    mocker.patch(
        "entrypoints.get_group_all",
        return_value=[
            EntryPoint(
                "my-plugin", "tests.console.test_application", "AddCommandPlugin"
            )
        ],
    )

    app = Application()

    tester = ApplicationTester(app)
    tester.execute("foo")

    assert tester.io.fetch_output() == "foo called\n"
    assert tester.status_code == 0


def test_application_execute_plugin_command_with_plugins_disabled(
    mocker: MockerFixture,
):
    mocker.patch(
        "entrypoints.get_group_all",
        return_value=[
            EntryPoint(
                "my-plugin", "tests.console.test_application", "AddCommandPlugin"
            )
        ],
    )

    app = Application()

    tester = ApplicationTester(app)
    tester.execute("foo --no-plugins")

    assert tester.io.fetch_output() == ""
    assert tester.io.fetch_error() == '\nThe command "foo" does not exist.\n'
    assert tester.status_code == 1


@pytest.mark.parametrize("disable_cache", [True, False])
def test_application_verify_source_cache_flag(disable_cache: bool):
    app = Application()

    tester = ApplicationTester(app)
    command = "debug info"

    if disable_cache:
        command = f"{command} --no-cache"

    assert not app._poetry

    tester.execute(command)

    assert app.poetry.pool.repositories

    for repo in app.poetry.pool.repositories:
        assert repo._disable_cache == disable_cache
