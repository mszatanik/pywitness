import argparse
import ipaddress
import requests
from multiprocessing import Pool
from requests.exceptions import ConnectTimeout
from itertools import product
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


''' given an IP range, check if there's a web interface siting on each IP, and if so make a screenshot
    The aim is to find web interfaces of IT assets
    The test goal is to find default credentials on said assets, this script might help finding places to dig deeper

    example:
        python3 .\interfacer.py --ports="80,8080" --ip=192.168.0.0/29 --pool=10 --timeout=2 --verbose --screenshot
'''

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
    args = parser.parse_args()

    ips = [str(ip) for ip in ipaddress.IPv4Network(args.ip)]

    ports = args.ports.split(",")

    with Pool(processes=int(args.pool)) as pool:
        results = pool.starmap(_check, product(ips, ports, [int(args.timeout)], [args.verbose]))

    if args.screenshot:
        options = Options()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        #driver.maximize_window()
        #driver = webdriver.Edge()

        if results:
            for result in results:
                if result != None:
                    driver.get(result)
                    driver.save_screenshot(f"shots/{result.replace('/', '').replace(':', '_')}.png")
                    driver.quit()

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
    url = f"http://{ip}:{port}"
    if verbose:
        _log(message=f"checking {url}", level="debug")
    try:
        response = requests.get(url=url, timeout=timeout, allow_redirects=True)
        if response.status_code != "404":
            _log(message=f"found {response.url}")
            return response.url
        else:
            if verbose:
                _log(message=f"status_code = 404 for {url}", level="debug")
    except ConnectTimeout:
        if verbose:
            _log(message=f"ConnectTimeout for {url}", level="debug")
    except Exception as e:
        _log(message=f"{e}", level="error")
        

if __name__ == '__main__':
    main()