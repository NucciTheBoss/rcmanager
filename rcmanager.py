import click
import os
import sqlite3


# Check for the rcmanager database. If not available then create
# a new database to be used by rcmanager
def checkdatabase():
    home_env_var = os.getenv('HOME')
    if os.path.exists("{}/.local/rcmanager/data/rcmanager.db".format(home_env_var)):
        return

    else:
        os.system("mkdir -p {}/.local/rcmanager/data".format(home_env_var))
        os.system("mkdir -p {}/.local/rcmanager/logs".format(home_env_var))
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
            fout = open("{}/.local/rcmanager/logs/initialization.err.log".format(home_env_var), "wt")
            print(e, file=fout)
            fout.close()
            print("An error occurred! Please check log file in \n"
                  "~/.local/rcmanager/logs")
            exit()

        finally:
            conn.close()


# TODO: Write upload method
# TODO: Write remove method
# TODO: Write update method
# TODO: Write reset method
# TODO: Write restore method
# TODO: Write query method
# TODO: Write skel method
# TODO: Write swap method
@click.group()
def rcmanager():
    pass


@rcmanager.command()
def upload():
    """Upload a new rc file to the rc file database."""
    checkdatabase()


@rcmanager.command()
def remove():
    """Remove an rc file from the rc file database."""
    checkdatabase()


@rcmanager.command()
def update():
    """Update a rc file stored in the rc file database."""
    checkdatabase()


@rcmanager.command()
def reset():
    """Reset the specified shell's rc file."""
    checkdatabase()


@rcmanager.command()
def restore():
    """Restore a shell's previous rc file."""
    checkdatabase()


@rcmanager.command()
def query():
    """Query the rc file database."""
    checkdatabase()


@rcmanager.command()
def skel():
    """Manage skeleton rc files."""
    checkdatabase()


main = click.CommandCollection(sources=[rcmanager])

if __name__ == '__main__':
    main()
