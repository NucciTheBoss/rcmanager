import click
import os
import sqlite3
from tabulate import tabulate
# Local modules
from utils.rcdatabase import checkdatabase  # Function
from utils.rcfuncsandclass import checkshell  # Function


# Global variables
home_env_var = os.getenv('HOME')


@click.group(invoke_without_command=True)
@click.option("-v", "--version", is_flag=True, help="Print version info.")
@click.option("--license", is_flag=True, help="Print licensing info.")
def rcskel(version, license):
    if version:
        click.echo("rcskel v0.1  Copyright (C) 2020  Jason C. Nucciarone \n\n"
                   "This program comes with ABSOLUTELY NO WARRANTY; \n"
                   "for more details type \"rcskel --license\". This is free software, \n"
                   "and you are welcome to redistribute it under certain conditions; \n"
                   "type \"rcskel --license\" for more details.")

    elif license:
        click.echo("""rcskel: A simple command-line utility for managing skeleton rc files (included with rcmanager 
        package). Copyright (C)  2020  Jason C. Nucciarone 

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.""")


@rcskel.command()
@click.option("-n", "--name", default=None, help="The skeleton rc file's name.")
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None,
              help="The skeleton rc file's corresponding shell.")
@click.option("-f", "--rcfile", default=None, help="Path to the skeleton rc file.")
@click.option("--note", default=None, help="A short description of the skeleton rc file.")
@click.option("--yml_file", default=None, help="Upload a skeleton rc file from a YAML file.")
@click.option("-y", "--yes", is_flag=True)
def upload(name, shell, rcfile, note, yml_file, yes):
    """Upload a new skeleton rc file to the rc file database."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()


@rcskel.command()
@click.option("-n", "--name", default=None, help="Name of the skeleton rc file you wish to delete.")
@click.option("-i", "--index", default=None, help="Index of the skeleton rc file you wish to delete.")
def remove(name, index):
    """Remove a skeleton rc file from the rc file database."""
    checkdatabase(home_env_var)


@rcskel.command()
@click.option("-n", "--name", default=None, help="Name of the skeleton rc file whose content you wish to update.")
@click.option("-i", "--index", default=None, help="Index of the skeleton rc file whose content you wish to update.")
@click.option("--update_name", default=None, help="Set a new name for the specified skeleton rc file.")
@click.option("--update_shell", default=None, help="Set a new shell for the specified skeleton rc file.")
@click.option("--update_content", default=None, help="Set new rc file content for specified skeleton rc file.\n "
                                                     "Specify the full path to file containing the new content "
                                                     "for the skeleton rc file.")
@click.option("--update_note", default=None, help="Set a new note for specified skeleton rc file.")
def update(name, index, update_name, update_shell, update_content, update_note):
    """Update a rc file stored in the rc file database."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if update_shell is not None:
        is_shell_installed = checkshell(update_shell)
        if is_shell_installed is False:
            exit()


@rcskel.command()
@click.option("-n", "--name", default=None, help="List a skeleton rc file based on its name in the skel table.")
@click.option("-i", "--index", default=None, help="List a skeleton rc file based on its index in the skel table.")
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None, help="List a skeleton rc file based on its shell")
@click.option("--showrc", is_flag=True, help="Show contents of the skeleton rc file.\n "
                                             "Warning: Output can potentially get very large")
def list(name, index, shell, showrc):
    """List the contents of the skel table in the rc file database."""
    checkdatabase(home_env_var)

    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()


@rcskel.command()
@click.option("-n", "--name", default=None, help="Export a skeleton rc file to YAML based on its name in the skel "
                                                 "table.")
@click.option("-i", "--index", default=None, help="Export a skeleton rc file to YAML based on its index in the skel "
                                                  "table.")
def export():
    """Export skeleton rc file to YAML"""
    checkdatabase(home_env_var)


@rcskel.command()
def dump():
    """Dump rc file database to SQL"""
    checkdatabase(home_env_var)


if __name__ == '__main__':
    rcskel()
