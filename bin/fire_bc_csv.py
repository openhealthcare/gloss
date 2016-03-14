"""
Script to fire a RFH Blood Culture CSV at an OPAL app
"""
import argparse
import sys

import ffs

# Just in case.
sys.path.append('.')

from gloss.translate.files import RFHBloodCulturesFileType as BloodFile

def fire_csv(args):
    thefile = ffs.Path(args.file)
    bf = BloodFile(thefile)
    bf.process()


def main():
    parser = argparse.ArgumentParser(
        description='Script to fire a blood culture CSV dir at OPAL',
    )
    parser.add_argument('file')
    args = parser.parse_args()
    fire_csv(args)
    return 0

if __name__ == '__main__':
    sys.exit(main())
