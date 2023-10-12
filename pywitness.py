import argparse
import ipaddress
import requests
import socket
import time
from multiprocessing import Pool
from requests.exceptions import ConnectTimeout
from itertools import product
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dataclasses import dataclass, field

''' given an IP range, check if there's a web interface siting on each IP, and if so make a screenshot
    The aim is to find web interfaces of IT assets
    The test goal is to find default credentials on said assets, this script might help finding places to dig deeper

    example:
        python3 .\interfacer.py --ports="80,8080" --ip=192.168.0.0/29 --pool=10 --timeout=2 --verbose --screenshot
'''

@dataclass
class Page:
    ip:str
    port:int
    url:str
    exists:bool
    name:str = field(default="")
    screenshot:str = field(default="")
    form:bool = field(default=False)
    html:str = field(default="")
    headers:str = field(default="")
    status_code:int = field(default=0)
    template:str = field(default="")

def main():
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help"
    )
    parser.add_argument("--pool", default=10, help="how big is the pool")
    parser.add_argument("-p", "--ports", default="80,443", help="comma separated list of ports")
    parser.add_argument("-i", "--ip", required=True, help="CIDR range of IP addresses")
    parser.add_argument("-t", "--timeout", default=10, help="how long should we wait for the server response ?")
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="more output to console")
    parser.add_argument("-s", "--screenshot", default=False, action="store_true", help="take screenshots of found urls with headless chrome and selenium framework")
    parser.add_argument("-c", "--chromedriver", default="", help="path to chrome driver exe")
    args = parser.parse_args()

    ips = [str(ip) for ip in ipaddress.IPv4Network(args.ip)]

    ports = args.ports.split(",")

    with Pool(processes=int(args.pool)) as pool:
        results = pool.starmap(_check, product(ips, ports, [int(args.timeout)], [args.verbose]))

    if args.screenshot:
        options = Options()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--headless')
        #driver = webdriver.Chrome(options=options)
        # https://chromedriver.chromium.org/downloads
        driver = webdriver.Chrome(args.chromedriver, options=options)
        driver.maximize_window()
        #driver = webdriver.Edge()

        if results:
            templates = list()
            for page in results:
                if page.exists:
                    # add log
                    _log(message=f"working on {page.url}")

                    # get screenshot with seleninum
                    driver.get(page.url)
                    ssPath = f"shots/{page.url.replace('/', '').replace(':', '_')}.png"
                    driver.save_screenshot(ssPath)
                    driver.quit()
                    _log(level="debug", message=f"screenshot saved at {ssPath}")

                    # has form?
                    page.form = True if "<form>" in page.html else False
                    _log(level="debug", message=f"has form? {page.form}")

                    # reverse ns lookup
                    page.name = socket.getnameinfo((page.ip, page.port), socket.NI_NUMERICSERV)
                    _log(level="debug", message=f"name resolution {page.ip}:{page.port} = {page.name}")

                    # get HTML template for report
                    page.template = _getTemplate(page)
                    templates.append(page.template)
                    _log(level="debug", message="got html template")

            # build report
            _log(message="done checking pages, building a report")
            _buildReport(templates)

def _log(message, level="info"):
    if message:
        color = "\033[0;32m"
        endc = "\033[0m"
        prefix = "II :: "
        if level == "error":
            color = "\033[0;31m"
            prefix = "EE :: "
        if level == "debug":
            color = "\033[1;33m"
            prefix = "DD :: "
        print(f"{color}{prefix}{message}{endc}")

def _check(ip, port, timeout, verbose):
    url = f"http://{ip}:{port}" # assuming http + port 443 works as https
    p = Page(ip=ip, port=int(port), url=url, exists=False)
    if verbose:
        _log(message=f"checking {url}", level="debug")
    try:
        response = requests.get(url=url, timeout=timeout, allow_redirects=True, verify=False)
        p.status_code = response.status_code
        if response.status_code != "404":
            _log(message=f"found {response.url}")
            p.exists = True
            p.html = response.text
            p.headers = response.headers
            return p
        else:
            if verbose:
                _log(message=f"status_code = 404 for {url}", level="debug")
                return p
    except ConnectTimeout:
        if verbose:
            _log(message=f"ConnectTimeout for {url}", level="debug")
        return p
    except Exception as e:
        _log(message=f"{e}", level="error")
        return p
        

def _getTemplate(page):
    template = f'''
        <section class="result">
            <div class="float thumbnail">
                <img src="../shots/{page.url.replace('/', '').replace(':', '_')}.png" />
            </div>
            <div class="float info form_{page.form}">
                <ul>
                    <li><bold>IP:</bold> {page.ip}</li>
                    <li><bold>Port:</bold> {page.port}</li>
                    <li><bold>URL:</bold> {page.url}</li>
                    <li><bold>Name:</bold> {page.name}</li>
                    <li><bold>Has FORM:</bold> {page.form}</li>
                </ul>
            </div>
        </section>
    '''
    return template

def _buildReport(templates):
    head = '''
        <html>
        <head>
            <title>pywitness report</title>
            <link rel="stylesheet" href="../templates/whole.css">
        </head>
        <body>
            <section id="top">
                <h1>PyWitness report</h1>
            </section>
            <section id="results">
    '''
    foot = '''
            </section>
        </body>
        </html>
    '''
    html = ""
    html += head
    for t in templates:
        if t:
            html += t
    
    html += foot
    reportPath = "reports/report_timestamp.html"
    
    with open(reportPath, "w") as f:
        f.write(html)

if __name__ == '__main__':
    main()