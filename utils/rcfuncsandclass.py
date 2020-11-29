import os
from tabulate import tabulate
# Local modules
from .command import command


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


# checkshell verifies that a shell is installed on the system.
# If not, the rcmanager and rcskel will exit before doing anything.
def checkshell(shell):
    if shell.lower() == "bash":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that bash is not installed on your system.\n\n"
                  "To install bash on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install bash\n\n"
                  "To install bash on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install bash")
            return False

    elif shell.lower() == "csh":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that csh is not installed on your system.\n\n"
                  "To install csh on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install csh\n\n"
                  "To install csh on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install tcsh")
            return False

    elif shell.lower() == "ksh":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that ksh is not installed on your system.\n\n"
                  "To install ksh on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install ksh\n\n"
                  "To install ksh on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install ksh")
            return False

    elif shell.lower() == "tcsh":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that tcsh is not installed on your system.\n\n"
                  "To install tcsh on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install tcsh\n\n"
                  "To install tcsh on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install tcsh")
            return False

    elif shell.lower() == "zsh":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that zsh is not installed on your system.\n\n"
                  "To install zsh on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install zsh\n\n"
                  "To install zsh on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install zsh")
            return False

    elif shell.lower() == "fish":
        is_installed = command(shell.lower())
        if is_installed is True:
            return True

        else:
            print("Hmm. It seems that fish is not installed on your system.\n\n"
                  "To install fish on Debian/Ubuntu systems:\n\n"
                  "$ sudo apt-get install fish\n\n"
                  "To install fish on CentOS/Fedora/RHEL:\n\n"
                  "$ sudo dnf install fish")
            return False

    else:
        print("Shell passed as argument not recognized.")
        return False


# blobtotext converts binary large objects back into files
def blobtotext(blob_data, env_home):
    tmp_file = "{}/.local/rcmanager/tmp/tmp_file.txt".format(env_home)
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


# Function to retrieve rc file from proper location
# Returns Backup class
def rcfileretriever(shell, env_home):
    # Get RC file based on specified shell
    if shell.lower() == "bash":
        # .bashrc is usually located in users home directory
        bash_file = Backup(shell.lower(), env_home + "/.bashrc", ".bashrc")
        return bash_file

    elif shell.lower() == "csh":
        # .cshrc is usually located in users home directory
        csh_file = Backup(shell.lower(), env_home + "/.cshrc", ".cshrc")
        return csh_file

    elif shell.lower() == "ksh":
        # .kshrc is also usually located in the home directory
        ksh_file = Backup(shell.lower(), env_home + "/.kshrc", ".kshrc")
        return ksh_file

    elif shell.lower() == "tcsh":
        # .tcshrc is in the home directory too
        tcsh_file = Backup(shell.lower(), env_home + "/.tcshrc", ".tcshrc")
        return tcsh_file

    elif shell.lower() == "zsh":
        # Everyone is in the home directory except for fish
        zsh_file = Backup(shell.lower(), env_home + "/.zshrc", ".zshrc")
        return zsh_file

    elif shell.lower() == "fish":
        # In ~/.config, always gotta be special
        # Always my favorite though boo <3
        fish_file = Backup(shell.lower(), env_home + "/.config/fish/config.fish", "config.fish")
        return fish_file

    else:
        return "Error file not found"
    

# Local classes
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


# Local functions
# toblob converts files to binary large objects
def toblob(filepath):
    if os.path.exists(filepath):
        fin = open(filepath, "rb")
        tmp_blob = fin.read()
        fin.close()
        return tmp_blob

    else:
        return "err"
    
    
# Ensures that strings are under a specific length
def underlength(string, max_length):
    if len(string) <= max_length:
        return True

    else:
        return False
