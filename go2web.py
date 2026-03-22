import argparse
import socket


def make_request(host, path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, 80))

    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    s.sendall(request.encode())

    response = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk

    s.close()
    response = response.decode("utf-8", errors="replace")

    headers, body = response.split("\r\n\r\n", 1)
    return headers, body


def parse_url(url):
    domain = url.split("//")[1]
    parts = domain.split("/")
    host = parts[0]
    path = "/" + "/".join(parts[1:])
    return host, path


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