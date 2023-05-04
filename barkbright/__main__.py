import argparse
from barkbright.cli import main

parser = argparse.ArgumentParser(prog='BarkBright',
                                 description='Voice Enabled LED Light Control')
parser.add_argument('-c', '--cli', action='store_true')
parser.add_argument('-t', '--train', action='store_true')

args = parser.parse_args()

if args.cli:
    main(train=args.train)

