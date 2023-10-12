# pywitness
this simple python tool allows to find web interfaces on a network.
this can be helpfull in e.g. pentesting engagement when we want to find any device or application with default credentials

the tool is using 'requests' to query each IP:PORT to see whether anything is sitting there. 
Then selenium is used to take screenshots. Selenium fires a browser in headless mode, goes to the IP:PORT that gave positive result and takes a screenshot.
The screenshots can then be manually checked to figure out any targets for further investigation.

currently Chrome is default browser that the tool uses.

!! chrome driver is required https://chromedriver.chromium.org/downloads !!

TODO:
- add support for firefox
- add support for edge 



$ python3 .\pywitness.py -h
usage: ProgramName [-h] [--pool POOL] [-p PORTS] -i IP [-t TIMEOUT] [-v] [-s] [-c CHROMEDRIVER]

What the program does

options:
  -h, --help            show this help message and exit
  --pool POOL           how big is the pool
  -p PORTS, --ports PORTS
                        comma separated list of ports
  -i IP, --ip IP        CIDR range of IP addresses
  -t TIMEOUT, --timeout TIMEOUT
                        how long should we wait for the server response ?
  -v, --verbose         more output to console
  -s, --screenshot      take screenshots of found urls with headless chrome and selenium framework
  -c CHROMEDRIVER, --chromedriver CHROMEDRIVER
                        path to chrome driver exe

example:
    python3 .\pywitness.py --ports="80,8080" --ip=192.168.0.0/29 --pool=10 --timeout=2 --verbose --screenshot --chromedriver=C:\\path_to\\chromedriver.exe