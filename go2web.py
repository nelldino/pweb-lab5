import sys
from os import name

def help():
    print("Available commands are:\n\
            go2web -u <URL>         # make an HTTP request to URL and print the response\n\
            go2web -s <search-term> # search the term and print top 10 results\n\
            go2web -h               # show help\n")

def main():
    command = sys.argv

    if len(command) >= 3:
        if command[1] == "-u":
            print("url")
        elif command[1] == "-s":
            print("search")
        else:
            print("Invalid command")

    elif len(command) == 2 and command[1] == "-h":
        help()

    else:
        while True:
            user_input = input("Enter a command (enter go2web -h to see all commands) or 'exit' to exit:\n> ")
            command = user_input.split()
            if len(command) == 0:
                continue
            elif command[0] == "go2web":
                if len(command) >= 3:
                    if command[1] == "-u":
                        print("url")
                    elif command[1] == "-s":
                        print("search")
                    else:
                        print("Invalid command")
                elif len(command) == 2 and command[1] == "-h":
                    help()
                else:
                    print("Invalid command")
            elif command[0] == "exit":
                break
            else:
                print("Invalid command")


if __name__ == '__main__':
    main()
