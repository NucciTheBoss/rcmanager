import click
import os
import sqlite3
from tabulate import tabulate

# Global variables
home_env_var = os.getenv('HOME')


# Check for the rcmanager database. If not available then create
# a new database to be used by rcmanager
def checkdatabase():
    if os.path.exists("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var)):
        return

    else:
        os.system("mkdir -p {}/.local/rcmanager/data".format(home_env_var))
        os.system("mkdir -p {}/.local/rcmanager/logs".format(home_env_var))
        os.system("mkdir -p {}/.local/rcmanager/tmp".format(home_env_var))
        os.system("touch {}/.local/rcmanager/data/rcmanager.db".format(home_env_var))  # Create db file

        # Populate the database with default tables
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            cursor.execute('''CREATE TABLE rcfile(
                                id INTEGER PRIMARY KEY,
                                name VARCHAR(20) UNIQUE,
                                shell VARCHAR(10),
                                content BLOB,
                                note VARCHAR(100))''')
            cursor.execute('''CREATE TABLE skel(
                                id INTEGER PRIMARY KEY,
                                name VARCHAR(20) UNIQUE,
                                shell VARCHAR(10),
                                content BLOB,
                                note VARCHAR(100))''')
            cursor.execute('''CREATE TABLE backup(
                                id INTEGER PRIMARY KEY,
                                shell VARCHAR(10),
                                content BLOB)''')

            # Once tables are created populate the skel table
            # Pull off of github for the time being
            try:
                os.system("curl -s -o /tmp/tmp_bashrc "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.bashrc")
                os.system("curl -s -o /tmp/tmp_cshrc "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.cshrc")
                os.system("curl -s -o /tmp/tmp_kshrc "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.kshrc")
                os.system("curl -s -o /tmp/tmp_tcshrc "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.tcshrc")
                os.system("curl -s -o /tmp/tmp_zshrc "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.zshrc")
                os.system("curl -s -o /tmp/tmp_fish "
                          "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/config.fish")

            except OSError:
                fout = open("{}/.local/rcmanager/logs/initialization.err.log".format(home_env_var), "wt")
                print("The was an issue retrieving skel files from GitHub. \n"
                      "Please contact owner of rcmanager repository", file=fout)
                fout.close()
                print("An error occurred! Please check log file in \n"
                      "~/.local/rcmanager/logs")
                exit()

            # Insert skel files into skel table
            # Create list with name and location of skel rc file
            skel_files = [("/tmp/tmp_bashrc", "bash"), ("/tmp/tmp_cshrc", "csh"), ("/tmp/tmp_kshrc", "ksh"),
                          ("/tmp/tmp_tcshrc", "tcsh"), ("/tmp/tmp_zshrc", "zsh"), ("/tmp/tmp_fish", "fish")]

            # Loop through list and add to rc file database
            for item in skel_files:
                fin = open(item[0], "rb")
                tmp_blob = fin.read()
                tmp_name = "{}_default".format(item[1])
                tmp_note = "The default rc file for the {} shell".format(item[1])
                cursor.execute('''INSERT INTO skel(name, shell, content, note)
                                    VALUES(?,?,?,?)''', (tmp_name, item[1], tmp_blob, tmp_note))

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            fout = open("{}/.local/rcmanager/logs/initialization.err.log".format(home_env_var), "wt")
            print(e, file=fout)
            fout.close()
            print("An error occurred! Please check log file in \n"
                  "~/.local/rcmanager/logs")
            exit()

        finally:
            conn.close()


def toblob(filepath):
    if os.path.exists(filepath):
        fin = open(filepath, "rb")
        tmp_blob = fin.read()
        fin.close()
        return tmp_blob

    else:
        return "err"


def blobtotext(blob_data):
    tmp_file = "{}/.local/rcmanager/tmp/tmp_file.txt".format(home_env_var)
    # Write out the blob data to a temp text file
    fout = open(tmp_file, "wb")
    fout.write(blob_data)
    fout.close()

    # Open the text file and return the text data
    fin = open(tmp_file, "rt")
    tmp_txt = fin.read()
    fin.close()
    os.remove(tmp_file)
    return tmp_txt


def underlength(string, max_length):
    if len(string) <= max_length:
        return True

    else:
        return False


# Function to retrieve RC file from proper location
# Returns Backup class
def rcfileretriever(shell):
    # Get RC file based on specified shell
    if shell.lower() == "bash":
        # .bashrc is usually located in users home directory
        bash_file = Backup(shell.lower(), home_env_var + "/.bashrc", ".bashrc")
        return bash_file

    elif shell.lower() == "csh":
        # .cshrc is usually located in users home directory
        csh_file = Backup(shell.lower(), home_env_var + "/.cshrc", ".cshrc")
        return csh_file

    elif shell.lower() == "ksh":
        # .kshrc is also usually located in the home directory
        ksh_file = Backup(shell.lower(), home_env_var + "/.kshrc", ".kshrc")
        return ksh_file

    elif shell.lower() == "tcsh":
        # .tcshrc is in the home directory too
        tcsh_file = Backup(shell.lower(), home_env_var + "/.tcshrc", ".tcshrc")
        return tcsh_file

    elif shell.lower() == "zsh":
        # Everyone is in the home directory except for fish
        zsh_file = Backup(shell.lower(), home_env_var + "/.zshrc", ".zshrc")
        return zsh_file

    elif shell.lower() == "fish":
        # In ~/.config, always gotta be special
        # Always my favorite though boo <3
        fish_file = Backup(shell.lower(), home_env_var + "/.config/fish/config.fish", "config.fish")
        return fish_file

    else:
        return "Error file not found"


# Rc file class to encapsulate rc file data
class RCfile:
    def __init__(self, name, shell, content, note):
        if underlength(name, 20):
            self.name = name

        else:
            print("{}: Over 20 characters. Please shorten the name".format(name))
            exit()

        self.shell = shell

        # Verify that content is a valid rc file
        tmp_content = toblob(content)
        if tmp_content == "err":
            print("{}: Could not find rcfile. Please check your path".format(content))
            exit()

        else:
            self.content = tmp_content  # BLOB of rcfile

        if underlength(note, 100):
            self.note = note  # A short description of the rcfile

        else:
            print("{}: Over 100 characters. Please shorten the note".format(note))
            exit()

    def getname(self):
        return self.name

    def getshell(self):
        return self.shell

    def getcontent(self):
        return self.content

    def getnote(self):
        return self.note

    def setname(self, new_name):
        if underlength(new_name, 20):
            self.name = new_name

        else:
            print("{}: Over 20 characters. Please shorten the name".format(new_name))
            exit()

    def setshell(self, new_shell):
        self.shell = new_shell

    def setcontent(self, new_content):
        tmp_content = toblob(new_content)
        if tmp_content == "err":
            print("{}: Could not find rcfile. Please check your path".format(new_content))
            exit()

        else:
            self.content = tmp_content

    def setnote(self, new_note):
        if underlength(new_note, 100):
            self.note = new_note  # A short description of the rcfile

        else:
            print("{}: Over 100 characters. Please shorten the note".format(new_note))
            exit()

    def totable(self, rcfile_path):
        table = [["Name:", self.name], ["Shell:", self.shell],
                 ["Rc File:", rcfile_path], ["Note:", self.note]]
        print(tabulate(table, tablefmt="rst"))


# Backup class to encapsulate backup file data
class Backup:
    def __init__(self, shell, path_to_rc_file, rc_file_name):
        self.shell = shell
        self.path_to_rc_file = path_to_rc_file
        self.rc_file_name = rc_file_name

    def getshell(self):
        return self.shell.lower()

    def getpath(self):
        return self.path_to_rc_file

    def getrcfilename(self):
        return self.rc_file_name

    def toblob(self):
        return toblob(self.path_to_rc_file)


# TODO: Write remove method
# TODO: Write update method
# TODO: Write restore method
# TODO: Write skel method
# TODO: Write swap method
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

    else:
        click.echo("rcmanager v0.1  Copyright (C) 2020  Jason C. Nucciarone \n\n"
                   "This program comes with ABSOLUTELY NO WARRANTY; \n"
                   "for more details type \"rcmanager --license\". This is free software, \n"
                   "and you are welcome to redistribute it under certain conditions; \n"
                   "type \"rcmanager --license\" for more details.")


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
    checkdatabase()
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
                    fout = open("{}/.local/rcmanager/logs/upload.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        fout = open("{}/.local/rcmanager/logs/upload.err.log".format(home_env_var), "wt")
                        print(e, file=fout)
                        fout.close()
                        print("An error occurred! Please check log file in \n"
                              "~/.local/rcmanager/logs")
                        exit()

                    finally:
                        conn.close()

                elif prompt == "n":
                    exit()

                else:
                    print("Please either enter y or n")
                    exit()


@rcmanager.command()
def remove():
    """Remove an rc file from the rc file database."""
    checkdatabase()


@rcmanager.command()
def update():
    """Update a rc file stored in the rc file database."""
    checkdatabase()


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
@click.option("--backup/--no-backup", default=True, help="Backup switched file. Default is backup")
@rcmanager.command()
def reset(shell, name, index, backup):
    """Reset the specified shell's rc file."""
    checkdatabase()
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
                backup_file = rcfileretriever(shell.lower())  # Returns Backup class
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
                new_rc_content = blobtotext(new_rc_file)

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
                file_to_replace = rcfileretriever(shell.lower())
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file)

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
            fout = open("{}/.local/rcmanager/logs/reset.err.log".format(home_env_var), "wt")
            print(e, file=fout)
            fout.close()
            print("An error occurred! Please check log file in \n"
                  "~/.local/rcmanager/logs")
            exit()

        finally:
            conn.close()

    # Use skel file specified by index
    elif index is not None and name is None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if backup:
                backup_file = rcfileretriever(shell.lower())  # Returns Backup class
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
                new_rc_content = blobtotext(new_rc_file)

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
                file_to_replace = rcfileretriever(shell.lower())
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE id = ?", (index,))
                new_rc_content = blobtotext(new_rc_file)

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
            fout = open("{}/.local/rcmanager/logs/reset.err.log".format(home_env_var), "wt")
            print(e, file=fout)
            fout.close()
            print("An error occurred! Please check log file in \n"
                  "~/.local/rcmanager/logs")
            exit()

        finally:
            conn.close()

    # Use skel file specified by name
    elif index is None and name is not None:
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var))
        cursor = conn.cursor()
        try:
            if backup:
                backup_file = rcfileretriever(shell.lower())  # Returns Backup class
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
                new_rc_content = blobtotext(new_rc_file)

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
                file_to_replace = rcfileretriever(shell.lower())
                # Delete old rc file
                os.remove(file_to_replace.getpath())
                # Get new rc file from skel
                new_rc_file = cursor.execute("SELECT content FROM skel WHERE name = ?", (name,))
                new_rc_content = blobtotext(new_rc_file)

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
            fout = open("{}/.local/rcmanager/logs/reset.err.log".format(home_env_var), "wt")
            print(e, file=fout)
            fout.close()
            print("An error occurred! Please check log file in \n"
                  "~/.local/rcmanager/logs")
            exit()

        finally:
            conn.close()

    else:
        print("Invalid option specified. Please use "
              "rcmanager reset --help for help.")


@rcmanager.command()
def restore():
    """Restore a shell's previous rc file."""
    checkdatabase()


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
    checkdatabase()
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], row[2], blobtotext(row[3]), row[4]])

                    print(tabulate(table, showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], blobtotext(row[2])])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], blobtotext(row[2])])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                        table.append([row[0], row[1], blobtotext(row[2])])

                    print(tabulate(table, backup_showrc_headers, tablefmt=showrc_fmt))

                except sqlite3.Error as e:
                    conn.rollback()
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
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
                    fout = open("{}/.local/rcmanager/logs/list.err.log".format(home_env_var), "wt")
                    print(e, file=fout)
                    fout.close()
                    print("An error occurred! Please check log file in \n"
                          "~/.local/rcmanager/logs")
                    exit()

                finally:
                    conn.close()

        else:
            print("Please only use one option to list rc files")

    else:
        print("Invalid option specified, please try again.")
        exit()


@rcmanager.command()
def skel():
    """Manage skeleton rc files."""
    checkdatabase()


@rcmanager.command()
def swap():
    """Swap rc files."""


if __name__ == '__main__':
    rcmanager()
