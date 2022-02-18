#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# main.py

import json
from io import BytesIO
from sys import exit

import certifi
import pycurl

from stdlib import LocalParser, Logger, getindex, init_killer, levels

log = Logger()


proxy_judges = {
    "https": "https://httpbin.org/get",
    "http": "http://httpbin.org/get",
    "php_http": "http://mojeip.net.pl/asdfa/azenv.php"
}


def send_request(url, proxy=False, proxy_type=False):
    global timeout, req_verbose
    session = pycurl.Curl()
    response_body = BytesIO()

    session.setopt(pycurl.URL, url)
    session.setopt(pycurl.WRITEDATA, response_body)
    session.setopt(pycurl.TIMEOUT, timeout)
    session.setopt(
        pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:8.0) Gecko/20100101 Firefox/8.0")

    if proxy:
        session.setopt(pycurl.PROXY, proxy)
    if proxy_type:  # This is not needed but there's no problem to add it
        session.setopt(pycurl.PROXYTYPE, proxy_type)

    # Linux
    # session.setopt(
    #     pycurl.CAINFO, "/etc/ca-certificates/extracted/ca-bundle.trust.crt")
    session.setopt(pycurl.CAINFO, certifi.where())

    if req_verbose:
        session.setopt(pycurl.VERBOSE, 1)  # For developping
    session.setopt(pycurl.SSL_VERIFYPEER, 1)
    session.setopt(pycurl.SSL_VERIFYHOST, 2)

    try:
        session.perform()
    except pycurl.error as err:
        if err.args[0] == pycurl.TIMEOUT:
            return False

    if session.getinfo(pycurl.HTTP_CODE) != 200:
        return False
    req_timeout = round(session.getinfo(pycurl.CONNECT_TIME) * 1000)
    response = response_body.getvalue().decode("ascii")

    session.close()
    # log.info("%s" % ({"timeout": timeout, "response": response}))  # For developping
    return {"timeout": req_timeout, "response": response}


def get_ip(proxy=False):
    request_arg = ["http://api.ipify.org/"]
    if proxy:
        request_arg += [proxy]

    response = send_request(*request_arg)
    if not response:
        return False

    return response["response"]


def check_anonymity(response):
    global self_ip
    if self_ip in response:
        return "Transparent"

    privacy_headers = [
        "VIA",
        "X-FORWARDED-FOR",
        "X-FORWARDED",
        "FORWARDED-FOR",
        "FORWARDED-FOR-IP",
        "FORWARDED",
        "CLIENT-IP",
        "PROXY-CONNECTION"
    ]

    if any([header in response for header in privacy_headers]):
        return "Anonymous"

    return "Elite"


def get_country(ip):
    res = send_request("https://ip2c.org/" + ip)

    if res and res["response"][0] == "1":
        res = res["response"].split(";")
        return [res[3], res[1]]

    return ["-", "-"]


def write_good_proxy(infos):
    global good_proxies_output, generate_proxychains

    with open(good_proxies_output, "a") as output:
        json.dump(infos, output, indent=4)

    if generate_proxychains:
        with open("proxychains.conf", "a") as output:
            output.write("%s %s %s\n" %
                         (infos["protocol"], *infos["proxy"].split(":")))


def get_proxies(proxies_type):
    url = "https://spys.me/" + proxies_type + ".txt"

    req = send_request(url)
    if not req:
        return False

    import re
    proxies = []

    for c in req["response"].split("\n"):
        m = re.match(r"[\d\.:]+", c)
        if not m:
            continue
        proxies += [m.group()]

    return proxies


def check(proxies):
    global force_ssl_support, protocols, proxy_judges

    if force_ssl_support:
        local_proxy_judges = [proxy_judges["https"]]
    else:
        local_proxy_judges = list(proxy_judges.values())

    for proxy in proxies:
        log.info("Trying %s ..." % proxy)
        out_proxy_judges = False

        for proxy_judge in local_proxy_judges:
            for protocol in protocols:
                log.debug("Trying %s on %s website with %s protocol!" %
                          (proxy, proxy_judge, protocol))
                proxy_url = protocol + "://" + proxy

                req = send_request(proxy_judge, proxy_url)
                if not req:
                    index = getindex(tuple(proxy_judges.items()), proxy_judge)
                    if index == 1:
                        log.critical("Cannot get %s index!?!" % proxy_judge)
                        exit(1)

                    continue

                timeout = req["timeout"]
                ip_addr = get_ip(proxy_url)
                if not ip_addr:
                    # log.error("Failed to get the IP address of this proxy!")
                    ip_addr = proxy.split(":")[0]

                country = get_country(ip_addr)

                anon_r = send_request(proxy_judges["php_http"], proxy_url)
                if not anon_r:
                    # log.error("Failed to check the proxy anonymity!")
                    anon_r = {"response": ""}
                anonymity = check_anonymity(anon_r["response"])

                log.success("Proxy %s is working on %s site with %s protocol!" % (
                    proxy, proxy_judge, protocol))
                infos = {"proxy": proxy, "ip_addr": ip_addr, "protocol": protocol, "website_judge": proxy_judge, "timeout": timeout,
                         "country": country, "anonymity": anonymity}

                # log.debug("%s" % infos)  # For developping
                write_good_proxy(infos)

                out_proxy_judges = True
                break

            if out_proxy_judges:
                break


def main():
    parser = LocalParser(
        description="Proxies checker in Python.", add_help=False)
    parser._positionals.title = "Positional arguments"
    parser._optionals.title = "Optional arguments"
    parser.add_argument("-h", "--help", action="help",
                        help="Show this help message.")
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s 0.7", help="Show script version.")
    parser.add_argument("-p", "--proxies", dest="proxies",
                        help="Set proxies to check, separated by comma ','.")
    parser.add_argument("-f", "--proxies-file", dest="proxies_file",
                        help="Set proxies file to check.")
    parser.add_argument("-P", "--protocols", dest="protocols", default="http,https,socks4,socks5",
                        help="Set proxies protocols to check, separated by comma ',' (default: socks5,socks4,https,http (from the suggested to the ignored))")
    parser.add_argument("-o", "--good-output", dest="good_proxies_output", default="good_proxies.json",
                        help="Set output file name of good proxies (default: good_proxies.txt).")
    parser.add_argument("-F", "--force-ssl", dest="force_ssl_support", action="store_true",
                        help="Add ssl (https) supporting as condition to accept any proxy.")
    parser.add_argument("-g", "--generate-proxychains", dest="generate_proxychains", action="store_true",
                        help="Generate proxychains file with the working proxies to use it with 'https://github.com/haad/proxychains/' program.")
    parser.add_argument("-Gs", "--get-socks-proxies", dest="get_socks_proxies", action="store_true",
                        help="Get socks proxies from 'https://spys.me/socks.txt'.")
    parser.add_argument("-Gh", "--get-http-proxies", dest="get_http_proxies", action="store_true",
                        help="Get http proxies from 'https://spys.me/http.txt'.")
    parser.add_argument("-t", "--timeout", dest="timeout", type=int, default=5,
                        help="Set request timeout (default: 5)")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                        help="Increase logging level.")
    parser.add_argument("-V", "--verbose", dest="req_verbose", action="store_true",
                        help="Print all requests logs with curl (not suggested, only use it if you need to know what happen).")

    args = parser.parse_args()

    global force_ssl_support, protocols, timeout, good_proxies_output, self_ip, generate_proxychains, req_verbose

    force_ssl_support = args.force_ssl_support
    protocols = [c for c in args.protocols.split(",") if c != ""]
    timeout = args.timeout
    good_proxies_output = args.good_proxies_output
    generate_proxychains = args.generate_proxychains
    req_verbose = args.req_verbose

    open(good_proxies_output, "w").close()
    if generate_proxychains:
        with open("proxychains.conf", "w") as output:
            output.write(
                "dynamic_chain\nproxy_dns\nremote_dns_subnet 224\ntcp_read_time_out 15000\ntcp_connect_time_out 8000\nlocalnet 127.0.0.0/255.0.0.0\n[ProxyList]\n")

    self_ip = get_ip()
    if not self_ip:
        log.critical("Check your internet connection!")

    log.info("Your IP address is: %s" % self_ip)

    if args.debug:
        log.setlevel(levels.DEBUG)

    if args.proxies:
        proxies = [c for c in args.proxies.split(",") if c != ""]
        check(proxies)

    if args.proxies_file:
        with open(args.proxies_file, "r") as proxies_file:
            proxies = [c
                       for c in proxies_file.read().split("\n") if c != ""]
        check(proxies)

    if args.get_socks_proxies:
        proxies = get_proxies("socks")
        if not proxies:
            log.error("Cannot get socks proxies, check your internet connection!")
            exit(1)
        check(proxies)

    elif args.get_http_proxies:
        proxies = get_proxies("proxy")
        if not proxies:
            log.error("Cannot get http proxies, check your internet connection!")
            exit(1)
        check(proxies)

    if not (args.proxies or args.proxies_file or args.get_socks_proxies or args.get_http_proxies):
        log.critical(
            "You should pass one of this arguments, -p, -f, -Gs or -Gh!")
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    init_killer()
    main()
