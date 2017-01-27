####################################################################
###########      Copyright (c) 2016 BigSQL           ###############
####################################################################

## Include libraries ###############################################
import os, sys, sqlite3, platform

## Set Global variables ############################################
rc = 0

def verify_metadata():
  try:
    c = cL.cursor()
    c.execute("SELECT count(*) FROM sqlite_master WHERE tbl_name = 'settings'")
    data = c.fetchone()
    kount = data[0]
    c.close()
  except sqlite3.Error as e:
    print("ERROR verify_metadata(): " + str(e.args[0]))
    sys.exit(1)
  if kount == 0:
    update_2_7_0()
  return


################ run_sql() #######################################
def run_sql(cmd):
  global rc 
  print ("")
  print (cmd)
  try:
    c = cL.cursor()
    c.execute(cmd)
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    print ("ERROR: " + str(e.args[0]))
    rc = 1


def update_2_7_0():
  print ("")
  print ("## Updating Metadata to 2.7 ####################")

  run_sql("DROP TABLE IF EXISTS settings")

  run_sql("CREATE TABLE settings ( \n" + \
          "  section            TEXT      NOT NULL, \n" + \
          "  s_key              TEXT      NOT NULL, \n" + \
          "  s_value            TEXT      NOT NULL, \n" + \
          "  PRIMARY KEY (section, s_key) \n" + \
          ")")

  ## default the new REPO variable to BITS environment variable
  ##  (if it is set)
  repo = os.getenv('BITS', 'http://s3.amazonaws.com/pgcentral')
  run_sql("INSERT INTO settings VALUES ('GLOBAL', 'REPO', '" + repo + "')")

  ## default the new PLATFORM variable based on OS 
  ##  (a Linux platform defaults to 'linux64' because platform specific 
  ##   linuxes, like el7-x64, are new as of hub v2.7.0)
  plat_sys = platform.system()
  pf = "linux64"
  if plat_sys == "Darwin":
    pf = "osx64"
  elif plat_sys == "Windows":
    pf = "win64"
  run_sql("INSERT INTO settings VALUES ('GLOBAL', 'PLATFORM', '" + pf + "')")

  return


def update_3_1_0():
  print ("")
  print ("## Updating Metadata to 3.1 ####################")
  run_sql("DROP TABLE IF EXISTS groups")
  run_sql("""CREATE TABLE groups (
               group_id           INTEGER PRIMARY KEY,
               group_name         TEXT    UNIQUE,
               group_desc         TEXT,
               group_type         TEXT,
               group_json         TEXT,
               parent_group_id    INTEGER)""")
  run_sql("INSERT INTO groups (group_name,parent_group_id) VALUES ('default',0)")

  run_sql("DROP TABLE IF EXISTS group_hosts")
  run_sql("""CREATE TABLE group_hosts (
             group_id         INTEGER NOT NULL,
             host_id          INTEGER NOT NULL,
             PRIMARY KEY (group_id, host_id))""")

  run_sql("ALTER TABLE hosts RENAME to hosts_old")

  run_sql("DROP TABLE IF EXISTS hosts")
  run_sql("""CREATE TABLE hosts (
               host_id            INTEGER PRIMARY KEY,
               host               TEXT NOT NULL,
               name               TEXT UNIQUE,
               ssh_user           TEXT,
               ssh_passwd         TEXT,
               ssh_key            TEXT,
               ssh_port           TEXT,
               pgc_home           TEXT NOT NULL,
               pg_user            TEXT,
               pg_passwd          TEXT,
               pg_port            TEXT,
               pg_database        TEXT,
               host_json          TEXT,
               platform           TEXT,
               interval           TEXT,
               last_update_utc    DATETIME,
               next_update_utc    DATETIME,
               unique_id          TEXT)""")

  run_sql("""INSERT INTO hosts (host,pgc_home,interval,last_update_utc,next_update_utc,unique_id)
             select host,"",interval,last_update_utc,next_update_utc,unique_id from hosts_old limit 1""")

  run_sql("DROP TABLE IF EXISTS hosts_old ")
  return


def mainline():
  ## need from_version & to_version
  if len(sys.argv) == 3:
    p_from_ver = sys.argv[1]
    p_to_ver = sys.argv[2]
  else:
    print ("ERROR: Invalid number of parameters, try: ")
    print ("         python update-hub.py from_version  to_version")
    sys.exit(1)

  print ("")
  print ("Running update-hub from v" + p_from_ver + " to v" + p_to_ver)

  if p_from_ver >= p_to_ver:
    print ("Nothing to do.")
    sys.exit(0)

  if (p_from_ver < "2.7.0") and (p_to_ver >= "2.7.0"):
    update_2_7_0()
  if (p_from_ver < "3.1.0") and (p_to_ver >= "3.1.0"):
    update_3_1_0()

  print (" ")
  print ("Goodbye.")
  sys.exit(rc)
  return


###################################################################
#  MAINLINE
###################################################################
PGC_HOME = os.getenv('PGC_HOME', '')
if PGC_HOME == '':
  print ("ERROR: Missing PGC_HOME envionment variable")
  sys.exit(1)

## gotta have a sqlite database to update
db_local = PGC_HOME + os.sep + "conf" + os.sep + "pgc_local.db"
cL = sqlite3.connect(db_local)

if __name__ == '__main__':
   mainline()
