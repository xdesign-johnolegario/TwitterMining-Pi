
import time
import urllib2

proxy_support = urllib2.ProxyHandler({'http':'mortmgs003.uk.hermes-europe.co.uk:port8080'})
opener = urllib2.build_opener(proxy_support)
def Main():
    while True:
        try:
            f = opener.open("https://www.myhermes.co.uk")
            f.read(1)
            print "Success"

            time.sleep(4)

        except Exception:
            print "Failed"
            time.sleep(4)

if __name__ == '__main__':
    Main()