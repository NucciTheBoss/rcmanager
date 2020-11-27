import click
import os
import sqlite3
from tabulate import tabulate

# Local modules


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


if __name__ == '__main__':
    rcskel()
