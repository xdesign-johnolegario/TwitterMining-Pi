
import urllib2, tarfile, os, sys

PGC_VER=os.getenv("PGC_VER", "3.1.0")
PGC_REPO=os.getenv("PGC_REPO", "http://s3.amazonaws.com/pgcentral")


###################################
# MAINLINE
###################################

IS_64BITS = sys.maxsize > 2**32
if not IS_64BITS:
  print("This is a 32bit machine and BigSQL packages are 64bit.\n"
        "Cannot install")
  sys.exit(1)

pgc_file="bigsql-pgc-" + PGC_VER + ".tar.bz2"
f = PGC_REPO + "/" + pgc_file

if not os.path.exists(pgc_file):
  print("\nDownloading BigSQL PGC " + PGC_VER + " ...")
  try:
    fu = urllib2.urlopen(f)
    local_file = open(pgc_file, "wb")
    local_file.write(fu.read())
    local_file.close()
  except (urllib2.URLError, urllib2.HTTPError) as e:
    print("ERROR: Unable to download " + f + "\n" + str(e))
    sys.exit(1)

print("\nUnpacking ...")
try:
  tar = tarfile.open(pgc_file)
  tar.extractall(path=".")
  print("\nCleaning up")
  tar.close()
  os.remove(pgc_file)
except Exception as e:
  print("ERROR: Unable to unpack \n" + str(e))
  sys.exit(1)

print("\nSetting REPO to " + PGC_REPO)
pgc_cmd = "bigsql" + os.sep + "pgc"
os.system(pgc_cmd + " set GLOBAL REPO " + PGC_REPO)

print("\nUpdating Metadata")
os.system(pgc_cmd + " update --silent")

print("\nBigSQL PGC installed.  Try '" + pgc_cmd + " help' to get started.\n")

sys.exit(0)

