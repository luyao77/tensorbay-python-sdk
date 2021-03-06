#!/usr/bin/env python3
#
# Copyright 2021 Graviti. Licensed under MIT License.
#

"""Graviti Tensorbay gas CLI utility functions."""

import logging
import os
import sys
from configparser import ConfigParser
from typing import NoReturn, Optional, Tuple, overload

import click
from typing_extensions import Literal

from ..client import GAS
from ..client import config as client_config
from ..client.dataset import DatasetClient, FusionDatasetClient
from ..client.gas import DatasetClientType
from .tbrn import TBRN


def _implement_cli(
    ctx: click.Context, access_key: str, url: str, profile_name: str, debug: bool
) -> None:
    ctx.obj = {
        "access_key": access_key,
        "url": url,
        "profile_name": profile_name,
    }
    client_config._x_source = "PYTHON-CLI"  # pylint: disable=protected-access

    if debug:
        logging.basicConfig(level=logging.DEBUG)


def get_config_filepath() -> str:
    """Get the path of the config file.

    Returns:
        The path of the config file.

    """
    home = "USERPROFILE" if os.name == "nt" else "HOME"
    return os.path.join(os.environ[home], ".gasconfig")


def read_config(config_filepath: str, profile_name: str) -> Tuple[str, str]:
    """Read accessKey and URL from the config file.

    Arguments:
        config_filepath: The file containing config info.
        profile_name: The environment to login.

    Returns:
        The accessKey of profile_name read from the config file.
        The URL of profile_name read from the config file.

    """
    if not os.path.exists(config_filepath):
        error(
            f"{config_filepath} not exist"
            "\n\nPlease use 'gas config <accessKey>' to create config file"
        )

    config_parser = ConfigParser()
    config_parser.read(config_filepath)
    access_key = config_parser[profile_name]["accessKey"]
    url = config_parser[profile_name]["url"] if "url" in config_parser[profile_name] else ""
    return access_key, url


def get_gas(access_key: str, url: str, profile_name: str) -> GAS:
    """Load an object of :class:`~tensorbay.client.gas.GAS`.

    We will read accessKey and URL from the appointed profile_name and login gas.

    Arguments:
        access_key: The accessKey of gas.
        url: The login URL.
        profile_name: The environment to login.

    Returns:
        Gas client logged in with accessKey and URL.

    """
    if not access_key and not url:
        access_key, url = read_config(get_config_filepath(), profile_name)

    if not access_key:
        error("AccessKey should be appointed")

    return GAS(access_key, url)


@overload
def get_dataset_client(gas: GAS, info: TBRN, is_fusion: Literal[None] = None) -> DatasetClientType:
    ...


@overload
def get_dataset_client(gas: GAS, info: TBRN, is_fusion: Literal[False]) -> DatasetClient:
    ...


@overload
def get_dataset_client(gas: GAS, info: TBRN, is_fusion: Literal[True]) -> FusionDatasetClient:
    ...


@overload
def get_dataset_client(gas: GAS, info: TBRN, is_fusion: Optional[bool] = None) -> DatasetClientType:
    ...


def get_dataset_client(gas: GAS, info: TBRN, is_fusion: Optional[bool] = None) -> DatasetClientType:
    """Get the dataset client with any type and its version info.

    Arguments:
        gas: The gas client.
        info: The tbrn of the resource.
        is_fusion: Whether the dataset is a fusion dataset, True for fusion dataset.

    Returns:
        The dataset client and its version info.

    """
    dataset_client = (
        gas._get_dataset_with_any_type(info.dataset_name)  # pylint: disable=protected-access
        if is_fusion is None
        else gas.get_dataset(info.dataset_name, is_fusion)
    )
    if info.is_draft:
        dataset_client.checkout(draft_number=info.draft_number)
    elif info.revision is not None:
        dataset_client.checkout(revision=info.revision)
    return dataset_client


def edit_input(hint: str) -> Tuple[str, str]:
    """Edit information input from the editor.

    Arguments:
        hint: The hint to be added in the temp file opened by the editor.

    Returns:
        The extracted title and the description.

    """
    config_file = get_config_filepath()
    config_parser = ConfigParser()
    config_parser.read(config_file)

    editor = config_parser["config"].get("editor") if "config" in config_parser else None
    input_info = click.edit(hint, editor=editor)
    return _clean_up(input_info)


def _clean_up(editor_input: Optional[str]) -> Tuple[str, str]:
    """Clean up the information from the editor input.

    Arguments:
        editor_input: The editor input.

    Returns:
        The extracted title and the description.

    """
    if not editor_input:
        return "", ""

    cleaned_up_lines = []
    for line in editor_input.splitlines():
        if line and not line.startswith("#"):
            cleaned_up_lines.append(line.rstrip())

    if not cleaned_up_lines:
        return "", ""
    return cleaned_up_lines[0].lstrip(), "\n".join(cleaned_up_lines[1:])


def error(message: str) -> NoReturn:
    """Print the error message and exit the program.

    Arguments:
        message: The error message to echo.

    """
    click.secho(f"ERROR: {message}", err=True, fg="red")
    sys.exit(1)
