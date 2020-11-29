import click
import os
import sqlite3
from tabulate import tabulate
# Local modules
from utils import rcerror
from utils.rcfuncsandclass import RCfile  # Class
from utils.rcdatabase import checkdatabase  # Function
from utils.rcfuncsandclass import checkshell  # Function
from utils.rcfuncsandclass import blobtotext  # Function
from utils.rcfuncsandclass import rcfileretriever  # Function

# Global variables
home_env_var = os.getenv('HOME')


@click.group(invoke_without_command=True)
@click.option("-v", "--version", is_flag=True, help="Print version info.")
@click.option("--license", is_flag=True, help="Print licensing info.")
def rcmanager(version, license):
    if version:
        click.echo("rcmanager v0.1  Copyright (C) 2020  Jason C. Nucciarone \n\n"
                   "This program comes with ABSOLUTELY NO WARRANTY; \n"
                   "for more details type \"rcmanager --license\". This is free software, \n"
                   "and you are welcome to redistribute it under certain conditions; \n"
                   "type \"rcmanager --license\" for more details.")

    elif license:
        click.echo("""rcmanager: A simple command-line utility for managing rc files.\n
    Copyright (C)  2020  Jason C. Nucciarone

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


@rcmanager.command()
@click.option("-n", "--name", default=None, help="The rc file's name.")
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None,
              help="The rc file's corresponding shell.")
@click.option("-f", "--rcfile", default=None, help="Path to the rc file.")
@click.option("--note", default=None, help="A short description of the rc file.")
@click.option("--yml_file", default=None, help="Upload rc file from YAML file.")
@click.option("-y", "--yes", is_flag=True)
def upload(name, shell, rcfile, note, yml_file, yes):
    """Upload a new rc file to the rc file database."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()

    # Begin the upload process
    if yml_file is not None:
        # TODO: Write method to parse YAML file
        pass

    else:
        if name is None:
            print("Please specify a name for your rc file")
            exit()

        elif shell is None:
            print("Please specify a shell for your rcfile")
            exit()

        elif rcfile is None:
            print("Please specify the path to your rcfile")
            exit()

        else:
            # Verify if user create a note for the rc file
            if note is None:
                note = "null"

            # Initialize rcfile
            upload_file = RCfile(name, shell, rcfile, note)

            # If yes, skip straight to uploading to the database
            if yes:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO rcfile (name, shell, content, note)\n"
                                   "VALUES (?,?,?,?)", (upload_file.getname(), upload_file.getshell(),
                                                        upload_file.getcontent(), upload_file.getnote()))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "upload", e)
                    exit()

                finally:
                    conn.close()

            else:
                upload_file.totable(rcfile)
                prompt = input("Add the above to the database? (y/n): ").lower()
                if prompt == "y":
                    conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO rcfile (name, shell, content, note)\n"
                                       "VALUES (?,?,?,?)", (upload_file.getname(), upload_file.getshell(),
                                                            upload_file.getcontent(), upload_file.getnote()))
                        conn.commit()

                    except sqlite3.Error as e:
                        conn.rollback()
                        rcerror.rcerrormsg(home_env_var, "upload", e)
                        exit()

                    finally:
                        conn.close()

                elif prompt == "n":
                    exit()

                else:
                    print("Please either enter y or n")
                    exit()


@click.option("-n", "--name", default=None, help="Name of the rc file you wish to delete.")
@click.option("-i", "--index", default=None, help="Index of the rc file you wish to delete.")
@rcmanager.command()
def remove(name, index):
    """Remove an rc file from the rc file database."""
    checkdatabase(home_env_var)
    if name is None and index is None:
        print("Please either use -n, --name or -i, --index "
              "to specify which rc file you would like to delete "
              "from the database. Use rcmanager remove --help "
              "for help.")

    elif name is not None and index is None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM rcfile WHERE EXISTS(SELECT * FROM rcfile WHERE name = ?)",
                           (name,))
            conn.commit()
            print("The rc file named {} has been deleted from the rc file database")

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "remove", e)
            exit()

        finally:
            conn.close()

    elif name is None and index is not None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM rcfile WHERE EXISTS(SELECT * FROM rcfile WHERE id = ?)",
                           (index,))
            conn.commit()
            print("The rc file with index {} has been deleted from the rc file database")

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "remove", e)
            exit()

        finally:
            conn.close()

    elif name is not None and index is not None:
        print("Please only use -n, --name or -i, --index. No need for both.")

    else:
        print("Invalid option specified. Please use "
              "rcmanager remove --help for help.")


@click.option("-n", "--name", default=None, help="Name of the rc file whose content you wish to update.")
@click.option("-i", "--index", default=None, help="Index of the rc file whose content you wish to update.")
@click.option("--update_name", default=None, help="Set a new name for the specified rc file.")
@click.option("--update_shell", default=None, help="Set a new shell for the specified rc file.")
@click.option("--update_content", default=None, help="Set new rc file content for specified rc file.\n "
                                                     "Specify the full path to file containing the new content "
                                                     "for the rc file.")
@click.option("--update_note", default=None, help="Set a new note for specified rc file.")
@rcmanager.command()
def update(name, index, update_name, update_shell, update_content, update_note):
    """Update a rc file stored in the rc file database."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if update_shell is not None:
        is_shell_installed = checkshell(update_shell)
        if is_shell_installed is False:
            exit()

    if name is None and index is None:
        print("Please either use -n, --name or -i, --index "
              "to specify which rc file entry you would like to update "
              "in the database. Use rcmanager update --help "
              "for help.")

    elif name is not None and index is None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if update_name is not None:
                try:
                    cursor.execute("UPDATE rcfile SET name = ? WHERE EXISTS(SELECT * FROM rcfile WHERE name = ?)",
                                   (update_name, name))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_shell is not None:
                try:
                    cursor.execute("UPDATE rcfile SET shell = ? WHERE EXISTS(SELECT * FROM rcfile WHERE name = ?)",
                                   (update_shell, name))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_content is not None:
                try:
                    cursor.execute("UPDATE rcfile SET content = ? WHERE EXISTS(SELECT * FROM rcfile WHERE name = ?)",
                                   (update_content, name))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_note is not None:
                try:
                    cursor.execute("UPDATE rcfile SET note = ? WHERE EXISTS(SELECT * FROM rcfile WHERE name = ?)",
                                   (update_note, name))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "update", e)
            exit()

        finally:
            conn.close()

    elif name is None and index is not None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if update_name is not None:
                try:
                    cursor.execute("UPDATE rcfile SET name = ? WHERE EXISTS(SELECT * FROM rcfile WHERE id = ?)",
                                   (update_name, index))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_shell is not None:
                try:
                    cursor.execute("UPDATE rcfile SET shell = ? WHERE EXISTS(SELECT * FROM rcfile WHERE id = ?)",
                                   (update_shell, index))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_content is not None:
                try:
                    cursor.execute("UPDATE rcfile SET content = ? WHERE EXISTS(SELECT * FROM rcfile WHERE id = ?)",
                                   (update_content, index))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

            if update_note is not None:
                try:
                    cursor.execute("UPDATE rcfile SET note = ? WHERE EXISTS(SELECT * FROM rcfile WHERE id = ?)",
                                   (update_note, index))
                    conn.commit()

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "update", e)
                    exit()

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "update", e)
            exit()

        finally:
            conn.close()

    elif name is not None and index is not None:
        print("Please only use -n, --name or -i, --index. No need for both.")

    else:
        print("Invalid option specified. Please use "
              "rcmanager update --help for help.")


@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None, help="Shell's RC file to reset")
@click.option("-n", "--name", default=None, help="Name of skel file to reset to.\n"
                                                 "\nDefaults for each shell are:\n"
                                                 "\nbash_default\n"
                                                 "csh_default\n"
                                                 "ksh_default\n"
                                                 "tcsh_default\n"
                                                 "zsh_default\n"
                                                 "fish_default")
@click.option("-i", "--index", default=None, help="Index of skel file to rest to.")
@click.option("--backup/--no-backup", default=True, help="Backup current rc file. Default is backup")
@rcmanager.command()
def reset(shell, name, index, backup):
    """Reset the specified shell's rc file."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()

    if shell is None:
        print("Please specify what shell you would like to reset.")
        exit()

    if index is not None and name is not None:
        print("Please only use -n, --name or -i, --index. No need for both.")

    # Default method for if the user only specifies the shell
    elif index is None and name is None:
        # Select the default skel file in the skel table
        if shell.lower() == "bash":
            name = "bash_default"

        elif shell.lower() == "csh":
            name = "csh_default"

        elif shell.lower() == "ksh":
            name = "ksh_default"

        elif shell.lower() == "tcsh":
            name = "tcsh_default"

        elif shell.lower() == "zsh":
            name = "zsh_default"

        elif shell.lower() == "fish":
            name = "fish_default"

        else:
            print("Invalid shell specified. Use 'rcmanager reset --help' for available shell options")
            exit()

        # Once default skel file is selected, pull and swap
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()

        try:
            # If the user wants a backup of their rc file
            if backup:
                backup_file = rcfileretriever(shell.lower(), home_env_var)  # Returns Backup class
                # Delete old backup of shell
                cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                               (shell.lower(),))
                # Insert new backup into database
                cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                               (backup_file.getshell(), backup_file.toblob()))
                # Once new backup is added, delete old rc file
                os.remove(backup_file.getpath())
                # Pull file from skel and set as new rc file
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(backup_file.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Commit changes to backup table
                conn.commit()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(backup_file.getrcfilename()))

            else:
                # Use backup class to get path, but only need it for path
                file_to_replace = rcfileretriever(shell.lower(), home_env_var)
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(file_to_replace.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(file_to_replace.getrcfilename()))

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "reset", e)
            exit()

        finally:
            conn.close()

    # Use skel file specified by index
    elif index is not None and name is None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if backup:
                backup_file = rcfileretriever(shell.lower(), home_env_var)  # Returns Backup class
                # Delete old backup of shell
                cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                               (shell.lower(),))
                # Insert new backup into database
                cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                               (backup_file.getshell(), backup_file.toblob()))
                # Once new backup is added, delete old rc file
                os.remove(backup_file.getpath())
                # Pull file from skel and set as new rc file
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE id = ?", (index,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(backup_file.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Commit changes to backup table
                conn.commit()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(backup_file.getrcfilename()))

            else:
                # Use backup class to get path, but only need it for path
                file_to_replace = rcfileretriever(shell.lower(), home_env_var)
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE id = ?", (index,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(file_to_replace.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(file_to_replace.getrcfilename()))

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "reset", e)
            exit()

        finally:
            conn.close()

    # Use skel file specified by name
    elif index is None and name is not None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if backup:
                backup_file = rcfileretriever(shell.lower(), home_env_var)  # Returns Backup class
                # Delete old backup of shell
                cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                               (shell.lower(),))
                # Insert new backup into database
                cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                               (backup_file.getshell(), backup_file.toblob()))
                # Once new backup is added, delete old rc file
                os.remove(backup_file.getpath())
                # Pull file from skel and set as new rc file
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(backup_file.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Commit changes to backup table
                conn.commit()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(backup_file.getrcfilename()))

            else:
                # Use backup class to get path, but only need it for path
                file_to_replace = rcfileretriever(shell.lower(), home_env_var)
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file, home_env_var)

                # Write out contents to new rc file
                fout = open(file_to_replace.getpath(), "wt")
                fout.write(new_rc_content)
                fout.close()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(file_to_replace.getrcfilename()))

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "reset", e)
            exit()

        finally:
            conn.close()

    else:
        print("Invalid option specified. Please use "
              "rcmanager reset --help for help.")


@rcmanager.command()
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None, help="Restore the shell's previous rc file.\n"
                                 "(Uses rc file in backup table)")
@click.option("--backup/--no-backup", default=True, help="Backup current rc file. Default is backup")
def restore(shell, backup):
    """Restore a shell's previous rc file."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()

    if shell is None:
        print("Please specify which shell you want to restore.")

    else:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            # Pull down backup entry before
            backup_file = cursor.execute("SELECT content FROM backup WHERE shell = ?", (shell.lower(),))
            backup_file_contents = blobtotext(backup_file, home_env_var)

            # Get old rc file info
            new_backup = rcfileretriever(shell.lower(), home_env_var)
            if backup:
                # Delete old backup from backup table
                cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                               (new_backup.getshell(),))

                # Upload new backup
                cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                               (new_backup.getshell(), new_backup.toblob()))

                conn.commit()

            # Delete old rc file and write new one
            os.remove(new_backup.getpath())

            fout = open(new_backup.getpath(), "wt")
            fout.write(backup_file_contents)
            fout.close()

            # Tell user to log out and log back in
            print("In order for changes to {} to take effect, "
                  "please logout and log back into your current "
                  "session.".format(new_backup.getrcfilename()))

        except sqlite3.Error as e:
            conn.rollback()
            rcerror.rcerrormsg(home_env_var, "restore", e)
            exit()

        finally:
            conn.close()


@rcmanager.command()
@click.option("-t", "--table", type=click.Choice(["rcfile", "skel", "backup"]),
              default=None, help="The table to list out.")
@click.option("-i", "--index", default=None, help="List an RC file based on its index within the table.")
@click.option("-n", "--name", default=None, help="List an RC file based on its name.")
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None, help="List an RC file based on its shell")
@click.option("--showrc", is_flag=True, help="Show contents of the uploaded RC file.\n "
                                             "Warning: Output can potentially get very large")
def list(table, index, name, shell, showrc):
    """List the contents of a table in the rc file database."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()

    # Global variables for function
    headers = ["Index", "Name", "Shell", "Note"]
    fmt = "grid"
    showrc_headers = ["Index", "Name", "Shell", "Contents", "Note"]
    showrc_fmt = "grid"
    backup_headers = ["Index", "Shell"]
    backup_showrc_headers = ["Index", "Shell", "Contents"]

    if table is None:
        print("Please specify which table you want to list out.")
        exit()

    elif table == "rcfile":
        if index is None and name is None and shell is None:
            # List all contents of the table
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM rcfile")
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM rcfile")
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is not None and name is None and shell is None:
            # List content by index
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM rcfile WHERE id = ?",
                                             (index,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM rcfile WHERE id = ?", (index,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is None and name is not None and shell is None:
            # List content by name
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM rcfile WHERE name = ?",
                                             (name,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM rcfile WHERE name = ?", (name,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is None and name is None and shell is not None:
            # List content by shell
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM rcfile WHERE shell = ?",
                                             (shell,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM rcfile WHERE shell = ?", (shell,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        else:
            print("Please only use one option to list rc files")

    elif table == "skel":
        if index is None and name is None and shell is None:
            # List all contents of the table
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM skel")
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM skel")
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is not None and name is None and shell is None:
            # List content by index
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM skel WHERE id = ?",
                                             (index,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM skel WHERE id = ?", (index,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is None and name is not None and shell is None:
            # List content by name
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM skel WHERE name = ?",
                                             (name,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM skel WHERE name = ?", (name,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is None and name is None and shell is not None:
            # List content by shell
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, content, note FROM skel WHERE shell = ?",
                                             (shell,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], blobtotext(row[3], home_env_var), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, name, shell, note FROM skel WHERE shell = ?", (shell,))
                    # Create table to print out using tabulate
                    table = []
                    for row in results:
                        table.append([row[0], row[1], row[2], row[3]])

                    print(tabulate(table, headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        else:
            print("Please only use one option to list rc files")

    elif table == "backup":
        if index is None and name is None and shell is None:
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell, content FROM backup")
                    table = []
                    for row in results:
                        table.append([row[0], row[1], blobtotext(row[2], home_env_var)])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell FROM backup")
                    table = []
                    for row in results:
                        table.append([row[0], row[1]])

                    print(tabulate(table, backup_headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is not None and name is None and shell is None:
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell, content FROM backup WHERE id = ?", (index,))
                    table = []
                    for row in results:
                        table.append([row[0], row[1], blobtotext(row[2], home_env_var)])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell FROM backup WHERE id = ?", (index,))
                    table = []
                    for row in results:
                        table.append([row[0], row[1]])

                    print(tabulate(table, backup_headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        elif index is None and name is not None and shell is None:
            print("Backups do not have names, please use either:\n "
                  "-i, --index\n "
                  "-s, --shell\n "
                  "to list the backups table")

        elif index is None and name is None and shell is not None:
            if showrc:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell, content FROM backup WHERE shell = ?", (shell,))
                    table = []
                    for row in results:
                        table.append([row[0], row[1], blobtotext(row[2], home_env_var)])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

            else:
                conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
                cursor = conn.cursor()
                try:
                    results = cursor.execute("SELECT id, shell FROM backup WHERE shell = ?", (shell,))
                    table = []
                    for row in results:
                        table.append([row[0], row[1]])

                    print(tabulate(table, backup_headers, tablefmt=fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    rcerror.rcerrormsg(home_env_var, "list", e)
                    exit()

                finally:
                    conn.close()

        else:
            print("Please only use one option to list rc files")

    else:
        print("Invalid option specified, please try again.")
        exit()


@rcmanager.command()
@click.option("-s", "--shell", type=click.Choice(["bash", "csh", "ksh",
                                                  "tcsh", "zsh", "fish"],
                                                 case_sensitive=False),
              default=None, help="Swap out shell's current rc file")
@click.option("-n", "--name", default=None, help="Name of rc file to swap current one with.")
@click.option("-i", "--index", default=None, help="Index of rc file to swap current one with.")
@click.option("--backup/--no-backup", default=True, help="Backup current rc file. Default is backup")
def swap(shell, name, index, backup):
    """Swap rc files."""
    checkdatabase(home_env_var)

    # Check if shell is installed on system
    if shell is not None:
        is_shell_installed = checkshell(shell)
        if is_shell_installed is False:
            exit()

    if shell is None:
        print("Please specify the shell whose rc file you would like to swap.")

    else:
        if name is None and index is None:
            print("Please either use --name or --index to specify \n"
                  "which rc file to use from the database.")

        elif name is not None and index is None:
            conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
            cursor = conn.cursor()
            try:
                results = cursor.execute("SELECT shell, content FROM rcfile WHERE name = ?", (name,))
                tmp_list = []
                for row in results:
                    tmp_list.append(row[0])
                    tmp_list.append(row[1])

                # Verify that the shells match
                # If they don't, exit program
                if tmp_list[0] != shell:
                    print("Hmm. It seems that the shell of the requested rc file "
                          "does not match with the requested shell. Please verify "
                          "that the requested rc file's shell matches the shell "
                          "you are swapping rc files for.")
                    exit()

                # Convert blob to text
                swap_file_contents = blobtotext(tmp_list[1], home_env_var)
                # Backup the current rc file
                new_backup = rcfileretriever(shell.lower(), home_env_var)
                if backup:
                    # Delete old backup from backup table
                    cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                                   (new_backup.getshell(),))

                    # Upload new backup
                    cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                                   (new_backup.getshell(), new_backup.toblob()))

                    conn.commit()

                # Now write new rc file
                os.remove(new_backup.getpath())

                fout = open(new_backup.getpath(), "wt")
                fout.write(swap_file_contents)
                fout.close()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(new_backup.getrcfilename()))

            except sqlite3.Error as e:
                conn.rollback()
                rcerror.rcerrormsg(home_env_var, "swap", e)
                exit()

            finally:
                conn.close()

        elif name is None and index is not None:
            conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
            cursor = conn.cursor()
            try:
                results = cursor.execute("SELECT shell, content FROM rcfile WHERE id = ?", (index,))
                tmp_list = []
                for row in results:
                    tmp_list.append(row[0])
                    tmp_list.append(row[1])

                # Verify that the shells match
                # If they don't, exit program
                if tmp_list[0] != shell:
                    print("Hmm. It seems that the shell of the requested rc file "
                          "does not match with the requested shell. Please verify "
                          "that the requested rc file's shell matches the shell "
                          "you are swapping rc files for.")
                    exit()

                # Convert blob to text
                swap_file_contents = blobtotext(tmp_list[1], home_env_var)
                # Backup the current rc file
                new_backup = rcfileretriever(shell.lower(), home_env_var)
                if backup:
                    # Delete old backup from backup table
                    cursor.execute("DELETE FROM backup WHERE EXISTS(SELECT * FROM backup WHERE shell = ?)",
                                   (new_backup.getshell(),))

                    # Upload new backup
                    cursor.execute("INSERT INTO backup (shell, content) VALUES (?,?)",
                                   (new_backup.getshell(), new_backup.toblob()))

                    conn.commit()

                # Now write new rc file
                os.remove(new_backup.getpath())

                fout = open(new_backup.getpath(), "wt")
                fout.write(swap_file_contents)
                fout.close()

                # Tell user to log out and log back in
                print("In order for changes to {} to take effect, "
                      "please logout and log back into your current "
                      "session.".format(new_backup.getrcfilename()))

            except sqlite3.Error as e:
                conn.rollback()
                rcerror.rcerrormsg(home_env_var, "swap", e)
                exit()

            finally:
                conn.close()

        elif name is not None and index is not None:
            print("Please only use either --name or --index. \n"
                  "No need to use both.")

        else:
            print("Invalid option specified. Please use "
                  "rcmanager swap --help for help")


if __name__ == '__main__':
    rcmanager()
