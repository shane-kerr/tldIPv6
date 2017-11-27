# tldIPv6
Scan the DNS top-level domains and see which support IPv6.

In order for an IPv6-only resolver to work, the authority servers that
it queries must also support IPv6. Since DNS is hierarchical, all of
the zones above a given domain must also support IPv6. The root DNS
servers have had IPv6 support for many years now, but there are still
some TLD domains which do not have any IPv6 servers. This program
finds them.

## Installation

Most importantly you need a Unix machine with working IPv6.

You also need Python 3 and dnspython. You can install dnspython via:

```
$ pip install -r requirements.txt
```

If you do not want to install dnspython system-wide you can also do it
only for your current user:

```
$ pip install --user -r requirements.txt
```

You can also use a virtual environment (my preferred method):

```
$ python3 -m venv venv
$ . venv/bin/activate
(venv) $ pip install -r requirements.txt
```

## Running

It takes quite a while to run, since every lookup is done
sequentially. The program outputs progress to the console via
`stderr`, so you can know that it is not just stuck.

Typical execution looks like this:

```
$ python3 tldIPv6.py > results-2017-11-27
No answer or RRset not for qname; Unable to XFR from 2001:500:2d::d
No answer or RRset not for qname; Unable to XFR from 198.41.0.4
No answer or RRset not for qname; Unable to XFR from 199.7.83.42
No answer or RRset not for qname; Unable to XFR from 198.97.190.53
[  48/1541   3%] alsace
```

As you see here, there are a few errors as it tries to AXFR the root
zone from a root server or two that does not support AXFR, but
eventually it will work.

You will get a result file that looks something like this:

```
ai  no IPv6 nameservers
bb  no IPv6 nameservers
bf  no IPv6 nameservers
bh  no IPv6 nameservers
ck  no IPv6 nameservers
dj  no IPv6 nameservers
fk  no IPv6 nameservers
 .
 .
 .
```

## How It Works

The program downloads the current root zone via an AXFR from one of
the root servers that allows zone transfers. It does not keep a list
of which servers support this, but just tries each root server IP
address until the transfer works. The order attempted is whatever the
local resolver returns for the NS for root.

Next it goes through each TLD and does an NS lookup to get the
authoritative list of name servers. It then tries each name server
returned until it finds one with an AAAA record. If none of the name
servers for a TLD have an AAAA record, then it is reported as not
supporting IPv6.
