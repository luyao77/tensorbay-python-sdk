#!/usr/bin/env python3
#
# Copyright 2021 Graviti. Licensed under MIT License.
#

"""Implementation of gas rm."""

import sys
from typing import Dict

import click

from .tbrn import TBRN, TBRNType
from .utility import filter_data, get_dataset_client, get_gas


def _implement_rm(obj: Dict[str, str], tbrn: str, is_recursive: bool) -> None:
    gas = get_gas(**obj)
    info = TBRN(tbrn=tbrn)
    dataset_client = get_dataset_client(gas, info, is_fusion=False)

    if info.type not in (TBRNType.SEGMENT, TBRNType.NORMAL_FILE):
        click.echo(f'"{tbrn}" is an invalid path to remove', err=True)
        sys.exit(1)

    if not info.is_draft:
        click.echo(
            f'To remove the data, "{info}" must be in draft status, like "{info}#1"', err=True
        )
        sys.exit(1)

    if info.type == TBRNType.SEGMENT:
        if not is_recursive:
            click.echo("Please use -r option to remove the whole segment", err=True)
            sys.exit(1)
        dataset_client.delete_segment(info.segment_name)
    elif info.remote_path.endswith("/") and not is_recursive:
        click.echo("Please use -r option to remove recursively", err=True)
        sys.exit(1)
    else:
        segment = dataset_client.get_segment(info.segment_name)
        data = filter_data(segment.list_data_paths(), info.remote_path, is_recursive)
        if not data:
            echo_info = "file or directory" if is_recursive else "file"
            click.echo(f'No such {echo_info} "{tbrn}" ', err=True)
            sys.exit(1)
        segment.delete_data(data)