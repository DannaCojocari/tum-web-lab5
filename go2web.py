import argparse
import socket
from bs4 import BeautifulSoup


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


def decode_chunked(body):
    result = ""
    while body:
        # find the chunk size
        size_str, body = body.split("\r\n", 1)
        size = int(size_str.strip(), 16)
        if size == 0:
            break
        result += body[:size]
        body = body[size + 2:]  # skip the \r\n after chunk
    return result


def strip_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def main():
    parser = argparse.ArgumentParser(description="go2web - a simple HTTP client")
    parser.add_argument("-u", help="make an HTTP request to the specified URL and print the response", metavar="URL")
    parser.add_argument("-s", nargs="+", help="make an HTTP request to search the term using your favorite search engine and print top 10 results", metavar="term")
    args = parser.parse_args()

    if args.u:
        host, path = parse_url(args.u)
        headers, body = make_request(host, path)
        if "Transfer-Encoding: chunked" in headers:
            body = decode_chunked(body)
        print(strip_html(body))
    elif args.s:
        search_term = " ".join(args.s)
        print(f"Searching for: {search_term}")
    else:
        parser.print_help()




if __name__ == "__main__":
    main()