def rcerrormsg(env_home, command_name, error):
    fout = open("{}/.local/rcmanager/logs/{}.err.log".format(env_home, command_name), "wt")
    print(error, file=fout)
    fout.close()
    print("An error occurred! Please check log file at \n"
          "{}/.local/rcmanager/logs/{}.err.log".format(env_home, command_name))
