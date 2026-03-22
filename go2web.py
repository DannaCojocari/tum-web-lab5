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
        s.connect((host, port))
        if is_https:
            context = ssl.create_default_context()
            s = context.wrap_socket(s, server_hostname=host)
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        print(f"Error: Could not connect to {host} - {e}")
        return None, None

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: Mozilla/5.0 (compatible; go2web/1.0)\r\n"
        f"Connection: close\r\n\r\n"
    )
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
    if "://" not in url:
        url = "http://" + url
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


def get_status_code(headers):
    first_line = headers.split("\r\n")[0]
    status_code = int(first_line.split(" ")[1])
    return status_code


def get_location(headers):
    for line in headers.split("\r\n"):
        if line.lower().startswith("location:"):
            return line.split(": ", 1)[1].strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="go2web - a simple HTTP client")
    parser.add_argument("-u", help="make an HTTP request to the specified URL and print the response", metavar="URL")
    parser.add_argument("-s", nargs="+", help="make an HTTP request to search the term using your favorite search engine and print top 10 results", metavar="term")
    args = parser.parse_args()

    if args.u:
        scheme, host, path = parse_url(args.u)

        max_redirects = 5  # avoid infinite loops
        for _ in range(max_redirects):
            headers, body = make_request(host, path, scheme)
            if headers is None:
                exit(1)

            status = get_status_code(headers)

            if status in (301, 302):
                location = get_location(headers)
                if location is None:
                    print("Redirect with no Location header")
                    exit(1)
                print(f"Redirecting to: {location}")
                scheme, host, path = parse_url(location)
            else:
                break

        if "transfer-encoding: chunked" in headers.lower():
            body = decode_chunked(body)
        print(strip_html(body))
    elif args.s:
        host, path = build_search_url(args.s)
        headers, body = make_request(host, path, "https")
        if headers is None:
            exit(1)
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