import os
import sys
import argparse
import glob
import re

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path",
                        help="the ids of items to search")

    return parser.parse_args()

def main():
    """
    
    """
    args = get_args()

    path = args.path
    os.chdir(path)
    facs_path = 'facs_data'
    sample_group_folders = glob.glob(facs_path + '/*/*')
    for folder in sample_group_folders:
        new_folder = re.subn(r'[\s-]+', '_', folder)[0]
        os.rename(folder, new_folder)

        fcs_files = glob.glob(new_folder + '/*.fcs')
        for fcs in fcs_files:
            new_fcs = re.subn(r'[\s-]+', '_', fcs)[0]
            os.rename(fcs, new_fcs)

if __name__ == "__main__":
    main()