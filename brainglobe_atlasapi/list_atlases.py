"""
    Some functionality to list all available and downloaded brainglobe atlases
"""

import os

from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

from brainglobe_atlasapi import config, descriptors, utils


def get_downloaded_atlases():
    """Get a list of all the downloaded atlases and their version.

    Returns
    -------
    list
        A list of tuples with the locally available atlases and their version
    """

    # Get brainglobe directory:
    brainglobe_dir = config.get_brainglobe_dir()

    return [
        f.name.split("_v")[0]
        for f in brainglobe_dir.glob("*_*_*_v*")
        if f.is_dir()
    ]


def get_local_atlas_version(atlas_name):
    """Get version of a downloaded available atlas.

    Arguments
    ---------
    atlas_name : str
        Name of the atlas.

    Returns
    -------
    str
        Version of atlas.
    """

    brainglobe_dir = config.get_brainglobe_dir()
    return [
        f.name.split("_v")[1]
        for f in brainglobe_dir.glob(f"*{atlas_name}*")
        if f.is_dir()
    ][0]


def get_all_atlases_lastversions():
    """Read from URL all available last versions"""

    if utils.check_internet_connection(raise_error=False):
        available_atlases = utils.conf_from_url(
            descriptors.remote_url_base.format("last_versions.conf")
        )
        available_atlases = dict(available_atlases["atlases"])

        return available_atlases

    if utils.check_internet_connection(
        url=(descriptors.remote_url_base.format("last_versions.conf")),
        raise_error=False,
    ) == "Gin_Server_Error" or not utils.check_internet_connection(
        raise_error=False
    ):

        print("No Internet connection.")

        conf_path = (f"{config.get_brainglobe_dir()}", "last_versions.conf")
        full_file_path = os.path.join(*conf_path)

        if utils.conf_from_file(full_file_path) != False:
            print(
                "Note: This list of atlases may be outdated. "
                "Please connect to the Internet for an updated list."
            )
            available_atlases_offline = utils.conf_from_file(full_file_path)
            available_atlases_offline = dict(
                available_atlases_offline["atlases"]
            )
            return available_atlases_offline


def get_atlases_lastversions():
    """
    Returns
    -------
    dict
        A dictionary with metadata about already installed atlases.
    """

    available_atlases = get_all_atlases_lastversions()

    # Get downloaded atlases looping over folders in brainglobe directory:
    atlases = {}
    for name in get_downloaded_atlases():
        if name in available_atlases.keys():
            local_version = get_local_atlas_version(name)
            atlases[name] = dict(
                downloaded=True,
                local=name,
                version=local_version,
                latest_version=str(available_atlases[name]),
                updated=str(available_atlases[name]) == local_version,
            )
    return atlases


def show_atlases(show_local_path: bool = False, table_width: int = 88) -> None:
    """
    Prints a formatted table with the name and version of local (downloaded)
    and online (available) atlases.
    Parameters
    ----------
    show_local_path : bool, optional
        If True, includes the local path of the atlases
        in the table (default is False).
    table_width : int, optional
        The width of the table to be printed (default is 88).

    Returns
    -------
    None

    """

    available_atlases = get_all_atlases_lastversions()

    # Get local atlases
    downloaded_atlases = get_atlases_lastversions()

    # Get atlases not yet downloaded
    non_downloaded_atlases = {}
    for atlas in available_atlases.keys():
        if atlas not in downloaded_atlases.keys():
            non_downloaded_atlases[str(atlas)] = dict(
                downloaded=False,
                local="",
                version="",
                latest_version=str(available_atlases[atlas]),
                updated=None,
            )

    # Create table
    table = Table(
        show_header=True,
        header_style="bold green",
        show_lines=True,
        expand=False,
        box=None,
    )

    table.add_column("Name", no_wrap=True, width=32)
    table.add_column("Downloaded", justify="center")
    table.add_column("Updated", justify="center")
    table.add_column("Local version", justify="center")
    table.add_column("Latest version", justify="center")
    if show_local_path:
        table.add_column("Local path")

    # Add downloaded atlases (sorted) to the table first
    for atlas_name in sorted(downloaded_atlases.keys()):
        atlas = downloaded_atlases[atlas_name]
        table = add_atlas_to_row(
            atlas_name, atlas, table, show_local_path=show_local_path
        )

    # Then add non-download atlases (sorted) to the table
    for atlas_name in sorted(non_downloaded_atlases.keys()):
        atlas = non_downloaded_atlases[atlas_name]
        table = add_atlas_to_row(
            atlas_name, atlas, table, show_local_path=show_local_path
        )

    # Print the resulting table
    rprint(
        Panel.fit(
            table,
            width=table_width,
            title="Brainglobe Atlases",
        )
    )


def add_atlas_to_row(atlas, info, table, show_local_path=False):
    """
    Add information about each atlas to a row of the rich table.

    Parameters
    ----------
    atlas : str
        The name of the atlas.
    info : dict
        A dictionary containing information about the atlas.
    table : rich.table.Table
        The table to which the row will be added.
    show_local_path : bool, optional
        If True, includes the local path of the atlas
        in the row (default is False).

    Returns
    -------
    rich.table.Table
        The updated table with the new row added.
    -------

    """
    if info["downloaded"]:
        downloaded = "[green]:heavy_check_mark:[/green]"

        if info["version"] == info["latest_version"]:
            updated = "[green]:heavy_check_mark:[/green]"
        else:
            updated = "[red dim]x"

    else:
        downloaded = ""
        updated = ""

    row = [
        "[bold]" + atlas,
        downloaded,
        updated,
        ("[#c4c4c4]" + info["version"] if "-" not in info["version"] else ""),
        "[#c4c4c4]" + info["latest_version"],
    ]

    if show_local_path:
        row.append(info["local"])

    table.add_row(*row)

    return table
