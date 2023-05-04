'''
Copyright 2023 Robin Onsay

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import argparse
from barkbright import cli
from barkbright import demo


parser = argparse.ArgumentParser(prog='BarkBright',
                                 description='Voice Enabled LED Light Control')
parser.add_argument('-c', '--cli', action='store_true')
parser.add_argument('-t', '--train', action='store_true')

args = parser.parse_args()

if args.cli:
    cli.main(train=args.train)
else:
    demo.main(train=args.train)

