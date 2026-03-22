import argparse
import socket
import ssl
import urllib.parse
from bs4 import BeautifulSoup


def make_request(host, path, scheme="http"):
    is_https = scheme == "https"
    port = 443 if is_https else 80

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)

    try:
        if is_https:
            context = ssl.create_default_context()
            s = context.wrap_socket(s, server_hostname=host)
        s.connect((host, port))
    except (socket.timeout, ConnectionRefusedError) as e:
        print(f"Error: Could not connect to {host} - {e}")
        return None, None

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
    scheme = url.split("//")[0].replace(":", "")
    domain = url.split("//")[1]
    parts = domain.split("/")
    host = parts[0]
    path = "/" + "/".join(parts[1:])
    return scheme, host, path


def decode_chunked(body):
    result = ""
    while body:
        if "\r\n" not in body:
            break
        size_str, body = body.split("\r\n", 1)
        size_str = size_str.strip()
        if not size_str:  # skip empty lines
            continue
        try:
            size = int(size_str, 16)
        except ValueError:
            break
        if size == 0:
            break
        result += body[:size]
        body = body[size + 2:]
    return result


def strip_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def build_search_url(search_term):
    query = "+".join(search_term)
    return "html.duckduckgo.com", f"/html/?q={query}"


def parse_search_results(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for result in soup.find_all("a", class_="result__a"):
        title = result.get_text()
        href = result.get("href", "")
        # extract the real URL from the uddg parameter
        parsed = urllib.parse.urlparse(href)
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get("uddg", ["No URL"])[0]
        results.append((title, url))

    return results[:10]


def main():
    parser = argparse.ArgumentParser(description="go2web - a simple HTTP client")
    parser.add_argument("-u", help="make an HTTP request to the specified URL and print the response", metavar="URL")
    parser.add_argument("-s", nargs="+", help="make an HTTP request to search the term using your favorite search engine and print top 10 results", metavar="term")
    args = parser.parse_args()

    if args.u:
        scheme, host, path = parse_url(args.u)
        headers, body = make_request(host, path, scheme)
        if headers is None:
            exit(1)
        if "transfer-encoding: chunked" in headers.lower():
            body = decode_chunked(body)
        print(strip_html(body))
    elif args.s:
        host, path = build_search_url(args.s)
        headers, body = make_request(host, path, "https")
        if "transfer-encoding: chunked" in headers.lower():
            body = decode_chunked(body)
        results = parse_search_results(body)
        for i, (title, url) in enumerate(results, 1):
            print(f"{i}. {title}")
            print(f"   {url}")
            print()
    else:
        parser.print_help()




if __name__ == "__main__":
    main()