import os


# Sort of like "command -v <executable_name>"
def command(executable):
    # Define function to check is something is a executable
    def isexe(exe):
        return os.path.isfile(exe) and os.access(exe, os.X_OK)

    exec_path, exec_name = os.path.split(executable)
    if exec_path:
        if isexe(executable):
            return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, executable)
            if isexe(exe_file):
                return True

    return False
