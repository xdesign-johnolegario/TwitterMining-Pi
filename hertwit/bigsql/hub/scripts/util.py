
##################################################################
###########      Copyright (c) 2016 BigSQL           ###############
####################################################################

PGC_VERSION = "3.1.0"

## Include libraries ###############################################
import os, sys, socket, commands, platform, sqlite3, getpass
import fileinput, shlex, signal, commands, urllib2, hashlib
import json, uuid, logging, tempfile
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime, timedelta
import shutil
import filecmp
from distutils.dir_util import copy_tree
import traceback, api

scripts_lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if scripts_lib_path not in sys.path:
  sys.path.append(scripts_lib_path)

from crontab import CronTab
import semver

my_logger = logging.getLogger('pgcli_logger')
PGC_HOME=os.getenv('PGC_HOME')
pid_file = os.path.join(os.getenv('PGC_HOME'), 'conf', 'pgc.pid')


## is this component PostgreSQL ##################################
def is_postgres(p_comp):
  if (p_comp > 'pg90') and (p_comp < 'pg99'):
    return True
  return False


## anonymous data from the INFO command
def get_anonymous_info():
    jsonInfo = api.info(True, "", "", False)
    platform = jsonInfo['platform']
    os = jsonInfo['os']
    mem = str(jsonInfo['mem'])
    cores = str(jsonInfo['cores'])
    cpu = jsonInfo['cpu']
    anon = "(" + platform + "; " + os + "; " + mem + "; " + \
              cores + "; " + cpu + ")"
    return(anon)


## abruptly terminate whilst display abit of a message
def exit_message(p_msg, p_rc):
  msg = p_msg
  if p_rc >= 1:
    msg = "ERROR: " + msg
  print(msg)
  sys.exit(p_rc)


def verify(p_json):
  try:
    c = cL.cursor()
    sql = "SELECT component, version, platform, release_date " + \
          " FROM versions WHERE is_current = 1 " + \
          "ORDER BY 4 DESC, 1"
    c.execute(sql)
    data = c.fetchall()
    for row in data:
      comp_ver = str(row[0]) + "-" + str(row[1])
      plat = str(row[2])
      if plat == "":
        verify_comp(comp_ver)
      else:
        if "win" in plat:
          verify_comp(comp_ver + "-win64")
        if "osx" in plat:
          verify_comp(comp_ver + "-osx64")
        if "linux" in plat:
          verify_comp(comp_ver + "-linux64")
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"verify()")

  return


def verify_comp(p_comp_ver_plat):
  base = get_value("GLOBAL", "REPO") + "/" + p_comp_ver_plat
  url_file = base + ".tar.bz2"
  rc1 = http_is_file(url_file)

  url_checksum = url_file + ".sha512"
  rc2 = http_is_file(url_checksum)

  if rc1 == 0 and rc2 == 0:
    print ("GOOD: " + base)
    return 0

  print ("BAD:  " + base)
  return 1


def get_relnotes(p_comp, p_ver=""):
  comp_name = p_comp
  parent_comp = get_parent_component(comp_name,0)
  if parent_comp!="":
      comp_name=p_comp.replace("-" + parent_comp,"")

  file = "relnotes-" + comp_name + ".txt"
  ver = ""
  if is_postgres(comp_name):
    if p_ver == "":
      if p_comp == "pg10":
        ver = "10.0"
      elif p_comp == "pg96":
        ver = "9.6.0"
      elif p_comp == "pg95":
        ver = "9.5.0"
      elif p_comp == "pg94":
        ver = "9.4.0"
      elif p_comp == "pg93":
        ver = "9.3.0"
      elif p_comp == "pg92":
        ver = "9.2.0"
    else:
      ## remove the "-n" suffix
      ver = p_ver[:-2]
    file = "relnotes-" + comp_name + "-" + ver + ".txt"
  repo = get_value("GLOBAL", "REPO")
  repo_file = repo + "/" + file
  out_dir = PGC_HOME + os.sep + "conf" + os.sep + "cache"

  if http_is_file(repo_file) == 1:
    return("not available")

  if http_get_file(False, file, repo, out_dir, False, ""):
    out_file = out_dir + os.sep + file
    rel_notes_text = read_file_string(out_file)
    final_txt = unicode(str(rel_notes_text),sys.getdefaultencoding(),errors='ignore').strip()
    return final_txt

  return ""


def install_pg_autostart(p_json, p_comp_list):
  rc = 0
  this_os = get_os()

  comp = ""
  if len(p_comp_list) == 1:
    comp = p_comp_list[0]
    if is_postgres(comp):
      print("ERROR: component must be postgres")
      return 1
  else:
    print("ERROR: only one postgres component allowed at a time")
    return 1

  ## Figure out the PACKAGE name ##############################
  version = ""
  try:
    c = cL.cursor()
    sql = "SELECT version FROM packages WHERE component = ? AND os = ?"
    c.execute(sql, [comp, this_os])
    data = c.fetchone()
    if data is None:
      pass
    else:
      version = data[0]
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"install_pg_autostart()")

  if version == "":
    print("ERROR: Package not available for '" + comp + "' on '" + this_os + "'")
    return 1

  pkg_nm = "postgresql-" + version + "-" + this_os + "-x64-bigsql.rpm"

  ## Download the PACKAGE #####################################
  repo = get_value('GLOBAL', 'REPO')
  out_dir = "conf" + os.sep + "cache"
  repo_pkg = repo + "/" + pkg_nm
  print("Downloading " + repo_pkg)
  if not http_get_file(p_json, pkg_nm, repo, out_dir, False, ""):
    print("ERROR: Cannot download " + repo_pkg)
    return 1

  ## Run the right YUM or APT-GET command to install the PACKAGE
  cmd = "sudo yum localinstall " + out_dir + os.sep + pkg_nm
  print("")
  print("Running cmd = '" + cmd + "'")
  rc = os.system(cmd)
  if rc != 0:
    print(pkg_nm + " not installed")
    return 1

  return 0


def update_installed_date(p_app):
  try:
    c = cL.cursor()
    install_date=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sql = "UPDATE components SET install_dt = ? WHERE component = ?"
    c.execute(sql, [install_date, p_app])
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"update_installed_date()")

  return


def update_hosts(p_host, p_interval, p_unique_id, updated=False):

    last_update_utc = datetime.utcnow()

    current_time = last_update_utc

    cmd = os.path.abspath(PGC_HOME) + os.sep + "pgc update"

    if p_unique_id:
        unique_id = p_unique_id
    else:
        unique_id = str(uuid.uuid4())

    if updated:
        exec_sql("UPDATE hosts " + \
                 "   SET last_update_utc = '" + last_update_utc.strftime("%Y-%m-%d %H:%M:%S") + "', " + \
                 "       unique_id = '" + str(unique_id) + "' " + \
                 " WHERE host = '" + str(p_host) + "'")
    host_settings = read_hosts(p_host)
    if host_settings[1]:
        last_update_utc = datetime.strptime(host_settings[1], "%Y-%m-%d %H:%M:%S")

    if p_interval == "Daily":
        interval_days = 1
    elif p_interval == "Weekly":
        interval_days = 7
    elif p_interval == "Monthly":
        interval_days = 30
    else:
        p_interval = ""

    next_update = ""

    if p_interval:
        next_update_utc = last_update_utc + timedelta(days=interval_days)
        diff = current_time - next_update_utc
        if diff.days > 0:
            next_update_utc = next_update_utc + timedelta(days=diff.days)
        next_update = next_update_utc.strftime("%Y-%m-%d %H:%M:%S")

    if platform.system()=="Windows":
        from win32com.shell import shell
        schtask_cmd = os.getenv("SYSTEMROOT", "") + os.sep + "System32" + os.sep + "schtasks"

        # Create the scheduler task for checking updates if the user has admin privileges
        if shell.IsUserAnAdmin():
            # delete the previous scheduler if exists for checking the update
            try:
                delete_previous_taks = schtask_cmd + " /delete /tn check_pgc_update /f"
                schedule_return = system(delete_previous_taks, is_admin=True)
            except Exception as e:
                pass
            if p_interval:
                schedule_cmd = schtask_cmd + ' /create /RU System /tn check_pgc_update /tr "' + cmd + '"'\
                                 + " /sc once /st " + next_update_utc.strftime('%H:%M') \
                                 + " /sd " + next_update_utc.strftime('%m/%d/%Y')
                schedule_return = system(schedule_cmd, is_admin=True)
    else:
        cron_comment = "Cron to check the updates."
        cron_tab = CronTab(user=True)
        jobs = cron_tab.find_command(command=cmd)
        for job in jobs:
            job.delete()
        if p_interval:
            cron_job=cron_tab.new(command=cmd, comment=cron_comment)
            cron_job.minute.on(next_update_utc.minute)
            cron_job.hour.on(next_update_utc.hour)
            cron_job.day.on(next_update_utc.day)
            cron_job.month.on(next_update_utc.month)
        cron_tab.write()
        cron_tab.run_scheduler()

    update_sql = "UPDATE hosts " + \
                 " SET interval = '" + str(p_interval) + "', " + \
                 " next_update_utc = '" + next_update + "'" + \
                 " WHERE host = '" + str(p_host) + "'"
    exec_sql(update_sql)
    return


def get_versions_sql():
  return get_value ("GLOBAL", "VERSIONS", "versions.sql")


def get_stage():
  return get_value ("GLOBAL", "STAGE", "off")


def get_value (p_section, p_key, p_value=""):
  try:
    c = cL.cursor()
    sql = "SELECT s_value FROM settings WHERE section = ? AND s_key = ?"
    c.execute(sql, [p_section, p_key])
    data = c.fetchone()
    if data is None:
      return p_value
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_value()")
  return data[0]


def set_value (p_section, p_key, p_value):
  try:
    c = cL.cursor()
    sql = "DELETE FROM settings WHERE section = ? AND s_key = ?"
    c.execute(sql, [p_section, p_key])
    sql = "INSERT INTO settings (section, s_key, s_value) VALUES (?, ?, ?)"
    c.execute(sql, [p_section, p_key, p_value])
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "set_value()")
  return


def unset_value (p_section, p_key):
  try:
    c = cL.cursor()
    sql = "DELETE FROM settings WHERE section = ? AND s_key = ?"
    c.execute(sql, [p_section, p_key])
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "unset_value()")
  return


def get_pgc_hosts_file_name():
  pw_file=""
  pgc_host_dir = os.path.join(PGC_HOME, "conf")
  if get_platform() == "Windows":
    pw_file = os.path.join(pgc_host_dir, "pgc_hosts.conf")
  else:
    pw_file = os.path.join(pgc_host_dir, ".pgc_hosts")
  return(pw_file)


def get_pgc_host(p_host):
  try:
    c = cL.cursor()
    sql = "SELECT host,name,ssh_user,ssh_passwd,pgc_home,host_json FROM hosts where host=?"
    c.execute(sql,[p_host])
    data = c.fetchone()
    if data:
      l_host = data[0]
      l_user = data[2]
      l_passwd = data[3]
      l_pgc_home = data[4]
      return [l_pgc_home, l_user, l_passwd]
  except Exception as e:
    print ("ERROR: Retrieving host info")
    exit_message(str(e), 1)
  return ['','','']


def unregister(p_reg, isJson=False):
  if p_reg[0] not in ('HOST'):
    exit_message("not yet", 1)

  p_host = p_reg[1]
  try:
    c = cL.cursor()
    sql = "DELETE FROM hosts WHERE host = ?"
    c.execute(sql, [p_host])
    cL.commit()
  except Exception as e:
    print ("ERROR: unregistering the host")
    exit_message(str(e), 1)

def get_hosts_groups(p_group_id):
  try:
    c = cL.cursor()
    if p_group_id==1:
      sql="SELECT host,name,ssh_user,ssh_passwd,pgc_home,host_json,host_id FROM hosts"
      c.execute(sql)
    else:
      sql="SELECT host,name,ssh_user,ssh_passwd,pgc_home,host_json,host_id FROM hosts " \
          "where host_id in (select host_id from group_hosts where group_id=?)"
      c.execute(sql,[p_group_id])
    data = c.fetchall()
    return data
  except Exception as e:
    print(str(e))
  return None

def list_groups(isJson=False):
  try:
    has_groups=0
    groups_json_list=[]
    c = cL.cursor()
    sql = "SELECT group_id,group_name,group_type,group_json,parent_group_id FROM groups"
    c.execute(sql)
    data = c.fetchall()
    has_groups=0
    for row in data:
      has_groups=has_groups+1
      l_group_id = row[0]
      l_group = row[1]
      l_group_type = row[2]
      l_group_json = row[3]
      l_parent_group_id=row[4]
      if isJson:
        group_dict={}
        group_dict['group_id']=l_group_id
        group_dict['group']=l_group
        group_dict['group_type']=l_group_type
        group_dict['parent_group_id']=l_parent_group_id
        group_dict['hosts']=[]
        group_hosts=get_hosts_groups(l_group_id)
        if group_hosts:
          for row in group_hosts:
            l_host = row[0]
            l_name=row[1]
            l_user =row[2]
            l_passwd = row[3]
            l_pgc_home=row[4]
            host_dict={}
            host_dict['host_id']=row[6]
            host_dict['host']=l_host
            if l_host=="localhost":
              REPO=get_value('GLOBAL', 'REPO')
              host_dict['hostInfo']=api.info(True,PGC_HOME,REPO,False)
            else:
              host_dict['name']=str(l_name)
              host_dict['pgc_home']=str(l_pgc_home)
              host_dict['user']=str(l_user)
              host_dict['password']="*"*len(str(l_passwd))
              l_pgc_info=json.loads(str(row[5]))
              host_dict['hostInfo']=l_pgc_info[0]
            group_dict['hosts'].append(host_dict)
        groups_json_list.append(group_dict)
      else:
        print l_group
    if isJson:
        print (json.dumps(groups_json_list, sort_keys=True, indent=2))
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"list_groups()")
  if has_groups==0 and not isJson:
    p_msg="No groups registered"
    print (p_msg)

  return groups_json_list

def list_registrations(isJson=False):
  try:
    hosts_json_list=[]
    c = cL.cursor()
    sql = "SELECT host,name,ssh_user,ssh_passwd,pgc_home,host_json,host_id FROM hosts"
    c.execute(sql)
    data = c.fetchall()
    is_hosts_registered=0
    for row in data:
      l_host = row[0]
      l_name=row[1]
      l_user =row[2]
      l_passwd = row[3]
      l_pgc_home=row[4]
      if isJson:
        host_dict={}
        host_dict['host']=l_host
        host_dict['host_id']=row[6]
        if l_host=="localhost":
          REPO=get_value('GLOBAL', 'REPO')
          host_dict['hostInfo']=api.info(True,PGC_HOME,REPO,False)
        else:
          host_dict['name']=str(l_name)
          host_dict['pgc_home']=str(l_pgc_home)
          host_dict['user']=str(l_user)
          host_dict['password']="*"*len(str(l_passwd))
          l_pgc_info=json.loads(str(row[5]))
          host_dict['hostInfo']=l_pgc_info[0]
        hosts_json_list.append(host_dict)
      else:
        if not l_host=="localhost":
          is_hosts_registered=1
          print l_host+":"+l_pgc_home+":"+l_user+":"+l_passwd
    if isJson:
        print (json.dumps(hosts_json_list, sort_keys=True, indent=2))
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"list_registrations()")
  if is_hosts_registered==0 and not isJson:
    p_msg="No hosts registered"
    print (p_msg)

  return hosts_json_list


def check_remote_host(p_reg, isJson=False):
  from PgcRemote import PgcRemote
  host_info = p_reg[1:]
  try:
    remote = PgcRemote(host_info[0], host_info[2], host_info[3])
    remote.connect()
    # check if pgc_home directory exits
    pgc_home_exists = remote.is_exists(host_info[1])
    if pgc_home_exists:
      if isJson:
        json_dict = {}
        json_dict['state'] = "progress"
        json_dict['msg'] = "PGC HOME exists "
        print(json.dumps([json_dict]))
      else:
        print ("PGC HOME exists ")
    else:
      if isJson:
        pgc_setup="yes"
        json_dict = {}
        json_dict['state'] = "progress"
        json_dict['msg'] = "PGC_HOME doesn't exists we are setting up."
        print(json.dumps([json_dict]))
      else:
        try:
          pgc_setup=raw_input("PGC_HOME doesn't exist. Do you want to setup?")
        except Exception as e:
          pgc_setup="No"
      if pgc_setup == 'yes':
        pgc_version=get_pgc_version()
        pgc_file="bigsql-pgc-" + pgc_version + ".tar.bz2"
        repo = get_value("GLOBAL", "REPO")
        out_dir="/tmp"
        pgc_download_status=http_get_file(False,pgc_file,repo,out_dir,False,"")
        http_get_file(False,"install.py",repo,out_dir,False,"")
        if not pgc_download_status:
            return False
        remote.upload_pgc("/tmp", os.path.split(host_info[1])[0], pgc_version, repo)
      else:
        return False
    remote.disconnect()
  except Exception as e:
    errmsg = str(e)
    if isJson:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['msg'] = errmsg
      errmsg = json.dumps([json_dict])
    print (errmsg)
    return False
  return True


def update_remote_info(p_host,p_info):

    try:
        c = cL.cursor()
        update_sql = "UPDATE hosts SET host_json = ? WHERE host = ?"
        t=c.execute(update_sql, [str(p_info), str(p_host)])
        cL.commit()
    except Exception as e:
        print ("ERROR: updating info for host")
        exit_message(str(e), 1)
    return 0

def is_host_exists(p_name):
  try:
    c = cL.cursor()
    sql = "SELECT host FROM hosts where name=?"
    c.execute(sql,[p_name])
    data = c.fetchone()
    if data:
      return True
  except Exception as e:
    print ("ERROR: Retrieving host")
    exit_message(str(e), 1)
  return False

def register(p_reg, isJson=False):
  if p_reg[0] not in ('HOST'):
    exit_message("not yet", 1)

  host_array=p_reg[1:]
  try:
      p_host=host_array[0]
      p_home=host_array[1]
      p_ssh_user=host_array[2]
      p_ssh_pwd=host_array[3]
      p_name=p_host
      p_group="default"
      if len(host_array)>4:
          p_name=host_array[4]
      if len(host_array)>5:
          p_group=host_array[5]
      c = cL.cursor()
      if is_host_exists(p_name):
          sql = "UPDATE hosts SET host=?, name=?, ssh_user=?, ssh_passwd=?, pgc_home=? WHERE name = ?"
          c.execute(sql,[p_host, p_name, p_ssh_user, p_ssh_pwd, p_home, p_name])
      else:
          sql = "INSERT INTO hosts (host, name, ssh_user, ssh_passwd, pgc_home) VALUES (?, ?, ?, ?, ?)"
          c.execute(sql,[p_host, p_name, p_ssh_user, p_ssh_pwd, p_home])
      cL.commit()
      run_pgc_ssh(p_host, "info", True, True)
      if isJson:
        json_dict = {}
        json_dict['state'] = "completed"
        json_dict['msg'] = "Host registered successfully."
        print(json.dumps([json_dict]))

  except Exception as e:
    if isJson:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['msg'] = "ERROR: registering the host."+str(e)
      print(json.dumps([json_dict]))
    else:
      print ("ERROR: registering the host"+str(e))
      exit_message(str(e), 1)

  return 0


def get_group_id(p_group):
  try:
    c = cL.cursor()
    sql = "SELECT group_id FROM groups where group_name=?"
    c.execute(sql,[p_group])
    data = c.fetchone()
    if data:
      return data[0]
  except Exception as e:
    print ("ERROR: Retrieving group_id")
    exit_message(str(e), 1)
  return 0

def has_child_group(p_group_id):
  try:
    c = cL.cursor()
    sql = "SELECT group_id FROM groups where parent_group_id=?"
    c.execute(sql,[p_group_id])
    data = c.fetchall()
    if data:
      return True
  except Exception as e:
    print ("ERROR: Retrieving group_id")
    exit_message(str(e), 1)
  return False

def get_host_groups(p_host_id):
  try:
    c = cL.cursor()
    sql = "SELECT group_id FROM group_hosts where host_id=?"
    c.execute(sql,[p_host_id])
    data = c.fetchall()
    if data:
      return data
  except Exception as e:
    print ("ERROR: Retrieving host_groups")
    exit_message(str(e), 1)
  return False


def get_group_hosts(p_group_id):
  try:
    c = cL.cursor()
    sql = "SELECT host_id FROM group_hosts where group_id=?"
    c.execute(sql,[p_group_id])
    data = c.fetchall()
    if data:
      return data
  except Exception as e:
    print ("ERROR: Retrieving group_hosts")
    exit_message(str(e), 1)
  return False


def register_group(p_group, p_parent_group=0,p_group_id=0,isJson=False,printMsg=True):
    c = cL.cursor()
    msg="group registered successfully."
    if p_group_id>0:
      sql = "UPDATE groups set group_name=?, parent_group_id=? where group_id=?"
      c.execute(sql,[p_group,p_parent_group,p_group_id])
      msg="group updated successfully."
    else:
      sql = "INSERT INTO groups (group_name, parent_group_id) VALUES (?, ?)"
      c.execute(sql,[p_group,p_parent_group])
    cL.commit()
    if isJson:
        json_dict = {}
        json_dict['state'] = "completed"
        json_dict['msg'] = msg
        if printMsg:
          print(json.dumps([json_dict]))
        else:
          return json_dict
    else:
        print (msg)

def unregister_group(p_group, p_group_id=0,isJson=False,printMsg=True):
    c = cL.cursor()
    msg="group deleted successfully."
    state="completed"
    if p_group_id==0:
      p_group_id=get_group_id(p_group)
    has_childs=has_child_group(p_group_id)
    has_hosts=get_group_hosts(p_group_id)
    if p_group_id==1:
      state="error"
      msg="Default group cannot be deleted."
    elif p_group_id==0:
      state="error"
      msg="Group doesn't exist."
    elif has_childs or has_hosts:
      state="error"
      msg="group is not empty"
    else:
      sql = "DELETE FROM groups WHERE group_id = ?"
      c.execute(sql,[p_group_id])
      cL.commit()
    if isJson:
        json_dict = {}
        json_dict['state'] = state
        json_dict['msg'] = msg
        if printMsg:
          print(json.dumps([json_dict]))
        else:
          return json_dict
    else:
        print (msg)

def delete_hosts_group_mapping(p_group_id):
  try:
    c = cL.cursor()
    delete_sql = "delete FROM group_hosts WHERE group_id = ?"
    c.execute(delete_sql, [p_group_id])
    cL.commit()
  except Exception as e:
    print ("ERROR: updating info for host")
    exit_message(str(e), 1)
  return 0

def map_group_hosts(p_group, p_hosts, p_group_id=0, isJson=False, printMsg=True):
  c = cL.cursor()
  msg="servers added to the group successfully."
  if p_group_id==0:
    p_group_id=get_group_id(p_group)
  delete_hosts_group_mapping(p_group_id)
  for host_id in p_hosts:
    sql = "INSERT INTO group_hosts (group_id, host_id) VALUES (?, ?)"
    c.execute(sql,[p_group_id,host_id])
  cL.commit()
  if isJson:
    json_dict = {}
    json_dict['state'] = "completed"
    json_dict['msg'] = msg
    if printMsg:
      print(json.dumps([json_dict]))
    else:
      return json_dict
  else:
    print (msg)

def run_pgc_ssh(p_svr, p_cmd,isJson=False, cache=False):
  try:
    import paramiko
  except Exception as e:
    errmsg = "ERROR: Python 'paramiko' SSH module is not available"
    if isJson:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['msg'] = errmsg
      errmsg = json.dumps([json_dict])
    print(errmsg)

    sys.exit(1)

  from PgcRemote import PgcRemote

  [pgc_home, pgc_user, pgc_passwd] = get_pgc_host(p_svr)

  try:
    remote = PgcRemote(p_svr, username=pgc_user, password=pgc_passwd)
    remote.connect()
  except Exception as e:
    errmsg = "ERROR: Cannot connect to " + pgc_user + "@" + p_svr + " - " + str(e.args[0])
    if isJson:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['msg'] = errmsg
      errmsg = json.dumps([json_dict])
    print(errmsg)
    sys.exit(1)

  pgc_cmd = pgc_home + '/pgc ' + p_cmd

  if isJson:
    pgc_cmd = pgc_home + '/pgc ' + p_cmd + " --json"

  outlines = remote.execute(pgc_cmd)

  if isJson and p_cmd in ("info"):
    info_out= "".join(outlines['stdout']).replace('\n', '').replace('\r', '')
    update_remote_info(p_svr, info_out)

  if cache:
    return 0

  if outlines['stdout']:
    print (outlines['stdout'])

  rc = 0

  if outlines['stderr']:
    errmsg = "ERROR: running remote pgc command. "+ outlines['stderr']
    if isJson:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['msg'] = errmsg
      errmsg = json.dumps([json_dict])
    print(errmsg)

  return(rc)


def read_hosts (p_host):
  sql = "SELECT interval, last_update_utc, next_update_utc, unique_id \n" + \
        "  FROM hosts WHERE host = '" + p_host + "'"

  try:
    c = cL.cursor()
    c.execute(sql)
    data = c.fetchone()
    if data is None:
      return ["", "", "", ""]
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_host()")

  interval =  data[0]
  last_update_utc = data[1]
  next_update_utc = data[2]
  unique_id = data[3]

  return [interval, last_update_utc, next_update_utc, unique_id]


def is_password_less_ssh():
  cmd = "ssh -o 'PreferredAuthentications=publickey' localhost 'echo' >/dev/null 2>&1"
  rc = os.system(cmd)
  if rc:
    print("Error trying to do password-less SSH to localhost.")
    return False
  return True


def read_env_file(component):
  if str(platform.system()) == "Windows":
    from subprocess import check_output
    script = os.path.join(PGC_HOME, component, component+'-env.bat')
    if os.path.isfile(script):
      try:
        vars = check_output([script, '&&', 'set'], shell=True)
        for var in vars.splitlines():
          k, _, v = map(str.strip, var.strip().partition('='))
          if k.startswith('?'):
            continue
          os.environ[k] = v
      except Exception as e:
        my_logger.error(traceback.format_exc())
        pass
  else:
    script = os.path.join(PGC_HOME, component, component+'.env')
    if os.path.isfile(script):
        try:
          pipe1 = Popen(". %s; env" % script, stdout=PIPE, shell=True, executable="/bin/bash")
          output = pipe1.communicate()[0].strip()
          lines = output.split("\n")
          env = dict((line.split("=", 1) for line in lines))
          for e in env:
            os.environ[e] = env[e]
        except Exception as e:
          my_logger.error(traceback.format_exc())
          pass

  return


def remember_pgpassword(p_passwd, p_port):
  if get_platform() == "Windows":
    pw_dir  = os.getenv("APPDATA") + "\postgresql"
    if not os.path.isdir(pw_dir):
      os.mkdir(pw_dir)
    pw_file = pw_dir + "\pgpass.conf"
  else:
    pw_file = os.getenv("HOME") + "/.pgpass"

  if os.path.isfile(pw_file):
    s_pw = read_file_string(pw_file)
  else:
    s_pw = ""

  file = open(pw_file, 'w')
  ## pre-pend the new
  file.write("localhost:" + p_port + ":*:postgres:" + p_passwd + "\n")
  file.write("127.0.0.1:" + p_port + ":*:postgres:" + p_passwd + "\n")
  if s_pw > "":
    ## append the old
    file.write(s_pw)
  file.close()

  if not get_platform() == "Windows":
    os.chmod(pw_file, 0600)

  print (" ")
  print ("Password securely remembered in the file: " + pw_file)
  return pw_file


def update_postgresql_conf(p_pgver, p_port, is_new=True):
  ## does 'postgresql.conf' file exist for updating
  pg_data = get_column('datadir', p_pgver)
  config_file = pg_data + os.sep + "postgresql.conf"
  if not os.path.isfile(config_file):
    print ("ERROR: You may not (config)ure before (init)ialization.")
    sys.exit(1)
  if not os.access(config_file, os.W_OK):
    print ("ERROR: Write permission denied on 'postgresql.conf'.")
    sys.exit(1)

  ## set port in sqlite metadata
  set_column("port", p_pgver, str(p_port))

  ## set port in postgresql.conf
  s = read_file_string(config_file)
  ns = ""
  lines = s.split('\n')
  for line in lines:
    if line.startswith("port") or line.startswith("#port"):
      # always override port
      pt = "port = " + str(p_port) + \
             "\t\t\t\t# (change requires restart)"
      ns = ns + "\n" + pt

    elif is_new and line.startswith("#listen_addresses = 'localhost'"):
      # override default to match default for pg_hba.conf
      la = "listen_addresses = '*'" + \
              "\t\t\t# what IP address(es) to listen on;"
      ns = ns + "\n" + la

    elif is_new and line.startswith("#logging_collector"):
      ns = ns + "\n" + "logging_collector = on"

    elif is_new and line.startswith("#log_directory"):
      log_directory = os.path.join(PGC_HOME, "data", "logs", p_pgver).replace("\\", "/")
      ns = ns + "\n" + "log_directory = '" + log_directory + "'"

    elif is_new and line.startswith("#log_filename"):
      ns = ns + "\n" + "log_filename = 'postgresql-%a.log'"

    elif is_new and line.startswith("#log_line_prefix"):
      ns = ns + "\n" + "log_line_prefix =  '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '"

    elif is_new and line.startswith("#log_truncate_on_rotation"):
      ns = ns + "\n" + "log_truncate_on_rotation = on "

    elif is_new and line.startswith("#log_checkpoints"):
      ns = ns + "\n" + "log_checkpoints = on"

    elif is_new and line.startswith("#log_autovacuum_min_duration"):
      ns = ns + "\n" + "log_autovacuum_min_duration = 0"

    elif is_new and line.startswith("#log_temp_files"):
      ns = ns + "\n" + "log_temp_files = 0"

    elif is_new and line.startswith("#log_lock_waits"):
      ns = ns + "\n" + "log_lock_waits = on"

    elif is_new and line.startswith("#checkpoint_segments"):
      ns = ns + "\n" + "checkpoint_segments = 16"

    elif is_new and line.startswith("#maintenance_work_mem"):
      ns = ns + "\n" + "maintenance_work_mem = 64MB"

    elif is_new and line.startswith("#max_wal_senders"):
      ns = ns + "\n" + "max_wal_senders = 5"

    elif is_new and line.startswith("#track_io_timing"):
      ns = ns + "\n" + "track_io_timing = on"

    elif is_new and line.startswith("#wal_keep_segments"):
      ns = ns + "\n" + "wal_keep_segments = 32"

    elif is_new and line.startswith("#max_replication_slots"):
      ns = ns + "\n" + "max_replication_slots = 5"

    elif is_new and line.startswith("#wal_level"):
      ns = ns + "\n" + "wal_level = hot_standby"

    elif is_new and line.startswith("#update_process_title") and get_platform() == "Windows":
      ns = ns + "\n" + "update_process_title = off"

    else:
      if ns == "":
        ns = line
      else:
        ns = ns + "\n" + line
  write_string_file(ns, config_file)

  print (" ")
  print ("Using PostgreSQL Port " + str(p_port))
  return


def get_superuser_passwd():
  print (" ")
  try:
    while True:
      pg_pass1 = getpass.getpass("Superuser Password [password]: ")
      if pg_pass1.strip() == "":
        pg_pass1 = "password"
        break
      pg_pass2 = getpass.getpass("Confirm Password: ")
      if pg_pass1 == pg_pass2:
        break
      else:
        print (" ")
        print ("Password mis-match, try again.")
        print (" ")
        continue
  except KeyboardInterrupt as e:
    sys.exit(1)
  return pg_pass1;


def write_pgenv_file(p_pghome, p_pgver, p_pgdata, p_pguser, p_pgdatabase, p_pgport, p_pgpassfile):
  pg_bin_path = os.path.join(p_pghome, "bin")
  if get_platform() == "Windows":
    export = "set "
    source = "run"
    newpath = export + "PATH=" + pg_bin_path + ";%PATH%"
    env_file = p_pghome + os.sep + p_pgver + "-env.bat"
  else:
    export = "export "
    source = "source"
    newpath = export + "PATH=" + pg_bin_path + ":$PATH"
    env_file = p_pghome + os.sep + p_pgver + ".env"

  try:
    file = open(env_file, 'w')
    if get_platform() == "Windows":
      file.write('@echo off\n')
    file.write(export + 'PGHOME=' + p_pghome + '\n')
    file.write(export + 'PGDATA=' + p_pgdata + '\n')
    file.write(newpath + '\n')
    file.write(export + 'PGUSER=' + p_pguser + '\n')
    file.write(export + 'PGDATABASE=' + p_pgdatabase + '\n')
    file.write(export + 'PGPORT=' + p_pgport + '\n')
    file.write(export + 'PGPASSFILE=' + p_pgpassfile + '\n')
    file.write(export + 'PYTHONPATH=' + os.path.join(PGC_HOME, p_pgver, "python", "site-packages") + '\n')
    file.close()
    os.chmod(env_file, 0755)
  except IOError as e:
    return 1

  print (" ")
  print ("to load this postgres into your environment, " + source + " the env file: ")
  print ("    " + env_file)
  print (" ")
  return 0


####################################################################
# Check if port is already assigned
####################################################################
def is_port_assigned(p_port, p_comp):
  try:
    c = cL.cursor()
    sql = "SELECT port FROM components WHERE component != '" + \
          p_comp + "' and port='" + str(p_port) + "' and datadir !=''"
    c.execute(sql)
    data = c.fetchone()
    if data is None:
      return False
  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "is_port_assigned()")
  return True


####################################################################
# Get an available port
####################################################################
def get_avail_port(p_prompt, p_def_port, p_comp="", p_interactive=False):
  def_port = int(p_def_port)

  ## iterate to first non-busy port
  while (is_socket_busy(def_port, p_comp)):
    def_port = def_port + 1
    continue

  err_msg="Port must be between 1000 and 9999, try again."

  while True:
    if p_interactive:
      s_port = raw_input(p_prompt + "[" + str(def_port) + "]? ")
      if s_port == "":
        s_port = str(def_port)
    else:
      s_port = str(def_port)

    if (s_port.isdigit() == False):
      print (err_msg)
      continue

    i_port = int(s_port)

    if ( i_port < 1000 ) or ( i_port > 9999 ):
      print (err_msg)
      continue

    if is_port_assigned(i_port, p_comp) or is_socket_busy(i_port, p_comp):
      print ("Port " + str(i_port) + " is in use.")
      def_port = str(i_port + 1)
      continue

    break

  return i_port


####################################################################
# delete a directory using OS specific commands
####################################################################
def delete_dir(p_dir):
  if (get_platform() == "Windows"):
    cmd = 'RMDIR "' + p_dir + '" /s /q'
  else:
    cmd = 'rm -rf "' + p_dir + '"'
  rc = os.system(cmd)
  return rc


####################################################################
# optionally run a system level command as Admin/root
####################################################################
def system(p_cmd, is_admin=False, is_display=False):
  if is_display:
    print ("\n## " + p_cmd + " ##########")

  if is_admin:
    rc = runas_win_admin(p_cmd)
  else:
    rc = os.system(p_cmd)

  if is_display:
    print ("rc = " + str(rc))

  return rc


####################################################################
# round to scale & show integers without the ".0"
####################################################################
def pretty_rounder(p_num, p_scale):
  rounded = round(p_num, p_scale)
  if not (rounded % 1):
    return int(rounded)
  return rounded


####################################################################
# retrieve PGC version
####################################################################
def get_pgc_version():
  return (PGC_VERSION)


####################################################################
# retrieve project dependencies
####################################################################
def get_depend():
  dep = []
  try:
    c = cL.cursor()
    sql = "SELECT DISTINCT r1.component, r2.component, p.start_order \n" + \
          "  FROM projects p, releases r1, releases r2, versions v \n" + \
          " WHERE v.component = r1.component \n" + \
          "   AND " + like_pf("v.platform") +  " \n" + \
          "   AND p.project = r1.project \n" + \
          "   AND p.depends = r2.project \n" + \
          "ORDER BY 3"
    c.execute(sql)
    data = c.fetchall()
    for row in data:
      component = str(row[0])
      depends = str(row[1])
      p = component + " " + depends
      dep.append(p.split())
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_depend()")
  return dep


##################################################################
# Run the sql statements in a command file
##################################################################
def process_sql_file(p_file, p_json):
  isSilent = os.environ.get('isSilent', None)

  rc = True

  ## verify the hub version ##################
  file = open(p_file, 'r')
  cmd = ""
  for line in file:
    line_strip = line.strip()
    if line_strip == "":
      continue
    cmd = cmd + line
    if line_strip.endswith(";"):
      if ("hub" in cmd) and ("INSERT INTO versions" in cmd) and ("1," in cmd):
        cmdList = cmd.split(',')
        newHubV = cmdList[1].strip().replace("'", "")
        oldHubV = get_pgc_version()
        msg_frag = "'hub' from v" + oldHubV + " to v" + newHubV + "."
        if newHubV == oldHubV:
          msg = "'hub' is v" + newHubV
        if newHubV > oldHubV:
          msg = "Automatic updating " + msg_frag
        if newHubV < oldHubV:
          msg = "ENVIRONMENT ERROR:  Cannot downgrade " + msg_frag
          rc = False
        if p_json:
          print ('[{"status":"wip","msg":"'+msg+'"}]')
        else:
          if not isSilent:
            print (msg)
        my_logger.info(msg)
        break
      cmd = ""
  file.close()

  if rc == False:
    if p_json:
      print ('[{"status":"completed","has_updates":0}]')
    return False

  ## process the file ##########################
  file = open(p_file, 'r')
  cmd = ""
  for line in file:
    line_strip = line.strip()
    if line_strip == "":
      continue
    cmd = cmd + line
    if line_strip.endswith(";"):
      exec_sql(cmd)
      cmd = ""
  file.close()

  return True


##################################################################
# execute a sql command & commit it
##################################################################
def exec_sql(cmd):
  try:
    c = cL.cursor()
    c.execute(cmd)
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,cmd,"exec_sql()")


##################################################################
# Print key server metrics
##################################################################
def show_metrics(p_home, p_port, p_data, p_log, p_pid):
  return
  if not p_home == None:
    print ("  --homedir " + str(p_home))
  if not p_port == None:
    print ("  --port    " + str(p_port))
  if not p_data == None:
    print ("  --datadir " + p_data)
  if not p_log == None:
    print ("  --logfile " + p_log)
  if not p_pid == None:
    print ("  --pidfile " + p_pid)


####################################################################################
# Retrieve the string value of a column from Components table
####################################################################################
def get_column(p_column, p_comp, p_env=''):
  try:
    c = cL.cursor()
    sql = "SELECT " + p_column + " FROM components WHERE component = '" + p_comp + "'"
    c.execute(sql)
    data = c.fetchone()
    if data is None:
      return "-1"
    col_val = str(data[0])
    if col_val == "None" or col_val == "" or col_val is None:
      if p_env > '':
        if p_env.startswith('$'):
          env = os.getenv(p_env[1:], '')
        else:
          env = p_env
        if env > '':
          set_column(p_column, p_comp, env)
          return env
        else:
          return "-1"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_column()")
  return col_val


####################################################################################
# Update the value of a column for Components table
####################################################################################
def set_column(p_column, p_comp, p_value):
  try:
    c = cL.cursor()
    sql = "UPDATE components SET " + p_column + " = '" + str(p_value) + "' " + \
          " WHERE component = '" + p_comp + "'"
    c.execute(sql)
    cL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"set_column()")


def fatal_sql_error(err,sql,func):
  msg = "#"
  msg = msg + "\n" + "################################################"
  msg = msg + "\n" + "FATAL SQL Error in " + func
  msg = msg + "\n" + "    SQL Message =  " + err.args[0]
  msg = msg + "\n" + "  SQL Statement = " + sql
  msg = msg + "\n" + "################################################"
  print (msg)
  my_logger.error(msg)
  sys.exit(1)


####################################################################################
# Return the SHA512 checksum of a file
####################################################################################
def get_file_checksum(p_filename):
  BLOCKSIZE = 65536
  hasher = hashlib.sha512()
  with open(p_filename, 'rb') as afile:
    buf = afile.read(BLOCKSIZE)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(BLOCKSIZE)
  return(hasher.hexdigest())


####################################################################################
# Read contents of a small file directly into a string
####################################################################################
def read_file_string(p_filename):
  try:
    f = open(p_filename, 'r')
    filedata = f.read()
    f.close()
    return(filedata)
  except IOError as e:
    print (e)
    return ""


####################################################################################
# Write contents of string into file
####################################################################################
def write_string_file(p_stringname, p_filename):
  f = open(p_filename,'w')
  f.write(p_stringname)
  f.close()


####################################################################################
# search and replace simple strings on a file, in-place
####################################################################################
def replace(p_olddata, p_newdata, p_filename):
  filestring = read_file_string(p_filename)
  print("replace (" + p_olddata + ") with (" + p_newdata + ") on file (" + p_filename + ")")
  newstring = filestring.replace(p_olddata, p_newdata)
  write_string_file(newstring, p_filename)
  return


####################################################################################
# abruptly terminate a process id
####################################################################################
def kill_pid(pid):
  if (pid < 1):
    return
  if (get_platform() == "Windows"):
    os.kill(pid, 2)
  else:
    os.kill(pid, signal.SIGKILL)
  return


####################################################################################
# use the java JPS command to locate one or more java process id's by keyword
####################################################################################
def get_jps_pid(keyword):
  pid = 0
  out = ""
  err = ""

  jps = os.getenv("JAVA_HOME") + os.sep + "bin" + os.sep + "jps"

  args = [jps, '-lm']

  try:
    proc = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out, err = proc.communicate()
    rc = proc.returncode
  except OSError as e:
    msg = "unexpected error running the command '" + str(args) + "'"
    print (msg)
    my_logger.error(msg)
    my_logger.error(traceback.format_exc())
    return -1

  line = ""
  for char in out:
    if ( char == "\n" ):
      if keyword in line:
        return int(line.split()[0])
      line = ""
    else:
      line = line + char

  return pid


####################################################################################
# use the java JPS command to kill a process id by keyword
####################################################################################
def kill_jps_pid(keyword):
  v_pid = get_jps_pid(keyword)
  if v_pid > 0:
    msg = "  killing " + keyword + " (" + str(v_pid) + ")"
    print (msg)
    my_logger.info(msg)
    kill_pid(v_pid)
  else:
    msg = keyword + " is not running."
    print ("  " + msg)
    my_logger.info(msg)
  return 0


####################################################################################
# return the OS platform (Linux, Windows or Darwin)
####################################################################################
def get_platform():
  return str(platform.system())


####################################################################################
# returns the OS (osx, win, el6, el7, ubu14, ubu16, deb)
####################################################################################
def get_os():
  if platform.system() == "Darwin":
    return ("osx")

  if platform.system() == "Windows":
    return ("win")

  try:
    if os.path.exists("/etc/redhat-release"):
      ver = read_file_string("/etc/redhat-release").split()[3]
      if ver.startswith("7"):
        return "el7"
      else:
        return "el6"

    if os.path.exists("/etc/system-release"):
      ## Amazon Linux
      return "el6"

    if os.path.exists("/etc/lsb-release"):
      this_os = commands.getoutput("cat /etc/lsb-release | grep DISTRIB_DESCRIPTION | cut -d= -f2 | tr -d '\"'")
      ver = this_os.split()[1]
      if ver.startswith("14."):
        return "ubu14"
      elif ver.startswith("16."):
        return "ubu16"
      else:
        return "deb"
  except Exception as e:
    pass

  return ("el6")



####################################################################################
# return if the user has admin rights
####################################################################################
def has_admin_rights():
  status = True
  if get_platform() == "Windows":
    from win32com.shell import shell
    status = shell.IsUserAnAdmin()
  return status


####################################################################################
# return the default BIGSQL platform based on the OS
####################################################################################
def get_default_pf():
  if get_platform() == "Darwin":
    return "osx64"

  if get_platform() == "Windows":
    return "win64"

  ## for now we will always use LINUX64
  if get_platform() == "Linux":
    return "linux64"

  try:
    if os.path.exists("/etc/redhat-release"):
      ver = read_file_string("/etc/redhat-release").split()[3]
      if ver.startswith("7"):
        return "el7-x64"
      else:
        return "linux64"
    if os.path.exists("/etc/lsb-release"):
      this_os = commands.getoutput("cat /etc/lsb-release | grep DISTRIB_DESCRIPTION | cut -d= -f2 | tr -d '\"'")
      ver = this_os.split()[1]
      if ver.startswith("14"):
        return "ubu14-x64"
  except Exception as e:
    return "linux64"

  return "linux64"


####################################################################################
# return the BIGSQL platform
####################################################################################
def get_pf():
  return (get_value("GLOBAL", "PLATFORM", ""))


####################################################################################
# build up a LIKE clause for a SQL fragment appropriate for the platform
####################################################################################
def like_pf(p_col):
  pf = get_pf()
  OR = " OR "
  c1 = p_col + " LIKE ''"
  c2 = p_col + " LIKE '%" + pf + "%'"
  clause = "(" + c1 + OR + c2
  if pf in ("el7-x64", "ubu14-x64"):
    c3 = p_col + " LIKE '%linux64%'"
    clause = clause + OR + c3 + ")"
  else:
    clause = clause + ")"

  return clause


####################################################################################
# check if the current platform is in the list of component platforms
####################################################################################
def has_platform(p_platform):
  pf = get_pf()
  if "linux64" in p_platform and pf in ("el7-x64", "ubu14-x64"):
    return 0
  return p_platform.find(pf)


####################################################################################
# set the env variables
####################################################################################
def set_lang_path():
  perl_home = PGC_HOME + os.sep + 'perl5' + os.sep + 'perl'
  if os.path.exists(perl_home):
    os.environ['PERL_HOME'] = perl_home
    path = os.getenv('PATH')
    os.environ['PATH'] = perl_home + os.sep + 'site' + os.sep + 'bin' + os.pathsep + \
        perl_home + os.sep + 'bin' + os.pathsep + \
        PGC_HOME + os.sep + 'perl5' + os.sep + 'c' + os.sep + 'bin' + os.pathsep + path
  tcl_home = PGC_HOME + os.sep + 'tcl86'
  if os.path.exists(tcl_home):
    os.environ['TCL_HOME'] = tcl_home
    path = os.getenv('PATH')
    os.environ['PATH'] = tcl_home + os.sep + 'bin' + os.pathsep + path
  java_home = PGC_HOME + os.sep + 'java8'
  if os.path.exists(java_home):
    os.environ['JAVA_HOME'] = java_home
    path = os.getenv('PATH')
    os.environ['PATH'] = java_home + os.sep + 'bin' + os.pathsep + path


####################################################################################
# return the OS user name
####################################################################################
def get_user():
  if get_platform() == "Windows":
    return (os.getenv('USERNAME'))
  return (os.getenv('USER'))


####################################################################################
# return the OS hostname
####################################################################################
def get_host():
  if get_platform() == "Windows":
    return ("127.0.0.1")
  else:
    fqdn = commands.getoutput("hostname -f")
    return (fqdn)

def get_host_short():
  if get_platform() == "Windows":
    return ("127.0.0.1")
  else:
    host_short = commands.getoutput("hostname -s")
    return (host_short)

def get_host_ip():
  try:
    host_ip = socket.gethostbyname(get_host())
  except socket.gaierror as e:
    host_ip = "127.0.0.1"
  return(host_ip)


####################################################################################
# convert a Windows file name to a URI
####################################################################################
def make_uri(in_name):
  if get_platform() != "Windows":
    return (in_name)
  else:
    return('///' + in_name.replace("\\", "/"))


####################################################################################
# run a background job detached from the terminal
####################################################################################
def launch_daemon(arglist, p_logfile_name):

  if p_logfile_name == None:
    f_logfile = os.devnull
  else:
    f_logfile = p_logfile_name

  with open(f_logfile, "wb") as outfile:
    Popen(arglist, stdin=PIPE, stdout=outfile, stderr=STDOUT)

  return 0


####################################################################################
# delete a file (if it exists)
####################################################################################
def delete_file(p_file_name):
  if (os.path.isfile(p_file_name)):
    os.remove(p_file_name)
  return


def http_is_file(p_url):
  try:
    req = urllib2.Request(p_url, None, http_headers())
    u = urllib2.urlopen(req, timeout=10)
  except KeyboardInterrupt as e:
    sys.exit(1)
  except Exception as e:
    return(1)

  return(0)


def urlEncodeNonAscii(b):
  import re
  return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)


def http_headers():
  user_agent = 'PGC/' + get_pgc_version() + " " + get_anonymous_info()
  headers = { 'User-Agent' : urlEncodeNonAscii(user_agent) }
  return(headers)


## retrieve a remote file via http #################################################
def http_get_file(p_json, p_file_name, p_url, p_out_dir, p_display_status, p_msg, component_name=None):
  file_exists = False
  file_name_complete = p_out_dir + os.sep + p_file_name
  file_name_partial = file_name_complete + ".part"
  json_dict = {}
  json_dict['state'] = "download"
  if component_name is not None:
    json_dict['component'] = component_name
  if p_display_status:
    if not p_json:
      print (p_msg)
  try:
    delete_file(file_name_partial)
    file_url = p_url + '/' + p_file_name
    req = urllib2.Request(file_url, None, http_headers())
    u = urllib2.urlopen(req, timeout=10)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    file_size_dl = 0
    block_sz = 8192
    old_pct = 0.0
    old_size = 0
    f = open(file_name_partial,"wb")
    file_exists = True
    log_file_name = p_file_name.replace(".tar.bz2",'')
    log_msg = "Downloading file %s " % log_file_name
    is_checksum = False
    if p_file_name.find("sha512") >= 0:
      is_checksum = True
      log_file_name = p_file_name.replace(".tar.bz2.sha512",'')
      log_msg = "Downloading checksum for %s " % log_file_name
    my_logger.info(log_msg)
    previous_time = datetime.now()
    while True:
      if not p_file_name.endswith(".txt") and not os.path.isfile(pid_file):
        raise KeyboardInterrupt("No lock file exists.")
      buffer = u.read(block_sz)
      if not buffer:
        break
      file_size_dl += len(buffer)
      f.write(buffer)
      file_size_dl_mb = (file_size_dl / 1024 / 1024)
      download_pct = file_size_dl * 100 / file_size
      if p_display_status:
        if (file_size_dl_mb <> old_size) or (download_pct <> old_pct):
          if p_json:
            json_dict['status'] = "wip"
            json_dict['mb'] = get_file_size(file_size_dl)
            json_dict['pct'] = download_pct
            print (json.dumps([json_dict]))
          else:
            status = r"%s [%s]" % (get_file_size(file_size_dl), (str(download_pct) + "%"))
            status = status + chr(8)*(len(status)+1)
            print status,
            current_time=datetime.now()
            log_diff = current_time-previous_time
            if log_diff.seconds>0:
              previous_time=current_time
      old_size = file_size_dl_mb
      old_pct = download_pct
    if p_display_status and p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "download"
      json_dict['status'] = "complete"
      print (json.dumps([json_dict]))
  except (urllib2.URLError, urllib2.HTTPError) as e:
    msg = "url=" + p_url + ", file=" + p_file_name
    if p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "error"
      json_dict['msg'] = str(e)
      print (json.dumps([json_dict]))
    else:
      print("\n" + "ERROR: " + str(e))
      print("       " + msg)
    my_logger.error("Error while dowloading file %s (%s)",p_file_name,str(e))
    my_logger.error(traceback.format_exc())
    if file_exists and not f.closed:
      f.close()
    delete_file(file_name_partial)
    file_exists = False
    return(False)
  except socket.timeout as e:
    if p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "error"
      json_dict['msg'] = "Connection timed out while downloading."
      print (json.dumps([json_dict]))
    else:
      print("\n" + str(e))
    my_logger.error("Error while dowloading file %s (%s)",p_file_name,str(e))
    my_logger.error(traceback.format_exc())
    if file_exists and not f.closed:
      f.close()
    delete_file(file_name_partial)
    file_exists = False
    return(False)
  except (IOError, OSError) as e:
    if p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "error"
      json_dict['msg'] = str(e)
      print (json.dumps([json_dict]))
    else:
      print("\n" + str(e))
    my_logger.error("Error while dowloading file %s (%s)",p_file_name,str(e))
    my_logger.error(traceback.format_exc())
    if file_exists and not f.closed:
      f.close()
    delete_file(file_name_partial)
    file_exists = False
    return(False)
  except KeyboardInterrupt as e:
    if p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "download"
      json_dict['status'] = "cancelled"
      json_dict['msg'] = "Download cancelled"
      print (json.dumps([json_dict]))
    else:
      print("Download Cancelled")
    my_logger.error("Cancelled dowloading file %s ",p_file_name)
    if file_exists and not f.closed:
      f.close()
    delete_file(file_name_partial)
    file_exists = False
    return(False)
  except ValueError as e:
    if p_json:
      json_dict.clear()
      if component_name is not None:
        json_dict['component'] = component_name
      json_dict['state'] = "error"
      json_dict['msg'] = str(e)
      print (json.dumps([json_dict]))
    else:
      print("\n" + str(e))
    my_logger.error("Error while dowloading file %s (%s)",p_file_name,str(e))
    my_logger.error(traceback.format_exc())
    if file_exists and not f.closed:
      f.close()
    delete_file(file_name_partial)
    file_exists = False
    return(False)
  finally:
    if file_exists and not f.closed:
      f.close()
  delete_file(file_name_complete)
  f.close()
  os.rename(file_name_partial, file_name_complete)
  return(True);


def is_writable(path):
    try:
        testfile = tempfile.TemporaryFile(dir = path)
        testfile.close()
    except (IOError, OSError) as err:
        return False
    return True


## is running with Admin/Root priv's #########################################
def is_admin():
  rc = 0
  if get_platform() == "Windows":
    try:
      import subprocess
      result = subprocess.Popen("net session", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
      std_out, std_err = result.communicate()
      rc = result.returncode
      if rc != 0:
        my_logger.error(std_err)
    except Exception as e:
      my_logger.error(str(e))
      rc = e.errno
  else:
    rc = commands.getoutput("id -u")

  if str(rc) == "0":
    return(True)
  else:
    return(False)


## run command escalated as Windows Administrator ############################
def runas_win_admin(p_cmd, p_wait=True):
    if os.name != 'nt':
        raise RuntimeError, "This function is only implemented on Windows."

    import win32api, win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

    list_cmd = p_cmd.split()

    cmd = '"%s"' % (list_cmd[0],)
    params = " ".join(['"%s"' % (x,) for x in list_cmd[1:]])
    cmdDir = ''
    showCmd = win32con.SW_SHOWNORMAL
    lpVerb = 'runas'  # causes UAC elevation prompt.

    procInfo = ShellExecuteEx(nShow=showCmd,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb=lpVerb,
                              lpFile=cmd,
                              lpParameters=params)

    if p_wait:
        procHandle = procInfo['hProcess']
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)
    else:
        rc = None

    return rc


def is_protected(p_comp, p_platform):
  if p_comp.startswith("python") or p_comp.startswith("postgres"):
    return True
  return False


def is_server(p_comp, p_port):
  if str(p_port) > "0":
    return True
  return False


def print_error(p_error):
  print('')
  print('ERROR: ' + p_error)
  return


## Get Component Datadir ###################################################
def get_comp_datadir(p_comp):
  try:
    c = cL.cursor()
    sql = "SELECT datadir FROM components WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return "NotInstalled"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_comp_state()")
  if data[0] is None:
    return ""
  return str(data[0])


## Get parent component for extension
def get_parent_component(p_ext, p_ver):
  try:
    c = cL.cursor()
    sql = "SELECT parent FROM versions WHERE component = ? "
    if p_ver!=0:
      sql = sql + " AND version = '" + p_ver + "'"
    c.execute(sql,[p_ext])
    data = c.fetchone()
    if data is None:
      return ""
  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "get_parent_component()")
  return str(data[0])


## Get Component State #####################################################
def get_comp_state(p_comp):
  try:
    c = cL.cursor()
    sql = "SELECT status FROM components WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return "NotInstalled"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_comp_state()")
  return str(data[0])


## Get Component Port ######################################################
def get_comp_port(p_comp):
  try:
    c = cL.cursor()
    sql = "SELECT port FROM components WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return "-1"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_comp_port()")
  return str(data[0])


# Check if the port is inuse
def is_socket_busy(p_port, p_comp=''):

  if p_comp > '':
    if get_platform() == "Windows":
      is_ready_file = "pg_isready.exe"
    else:
      is_ready_file = "pg_isready"
    isready = os.path.join(os.getcwd(), p_comp, 'bin', is_ready_file)
    if os.path.isfile(isready):
      rc = os.system(isready + ' -q -p ' + str(p_port))
      if rc == 0:
        return True
      else:
        return False

  s =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if p_comp == "bam2":
    result = s.connect_ex(("127.0.0.1", p_port))
  else:
    result = s.connect_ex((get_host_ip(), p_port))
  s.close()
  if result == 0:
    return True
  else:
    return False


## Get Component category ######################################################
def get_comp_category(p_comp):
  try:
    c = cL.cursor()
    sql = "SELECT p.category FROM projects p,components c WHERE component = ? and p.project=c.project"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return None
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_comp_port()")
  return data[0]


#get the list for files in a folder recursively:
def get_files_recursively(directory):
  for root, dirs, files in os.walk(directory):
    for basename in files:
      filename = os.path.join(root, basename)
      yield filename


# create the manifest file for the extension
def create_manifest(ext_comp, parent_comp,upgrade=None):
  PARENT_DIR = os.path.join(PGC_HOME, parent_comp)
  COMP_DIR = os.path.join(PGC_HOME, ext_comp)
  if upgrade:
      COMP_DIR=os.path.join(COMP_DIR+"_new", ext_comp)

  manifest = {}
  manifest['component'] = ext_comp
  manifest['parent'] = parent_comp

  target_files = []

  files_list = get_files_recursively(COMP_DIR)
  for file in files_list:
    target_file = file.replace(COMP_DIR, PARENT_DIR)
    target_files.append(target_file)

  manifest['files'] = target_files

  manifest_file_name = ext_comp + ".manifest"

  manifest_file_path = os.path.join(PGC_HOME, "conf", manifest_file_name)

  try:
    with open(manifest_file_path, 'w') as f:
      json.dump(manifest, f, sort_keys = True, indent = 4)
  except Exception as e:
    my_logger.error(str(e))
    my_logger.error(traceback.format_exc())
    print (str(e))
    pass

  return True


#copy the extension files to parent component
def copy_extension_files(ext_comp, parent_comp,upgrade=None):
  PARENT_DIR = os.path.join(PGC_HOME, parent_comp)
  COMP_DIR = os.path.join(PGC_HOME, ext_comp)
  if upgrade:
      COMP_DIR=os.path.join(COMP_DIR+"_new", ext_comp)
  comp_dir_list = os.listdir(COMP_DIR)
  for l in comp_dir_list:
    source = os.path.join(COMP_DIR, l)
    try:
      if os.path.isdir(source):
        target = os.path.join(PARENT_DIR, l)
        copy_tree(source, target, preserve_symlinks=True)
      else:
        shutil.copy(source, PARENT_DIR)
    except Exception as e:
      my_logger.error("Failed to copy " + str(e))
      my_logger.error(traceback.format_exc())
      print (str(e))
      pass

  return True


#Check and delete the files mentioned in the manifest file
def delete_extension_files(manifest_file,upgrade=None):
    my_logger.info("checking for extension files.")
    try:
        with open(manifest_file) as data_file:
            data = json.load(data_file)
    except Exception as e:
        print (str(e))
        exit(1)
    for file in data['files']:
        if os.path.isfile(file) or os.path.islink(file):
            pass
        else:
            continue
        try:
            fp = open(file)
            fp.close()
        except IOError as e:
            if upgrade:
                raise e
            print (str(e))
            exit(1)
    my_logger.info("deleting extension files.")
    for file in data['files']:
        if os.path.isfile(file) or os.path.islink(file):
            pass
        else:
            continue
        try:
            os.remove(file)
        except IOError as e:
            my_logger.error("failed to remove " + file)
            my_logger.error(str(e))
            my_logger.error(traceback.format_exc())
            print (str(e))
    return True


## Get file size in readable format
def get_file_size(file_size,precision=1):
    suffixes=['B','KB','MB','GB','TB']
    suffixIndex = 0
    while file_size > 1024:
        suffixIndex += 1 #increment the index of the suffix
        file_size = file_size/1024.0 #apply the division
    return "%.*f %s"%(precision,file_size,suffixes[suffixIndex])


def get_readable_time_diff(amount, units='seconds', precision=0):

    def process_time(amount, units):

        INTERVALS = [1, 60,
                     60*60,
                     60*60*24,
                     60*60*24*7,
                     60*60*24*7*4,
                     60*60*24*7*4*12]

        NAMES = [('second', 'seconds'),
                 ('minute', 'minutes'),
                 ('hour', 'hours'),
                 ('day', 'days'),
                 ('week', 'weeks'),
                 ('month', 'months'),
                 ('year', 'years')]

        result = []

        unit = map(lambda a: a[1], NAMES).index(units)
        # Convert to seconds
        amount = amount * INTERVALS[unit]

        for i in range(len(NAMES)-1, -1, -1):
            a = amount // INTERVALS[i]
            if a > 0:
                result.append((a, NAMES[i][1 % a]))
                amount -= a * INTERVALS[i]

        return result

    if int(amount)==0:
      return "0 Seconds"
    rd = process_time(int(amount), units)
    cont = 0
    for u in rd:
        if u[0] > 0:
            cont += 1

    buf = ''
    i = 0

    if precision > 0 and len(rd) > 2:
        rd = rd[:precision]
    for u in rd:
        if u[0] > 0:
            buf += "%d %s" % (u[0], u[1])
            cont -= 1

        if i < (len(rd)-1):
            if cont > 1:
                buf += ", "
            else:
                buf += " and "

        i += 1

    return buf


## check bam prerequisites to start
def check_python_tools_ssl(comp_name):
    is_passed = True
    try:
        import pkg_resources
    except ImportError as e:
        print ("Python-setuptools is required for " + comp_name)
        is_passed = False
        pass
    try:
        import OpenSSL
    except ImportError as e:
        print ("PyOpenSSL is required for " + comp_name)
        is_passed = False
        pass
    return is_passed


## get the latest log file from the specified log directory
def find_most_recent(directory, partial_file_name):

  if not os.path.isdir(directory):
    return None

  # list all the files in the directory
  files = os.listdir(directory)

  # remove all file names that don't match partial_file_name string
  files = filter(lambda x: x.find("offset") == -1, files)
  files = filter(lambda x: x.find(partial_file_name) > -1, files)

  # create a dict that contains list of files and their modification timestamps
  name_n_timestamp = dict([(x, os.stat(directory + os.sep + x).st_mtime) for x in files])

  if name_n_timestamp:
    # return the file with the latest timestamp
    return max(name_n_timestamp, key=lambda k: name_n_timestamp.get(k))
  return None


# recursively check and restore all env / extension files during upgrade
def recursively_copy_old_files(dcmp, diff_files=[], ignore=None):
  for name in dcmp.left_only:
    if ignore and name in ignore:
        continue
    try:
      source_file = os.path.join(dcmp.left, name)
      shutil.move(source_file, dcmp.right)
    except Exception as e:
      my_logger.error("Failed to restore the file %s due to %s" % (os.path.join(dcmp.right, name), str(e)))
      my_logger.error(traceback.format_exc())
      diff_files.append([name, dcmp.left, dcmp.right])
  for sub_dcmp in dcmp.subdirs.values():
    allfiles = diff_files
    recursively_copy_old_files(sub_dcmp, allfiles)
  return diff_files


# restore any extensions or env/conf files during upgrade
def restore_conf_ext_files(src, dst, ignore=None):
  if os.path.isdir(dst):
    diff = filecmp.dircmp(src, dst)
    extension_files_list = recursively_copy_old_files(diff, ignore=ignore)
  return True


def check_running_version(ver, running_version):
    try:

        version = semver.parse(ver)
        installed_version = semver.parse(running_version)
        for k in ["major", "minor", "patch"]:
            if installed_version[k] == version[k]:
                continue
            else:
                return False
    except Exception as e:
        return ver.startswith(running_version)
    return True


# create a short link in windows start menu and taskbar
def create_short_link_windows(short_link, target_link, link_desc=None,
                              parent_folder="PostgreSQL",
                              add_to_taskbar=False, logged_user_only=False):
  cmd_file = tempfile.mktemp(".ps1")
  fh = open(cmd_file, "w")
  fh.write('$objShell = New-Object -ComObject ("WScript.Shell")' + '\n')
  shortlink_dir = os.path.join(os.getenv("programdata"), "Microsoft",
                               "Windows", "Start Menu", "Programs",
                               parent_folder)
  if logged_user_only:
    shortlink_dir = os.path.join(os.getenv("appdata"), "Microsoft",
                                 "Windows", "Start Menu", "Programs",
                                 parent_folder)

  if not os.path.exists(shortlink_dir):
    os.mkdir(shortlink_dir)

  shortlink_file = os.path.join(shortlink_dir, short_link)
  fh.write('$objShortCut = $objShell.CreateShortcut("{0}")'.format(shortlink_file) + '\n')
  fh.write('$objShortCut.TargetPath="{0}"'.format(target_link) + '\n')

  if link_desc:
    fh.write('$objShortCut.Description="{0}"'.format(link_desc) + '\n')

  fh.write('$objShortCut.Save()' + '\n')

  # add to taskbar
  if add_to_taskbar:
    fh.write('$Shell = New-Object -ComObject Shell.Application' + '\n')
    fh.write('$FilePath = "{0}"'.format(target_link) + '\n')
    fh.write('$NameSpace = $Shell.NameSpace((Split-Path $FilePath))' + '\n')
    fh.write('$File = $NameSpace.ParseName((Split-Path $FilePath -Leaf))' + '\n')
    fh.write('$verb = $File.Verbs() | ? {$_.Name -eq "Pin to Tas&kbar"}' + '\n')
    fh.write('if ($verb) {$verb.DoIt()}' + '\n')

  fh.close()

  powershell_path = os.path.join(os.getenv("SYSTEMROOT"),
                                 "System32", "WindowsPowerShell",
                                 "v1.0", "powershell.exe")
  command_to_run = "{0} -ExecutionPolicy ByPass -NoProfile {1}".format(powershell_path, cmd_file)
  system(command_to_run, is_admin=True)


# delete the shortlinks
def delete_shortlink_windows(short_link, parent_folder="PostgreSQL"):
    parent_path = os.path.join(os.getenv("programdata"), "Microsoft",
                               "Windows", "Start Menu", "Programs",
                               parent_folder)
    shortlink_path = os.path.join(parent_path, short_link)
    delete_file(shortlink_path)
    if not os.listdir(parent_path):
        delete_dir(parent_path)


# Add the application to launchpad in OSX
def create_shortlink_osx(short_link, target_link):
    short_link_path = os.path.join("/Applications", short_link)
    cmd = "ln -s '{0}' '{1}'".format(target_link, short_link_path)
    os.system(cmd)
    os.system('killall Dock')


# delete the application from launchpad in OSX
def delete_shortlink_osx(short_link):
    short_link_path = os.path.join("/Applications", short_link)
    cmd = "rm '{0}'".format(short_link_path)
    if os.path.exists(short_link_path):
        os.system(cmd)
        os.system('killall Dock')


## MAINLINE ################################################################
cL = sqlite3.connect(os.getenv("PGC_HOME") + os.sep + "conf" + os.sep + "pgc_local.db", check_same_thread=False)
