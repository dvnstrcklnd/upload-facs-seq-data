import argparse

from util.navigator import Navigator
from util.provenance_helper import get_item_ids, collect_data, write_to_csv

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--item_ids", nargs='+',
                        help="the ids of items to search")
    parser.add_argument("-p", "--plan_id",
                        help="the ID of the NGS prep plan")
    parser.add_argument("-o", "--operation_type", 
                        help="the OperationType to collect items from")
    parser.add_argument("-n", "--output_name", 
                        help="the name of the Operation Output to collect items from")
    parser.add_argument("-s", "--server", 
                        help="the key pointing to the server instance in secrets.json")
    return parser.parse_args()

def main():
    """
    Creates a manifest file given command-line arguments specifying 
    ngs item ids or an ngs prep plan.
    """
    args = get_args()

    server = args.server
    nav = Navigator(aq_instance=server)
    
    item_ids = get_item_ids(args, nav)

    all_data = collect_data(nav, item_ids)

    write_to_csv(all_data, nav)

if __name__ == "__main__":
    main()