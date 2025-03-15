import ast
import json
import sys
import ssl
import socket
import time
import webbrowser
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
    # Check if the URL starts with http:// or https:// and remove it
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]

    # Split the URL into the host and path
    host, path = url.split('/', 1) if '/' in url else (url, "")

    context = ssl.create_default_context()

    # Check if the response is available in the cache
    if url in cached_responses:
        cached_response, cached_time = cached_responses[url]
        current_time = time.time()
        # Check if the cached response is still valid
        if current_time - cached_time < 300:
            print("\n================== RETURNING CACHE RESPONSE ==================\n")
            print(cached_response)
            return

    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as sslsock:
            request = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nAccept: text/html, application/json\r\n\r\n"
            sslsock.send(request.encode())

            response = bytearray()
            for data in iter(lambda: sslsock.recv(4096), b""):
                response.extend(data)
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
                # Check if the response contains JSON
                if 'application/json' in response_str:
                    try:
                        json_data = json.loads(response_str.split('\r\n\r\n', 1)[1])  # Extract JSON part
                        print(json.dumps(json_data, indent=2))  # Pretty print the JSON
                    except json.JSONDecodeError:
                        print("Failed to decode JSON.")
                else:
                    # If the response is not JSON, print HTML content
                    print("Response is not JSON. Raw HTML content:")
                    soup = BeautifulSoup(response.split(b'\r\n\r\n', 1)[1].decode('utf-8'), 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    text = unidecode(text)
                    print(text)

                cached_responses[url] = (response_str, time.time())


def clear_cache():
    global cached_responses
    cached_responses = {}
    print("Cache has been cleared.")


def show_cache():
    if cached_responses:
        print("\nCurrent Cache:")
        for url, (response, timestamp) in cached_responses.items():
            print(f"URL: {url}")
            print(f"Cached Response: {response[:200]}...")  # print the first 200 characters of the cached response
            print(f"Timestamp: {datetime.datetime.fromtimestamp(timestamp)}\n")
    else:
        print("Cache is empty.")


def search(query):

    host = "www.googleapis.com"
    context = ssl.create_default_context()

    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as sslsock:
            # Compose the HTTP GET request to search for the query on Google Custom Search API
            request = f"GET https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query} HTTP/1.0\r\nHost:{host}\r\nAccept: text/html, application/json\r\n\r\n"
            sslsock.send(request.encode())

            resp_str = ''
            for data in iter(lambda: sslsock.recv(4096), b""):
                resp_str += data.decode('utf-8')

            json_start = resp_str.find("{")
            json_end = resp_str.rfind("}") + 1
            json_str = resp_str[json_start:json_end]

            response = ast.literal_eval(json_str)

            print(f"Top {RESULTS_NR} search results for '{query}':\n")

            for i in range(1, RESULTS_NR + 1):
                item = response["items"][i - 1]
                title = item.get("title", "No title available")
                link = item.get("link", "No link available")
                print(f"{i}. {title}")
                print(f"Link: {link}\n")

            global link_list
            link_list = [item["link"] for item in response["items"]]

            # Call the access_link function to allow the user to open a link
            access_link()


def access_link():
    for i in range(RESULTS_NR + 1):
        print(f"Enter a number between 1 and {RESULTS_NR} to open a link, or 'exit' to exit.\n")
        user_input = input()
        if user_input == 'exit':
            break
        try:
            link_index = int(user_input) - 1
            if 0 <= link_index < RESULTS_NR:
                url_request(link_list[link_index])
            else:
                print(f"Invalid input. Please enter a number between 1 and {RESULTS_NR} or 'exit'.")
        except:
            print(f"Invalid input. Please enter a number between 1 and {RESULTS_NR} or 'exit'.")


def main():
    command = sys.argv

    # Command-line mode
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

    # Interactive mode
    else:
        while True:
            user_input = input("Enter a command (enter go2web -h to see all commands) or 'exit' to exit:\n> ")
            command = user_input.split()

            if len(command) == 0:
                continue

            if command[0] == "exit":
                break

            if command[0] != "go2web":
                print("Invalid command. Use 'go2web' followed by an option.")
                continue

            if len(command) == 1:
                print("Missing option. Use 'go2web -h' to see available commands.")
                continue

            # Process commands
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