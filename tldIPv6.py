import sys

import dns.exception
import dns.message
import dns.query
import dns.rdatatype
import dns.resolver

def get_root_server_ips():
    """get the root servers' IP addresses"""
    # look up the root servers
    root_ns_rr = dns.resolver.resolve('root-servers.net', dns.rdatatype.NS)
    root_server_names = set()
    for rr in root_ns_rr:
        if rr.rdtype == dns.rdatatype.NS:
            root_server_names.add(rr.target.to_text().lower())
    # get the IP addresses for each root server
    root_server_ips = set()
    for root_server_name in root_server_names:
        ipv4_rr = dns.resolver.resolve(root_server_name, dns.rdatatype.A)
        for rr in ipv4_rr:
            if rr.rdtype == dns.rdatatype.A:
                root_server_ips.add(rr.address)
        ipv6_rr = dns.resolver.resolve(root_server_name, dns.rdatatype.AAAA)
        for rr in ipv6_rr:
            if rr.rdtype == dns.rdatatype.AAAA:
                root_server_ips.add(rr.address.lower())
    # return our result
    return root_server_ips

def get_tlds(root_server_ips):
    """get a list of all TLD's from the root servers"""
    for target_ip in root_server_ips:
        try:
            root_xfr = dns.query.xfr(target_ip, '.')
            root_zones = set()
            for root_msg in root_xfr:
                for rrset in root_msg.answer:
                    if rrset.rdtype == dns.rdatatype.NS:
                        name = rrset.name.to_text().lower()
                        # filter out NS for the root zone itself
                        if name not in ('@', '.'):
                            root_zones.add(name)
            return root_zones
        except OSError as ex:
            print("%s; Unable to XFR from %s" % (ex, target_ip),
                  file=sys.stderr)
        except dns.exception.FormError as ex:
            print("%s; Unable to XFR from %s" % (ex, target_ip),
                  file=sys.stderr)
        except dns.xfr.TransferError:
            print("%s; Unable to XFR from %s" % (ex, target_ip),
                  file=sys.stderr)


def ipv6_ns_check(domain):
    """check if a domain has one or more IPv6 name servers"""
    # make sure we are looking up absolute names
    if not domain.endswith('.'):
        domain = domain + '.'
    # get our list of name servers for the domain
    try:
        ns_rr = dns.resolver.resolve(domain, dns.rdatatype.NS)
    except dns.exception.Timeout:
        return "lookup error: timeout"
    except dns.resolver.NoNameservers:
        return "lookup error: no working name servers"
    except dns.resolver.NoAnswer:
        return "lookup error: no answer"
    ns_names = set()
    for rr in ns_rr:
        if rr.rdtype == dns.rdatatype.NS:
            ns_names.add(rr.target.to_text().lower())
    # see if we can get an AAAA record for one of them
    for ns_name in ns_names:
        tries = 0
        while tries < 3:
            try:
                ipv6_rr = dns.resolver.resolve(ns_name, dns.rdatatype.AAAA)
                for rr in ipv6_rr:
                    if rr.rdtype == dns.rdatatype.AAAA:
                        return None
            except dns.resolver.NoAnswer:
                break
            except dns.resolver.NXDOMAIN:
                break
            except dns.exception.Timeout:
                tries += 1

        if tries == 3:
            return "all AAAA lookups timed out"

    # if not, we have no IPv6
    return "no IPv6 nameservers"

def main():
    root_server_ips = get_root_server_ips()
    tlds = get_tlds(root_server_ips)
    last_tld_len = 0
    for n, tld in enumerate(sorted(list(tlds))):
        progress = "[%4d/%4d %3d%%] " % (n+1, len(tlds), ((n+1)*100)/len(tlds))
        overwrite = "\r" + "".ljust(last_tld_len+len(progress)) + "\r"
        print(overwrite, end='', file=sys.stderr)
        print("%s%s" % (progress, tld), end='', flush=True, file=sys.stderr)
        err = ipv6_ns_check(tld)
        if err:
            print("%s\t%s" % (tld, err), flush=True)
        last_tld_len = len(tld)
    print(file=sys.stderr)

if __name__ == "__main__":
    main()
