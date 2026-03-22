import argparse

def main():
    parser = argparse.ArgumentParser(description="go2web - a simple HTTP client")
    parser.add_argument("-u", help="make an HTTP request to the specified URL and print the response", metavar="URL")
    parser.add_argument("-s", nargs="+", help="make an HTTP request to search the term using your favorite search engine and print top 10 results", metavar="term")
    args = parser.parse_args()

    if args.u:
        print(args.u)
    elif args.s:
        search_term = " ".join(args.s)
        print(f"Searching for: {search_term}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()