
import sys
import ssl
import socket
import time
import webbrowser
from bs4 import BeautifulSoup
from unidecode import unidecode
import datetime

cached_responses = {}


def help():
    print("Available commands are:\n\
            go2web -u <URL>         # make an HTTP request to URL and print the response\n\
            go2web -s <search-term> # search the term and print top 10 results\n\
            go2web -h               # show help\n\
            go2web -cache               # show current cached response\n")


def url_request(url, max_redirects=2, redirect_count=0):
    # Check if the URL starts with http:// or https:// and remove it
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]

    # Split the URL into the host and path
    host, path = url.split('/', 1) if '/' in url else (url, "")

    # Create a SSL context
    context = ssl.create_default_context()

    # check if the response is available in the cache
    if url in cached_responses:
        cached_response, cached_time = cached_responses[url]
        current_time = time.time()
        # check if the cached response is still valid
        if current_time - cached_time < 300:
            print("\n================== RETURNING CACHE RESPONSE ==================\n")
            print(cached_response)
            return

    # Create a socket connection and wrap it with SSL
    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as sslsock:
            # Send a GET request to the server
            request = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nAccept: text/html, application/json\r\n\r\n"
            sslsock.send(request.encode())

            # Receive the response from the server
            response = bytearray()
            for data in iter(lambda: sslsock.recv(4096), b""):
                response.extend(data)

            # Decode the response and extract the status code
            response_str = response.decode('utf-8')
            status_code = int(response_str.split()[1])

            # Check if the response is a redirection
            if status_code >= 300 and status_code < 400:
                if 'Location' in response_str and redirect_count < max_redirects:
                    new_url = response_str.split('Location: ')[1].split()[0]
                    print(f"Redirecting to {new_url}...")
                    webbrowser.open(new_url)
                    url_request(new_url, max_redirects, redirect_count + 1)
                    print(f"\nPress enter to exit.")

                else:
                    print(f"Too many redirects for {url}.")

            else:
                # Extract the HTML content from the response
                soup = BeautifulSoup(response.split(b'\r\n\r\n', 1)[1].decode('utf-8'), 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                text = unidecode(text)
                print(text)

                # store the response in the cache
                cached_responses[url] = (text, time.time())

def show_cache():
    if cached_responses:
        print("\nCurrent Cache:")
        for url, (response, timestamp) in cached_responses.items():
            print(f"URL: {url}")
            print(f"Cached Response: {response[:200]}...")  # print the first 200 characters of the cached response
            print(f"Timestamp: {datetime.datetime.fromtimestamp(timestamp)}\n")
    else:
        print("Cache is empty.")


def main():
    command = sys.argv

    if len(command) >= 3:
        if command[1] == "-u":
            url_request(command[2])
        elif command[1] == "-s":
            print("search")
        else:
            print("Invalid command")

    elif len(command) == 2 and command[1] == "-h":
        help()

    elif len(command) == 2 and command[1] == "-cache":
        show_cache()  # This will show the cache when the user enters `-cache` option

    else:
        while True:
            user_input = input("Enter a command (enter go2web -h to see all commands) or 'exit' to exit:\n> ")
            command = user_input.split()
            if len(command) == 0:
                continue
            elif command[0] == "go2web":
                if len(command) >= 3:
                    if command[1] == "-u":
                        url_request(command[2])
                    elif command[1] == "-s":
                        print("search")
                    else:
                        print("Invalid command")
                elif len(command) == 2 and command[1] == "-h":
                    help()
                elif len(command) == 2 and command[1] == "-cache":
                    show_cache()  # Show cache when `-cache` is used
                else:
                    print("Invalid command")
            elif command[0] == "exit":
                break
            else:
                print("Invalid command")


if __name__ == '__main__':
    main()
