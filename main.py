# main.py

import sys


def main():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    elif len(sys.argv) > 2:
        print("too many arguments provided")
        sys.exit(1)
    else:
        BASE_URL = sys.argv[1]
        print(f"starting crawl of: {BASE_URL}")


if __name__ == "__main__":
    main()
