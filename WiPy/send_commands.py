from ftplib import FTP
from os import listdir
from os.path import isdir
import argparse
from traceback import format_exc


def send_directory(ftp,
                   path='.',
                   ignore=['./send_commands.py']):
    print("Sending Directory: {}".format(path))
    for file_path in listdir(path):
        full_file_path = "{}/{}".format(path, file_path)
        print("Evaluating: {}".format(full_file_path))
        if full_file_path in ignore:
            print("{} in ignore list".format(full_file_path))
            continue
        if full_file_path.split("/")[-1][0] == '.':
            print("Skipping hidden file: {}".format(full_file_path))
            continue

        if isdir(full_file_path):
            try:
                print("Building {}".format(full_file_path))
                ftp.mkd(full_file_path)
            except Exception:
                print("Encountered directory build exception. Assuming directory exists".format(format_exc()))
            send_directory(ftp, path=full_file_path, ignore=ignore)
            continue
        else:
            print("Sending {}".format(full_file_path))
            with open(full_file_path, "rb") as binary:
                ftp.storbinary(cmd="STOR {}".format(full_file_path), fp=binary)
        print("{} transfer complete".format(file_path))


def send_files(server="192.168.1.23",
               user="micro",
               passwd="python",
               ignore_list=['send_commands.py', 'Device.md']):
    print("Attempting to connect to {}".format(server))
    with FTP(host=server,
             user=user,
             passwd=passwd) as ftp:
        print("Connected... configuring and moving to Flash directory")
        ftp.set_pasv(True)
        ftp.cwd("flash")

        send_directory(ftp)

    ftp.close()
    print("Transfers complete")


def main(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", help="WiPy FTP Hostname or IP", default="192.168.1.9")
    parser.add_argument("-u", "--user", help="WiPy FTP username", default="micro")
    parser.add_argument("-p", "--passwd", help="WiPy FTP password", default="python")
    parser.add_argument("-i", "--ignore", help="Files not to upload", action="append", default=['send_commands.py', 'Device.md'])
    args = parser.parse_args()

    send_files(args.server, args.user, args.passwd, args.ignore)


if __name__ == "__main__":
    main()
