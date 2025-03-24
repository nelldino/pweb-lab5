import json
import sys
import ssl
import socket
import time
from bs4 import BeautifulSoup
from unidecode import unidecode
import datetime

cached_responses = {}
GOOGLE_API_KEY = "AIzaSyCgdShmwIXVVDUzR1zc_UXhxFwrdUTQ5Qc"
GOOGLE_CX = "c6319817e2afd4b56"
RESULTS_NR = 10


def help():
    print("Available commands are:\n\
            go2web -u <URL>         # make an HTTP request to URL and print the response\n\
            go2web -s <search-term> # search the term and print top 10 results\n\
            go2web -h               # show help\n\
            go2web -cache           # show current cached response\n\
            go2web -c               # clear the cache\n")


def url_request(url, max_redirects=2, redirect_count=0):
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]

    if '/' in url:
        host, path = url.split('/', 1)
        path = '/' + path
    else:
        host = url
        path = '/'

    if url in cached_responses:
        cached_response, cached_time = cached_responses[url]
        if time.time() - cached_time < 300:
            print("\n================== RETURNING CACHE RESPONSE ==================\n")
            print(cached_response)
            return

    # Initially connect via HTTP (port 80)
    port = 80
    context = None

    try:
        with socket.create_connection((host, port)) as sock:
            request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\nAccept: text/html, application/json\r\n\r\n"
            sock.send(request.encode())

            response = bytearray()
            for data in iter(lambda: sock.recv(4096), b""):
                response.extend(data)

        response_str = response.decode('utf-8', errors='ignore')
        status_code = int(response_str.split()[1])

        if 300 <= status_code < 400:
            if 'Location: ' in response_str and redirect_count < max_redirects:
                new_url = response_str.split('Location: ')[1].split()[0].strip()

                if new_url.startswith("https://"):
                    print(f"Redirecting to secure HTTPS: {new_url}...")
                    return url_request(new_url, max_redirects, redirect_count + 1)
                else:
                    print(f"Redirecting to: {new_url}...")
                    return url_request(new_url, max_redirects, redirect_count + 1)

        # Check if the response is JSON
        if 'application/json' in response_str:
            try:
                json_data = json.loads(response_str.split('\r\n\r\n', 1)[1])
                formatted_json = json.dumps(json_data, indent=2)
                print("\n================== JSON RESPONSE ==================\n")
                print(formatted_json)
                cached_responses[url] = (formatted_json, time.time())
            except json.JSONDecodeError:
                print("Failed to decode JSON response.")

        else:  # If not JSON, handle as HTML
            soup = BeautifulSoup(response.split(b'\r\n\r\n', 1)[1].decode('utf-8'), 'html.parser')
            text = unidecode(soup.get_text(separator='\n', strip=True))
            print("\n================== HTML RESPONSE ==================\n")
            print(text)
            cached_responses[url] = (text, time.time())

    except Exception as e:
        print(f"An error occurred: {e}")
def clear_cache():
    global cached_responses
    cached_responses = {}
    print("Cache has been cleared.")

def show_cache():
    if cached_responses:
        print("\nCurrent Cache:")
        for url, (response, timestamp) in cached_responses.items():
            print(f"URL: {url}")
            print(f"Cached Response: {response[:200]}...")
            print(f"Timestamp: {datetime.datetime.fromtimestamp(timestamp)}\n")
    else:
        print("Cache is empty.")

def search(query):
    host = "www.googleapis.com"
    context = ssl.create_default_context()

    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as sslsock:
            request = f"GET /customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query} HTTP/1.0\r\nHost:{host}\r\nAccept: application/json\r\n\r\n"
            sslsock.send(request.encode())

            resp_str = ''
            for data in iter(lambda: sslsock.recv(4096), b""):
                resp_str += data.decode('utf-8')

            try:
                json_data = json.loads(resp_str.split('\r\n\r\n', 1)[1])
            except json.JSONDecodeError:
                print("Error decoding JSON response from API.")
                return

            if "items" not in json_data:
                print("No search results found.")
                return

            print(f"Top {RESULTS_NR} search results for '{query}':\n")

            global link_list
            link_list = []
            for i, item in enumerate(json_data["items"][:RESULTS_NR], 1):
                title = item.get("title", "No title available")
                link = item.get("link", "No link available")
                print(f"{i}. {title}\n   Link: {link}\n")
                link_list.append(link)
            # Call the access_link function to allow the user to open a lin
            access_link()


def access_link():
    while True:
        user_input = input(f"Enter a number between 1 and {RESULTS_NR} to open a link, or 'exit' to exit: ")
        if user_input.lower() == 'exit':
            break
        try:
            link_index = int(user_input) - 1
            if 0 <= link_index < len(link_list):
                url_request(link_list[link_index])
            else:
                print(f"Invalid input. Please enter a number between 1 and {RESULTS_NR} or 'exit'.")
        except ValueError:
            print(f"Invalid input. Please enter a number between 1 and {RESULTS_NR} or 'exit'.")


def main():
    command = sys.argv

    if len(command) > 1:
        if command[1] == "-h":
            help()
        elif command[1] == "-cache":
            show_cache()
        elif command[1] == "-c":
            clear_cache()
        elif command[1] == "-u" and len(command) > 2:
            url_request(command[2])
        elif command[1] == "-s" and len(command) > 2:
            search('+'.join(command[2:]))
        else:
            print("Invalid command")
            help()

    else:
        while True:
            user_input = input("Enter a command (or 'exit' to quit):\n> ")
            if user_input.lower() == "exit":
                break
            command = user_input.split()

            if len(command) < 2:
                print("Missing option. Use 'go2web -h' to see available commands.")
                continue

            if command[0] != "go2web":
                print("Invalid command. Use 'go2web' followed by an option.")
                continue

            if command[1] == "-h":
                help()
            elif command[1] == "-cache":
                show_cache()
            elif command[1] == "-c":
                clear_cache()
            elif command[1] == "-u" and len(command) > 2:
                url_request(command[2])
            elif command[1] == "-s" and len(command) > 2:
                search('+'.join(command[2:]))
            else:
                print("Invalid command")


if __name__ == '__main__':
    main()