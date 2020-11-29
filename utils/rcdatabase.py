import os
import requests
# Local modules
from .rcerror import rcerrormsg


# Check for the rcmanager database. If not available then create
# a new database to be used by rcmanager
def checkdatabase(env_home):
    if os.path.exists("{}/.local/rcmanager/data/rcmanager.db".format(env_home)):
        return

    else:
        os.system("mkdir -p {}/.local/rcmanager/data".format(env_home))
        os.system("mkdir -p {}/.local/rcmanager/logs".format(env_home))
        os.system("mkdir -p {}/.local/rcmanager/tmp".format(env_home))
        os.system("touch {}/.local/rcmanager/data/rcmanager.db".format(env_home))  # Create db file

        # Populate the database with default tables
        conn = sqlite3.connect("{}/.local/rcmanager/data/rcmanager.db".format(env_home))
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE rcfile(\n'
                           '                                id INTEGER PRIMARY KEY,\n'
                           '                                name VARCHAR(20) UNIQUE,\n'
                           '                                shell VARCHAR(10),\n'
                           '                                content BLOB,\n'
                           '                                note VARCHAR(100))')
            cursor.execute('CREATE TABLE skel(\n'
                           '                                id INTEGER PRIMARY KEY,\n'
                           '                                name VARCHAR(20) UNIQUE,\n'
                           '                                shell VARCHAR(10),\n'
                           '                                content BLOB,\n'
                           '                                note VARCHAR(100))')
            cursor.execute('CREATE TABLE backup(\n'
                           '                                id INTEGER PRIMARY KEY,\n'
                           '                                shell VARCHAR(10),\n'
                           '                                content BLOB)')

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

            except OSError as e:
                rcerrormsg(env_home, "initialization", e)
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
            rcerrormsg(env_home, "initialization", e)
            exit()

        finally:
            conn.close()