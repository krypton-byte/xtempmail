import argparse
import re
arg=argparse.ArgumentParser()
arg.add_argument('--version',type=str)
args=arg.parse_args()
if args.version:
    vers=re.search(r'\/?([0-9][0-9A-Za-z\.]+)', args.version)
    if vers:
        version = vers[1]
    else:
        version = '0.0.1'
    new=open('setup.py').read().replace('0.1',version)
    with open('setup.py','w') as fil:
        print(new)
        fil.write(new)