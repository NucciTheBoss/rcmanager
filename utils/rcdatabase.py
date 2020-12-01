import os
import sqlite3
import requests
# Local modules
from .rcerror import rcerrormsg
from .command import command


# Check for the rcmanager database. If not available then create
# a new database to be used by rcmanager
def checkdatabase(env_home):
    if os.path.exists("{}/.local/rcmanager/data/rcmanager.db".format(env_home)):
        return

    else:
        # Create necessary directories
        rc_manager_dirs = ["{}/.local/rcmanager/data".format(env_home),
                           "{}/.local/rcmanager/logs".format(env_home),
                           "{}/.local/rcmanager/tmp".format(env_home)]

        for dirs in rc_manager_dirs:
            try:
                os.makedirs(dirs)

            except FileExistsError:
                pass

        db = os.open("{}/.local/rcmanager/data/rcmanager.db".format(env_home), os.O_RDWR | os.O_CREAT)  # Create db file
        os.close(db)

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

            # Initialize skel files list
            skel_files = list()

            # Once tables are created populate the skel table
            # Try to pull most recent version off of GitHub
            try:
                # Where the skel files are currently hosted
                urls = ["https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.bashrc",
                        "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.cshrc",
                        "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.kshrc",
                        "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.tcshrc",
                        "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/.zshrc",
                        "https://raw.githubusercontent.com/NucciTheBoss/rcmanager/master/share/skel/config.fish"]

                if command("bash") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_bashrc".format(env_home)
                    urlretreiver(urls[0], path_name)
                    skel_files.append(("bash", path_name))

                if command("csh") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_cshrc".format(env_home)
                    urlretreiver(urls[1], path_name)
                    skel_files.append(("csh", path_name))

                if command("ksh") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_kshrc".format(env_home)
                    urlretreiver(urls[2], path_name)
                    skel_files.append(("ksh", path_name))

                if command("tcsh") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_tcshrc".format(env_home)
                    urlretreiver(urls[3], path_name)
                    skel_files.append(("tcsh", path_name))

                if command("zsh") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_zshrc".format(env_home)
                    urlretreiver(urls[4], path_name)
                    skel_files.append(("zsh", path_name))

                if command("fish") is True:
                    path_name = "{}/.local/rcmanager/tmp/tmp_fish".format(env_home)
                    urlretreiver(urls[5], path_name)
                    skel_files.append(("fish", path_name))

            except IOError as e:
                rcerrormsg(env_home, "initialization", e)
                exit()

            # Loop through list and add to rc file database
            for item in skel_files:
                fin = open(item[1], "rb")
                tmp_blob = fin.read()
                tmp_name = "{}_default".format(item[1])
                tmp_note = "The default rc file for the {} shell".format(item[0])
                cursor.execute('''INSERT INTO skel(name, shell, content, note)
                                    VALUES(?,?,?,?)''', (tmp_name, item[0], tmp_blob, tmp_note))

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            rcerrormsg(env_home, "initialization", e)
            exit()

        finally:
            conn.close()


# Local functions
def urlretreiver(url, output_path):
    r = requests.get(url, allow_redirects=True)
    with open(output_path, "wb") as fout:
        fout.write(r.content)
