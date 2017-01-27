####################################################################
###########       Copyright (c) 2016 BigSQL           ##############
####################################################################

import sys
if sys.version_info >= (3, 0):
  print("Currently we run best on Python 2.7")
  sys.exit(1)
IS_64BITS = sys.maxsize > 2**32
if not IS_64BITS:
  print("This is a 32bit machine and BigSQL packages are 64bit.\n"
        "Cannot continue")
  sys.exit(1)

import os
import socket
import commands, subprocess
import time
import datetime
import hashlib
import platform
import tarfile
import sqlite3
import time
import json
import glob
from shutil import copy2, copytree
import re
import io
import errno
import traceback

## Our own library files ##########################################
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
import util, api, update_hub
import logging
import logging.handlers
from PgInstance import PgInstance
from semantic_version import Version


if not util.is_writable(os.path.join(os.getenv('PGC_HOME'), 'conf')):
  print("You must run as administrator/root.")
  exit()

## Verify that the SQLite MetaData is up to date
update_hub.verify_metadata()

if util.get_value("GLOBAL", "PLATFORM", "") in ("", "posix", "windoze"):
  util.set_value("GLOBAL", "PLATFORM", util.get_default_pf())

try:
    ## Globals and other Initializations ##############################
    LOG_FILENAME = os.getenv('PGC_LOGS')
    LOG_DIRECTORY = os.path.split(LOG_FILENAME)[0]

    if not os.path.isdir(LOG_DIRECTORY):
      os.mkdir(LOG_DIRECTORY)

    # Set up a specific logger with our desired output level
    my_logger = logging.getLogger('pgcli_logger')
    COMMAND = 9
    logging.addLevelName(COMMAND, "COMMAND")
    my_logger.setLevel(logging.DEBUG)


    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] : %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
except (IOError, OSError) as err:
    print(str(err))
    if err.errno in (errno.EACCES, errno.EPERM):
      print("You must run as administrator/root.")
    exit()

if util.get_platform() == "Windows":
  if not util.is_admin():
    print("You must run as administrator/root.")
    exit()

ansi_escape = re.compile(r'\x1b[^m]*m')

dep9 = util.get_depend()
mode_list = ["start", "stop", "restart", "status", "list", "info", "update",
             "upgrade", "enable", "disable", "install", "remove", "reload",
             "activity", "help", "dbstat", "get", "set", "unset",
             "register", "unregister", "top", "--autostart", "--relnotes",
             "--help", "--json", "--test", "--old", "--extensions",
             "--host", "--list"]
mode_list_advanced = ['kill', 'config', 'deplist', 'download',
                      'verify', 'init', 'clean']

no_log_commands = ['status', 'info', 'list', 'activity']

lock_commands = ["install", "remove", "update", "upgrade"]

available_dbstats = ['get_aggregate_tps']

my_depend = []
installed_comp_list = []
global check_sum_match
check_sum_match = True

backup_dir = os.path.join(os.getenv('PGC_HOME'), 'conf', 'backup')
backup_target_dir = os.path.join(backup_dir, time.strftime("%Y%m%d%H%M"))

pid_file = os.path.join(os.getenv('PGC_HOME'), 'conf', 'pgc.pid')

PGC_ISJSON = os.environ.get("PGC_ISJSON", "False")


###################################################################
## Subroutines ####################################################
###################################################################

def get_dependent_components(p_comp):
  data = []
  sql = "SELECT c.component FROM projects p, components c \n" + \
        " WHERE p.project = c.project AND p.depends = \n" + \
        "   (SELECT project FROM releases \n" + \
        "     WHERE component = '" + p_comp + "')"
  try:
    c = connL.cursor()
    c.execute(sql)
    data = c.fetchall()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_dependent_components")
  return data


## is there a dependency violation if component where removed ####
def is_depend_violation(p_comp, p_remove_list):
  data = get_dependent_components(p_comp)

  kount = 0
  vv = []
  for i in data:
    if str(i[0]) in p_remove_list:
      continue
    kount = kount + 1
    vv.append(str(i[0]))

  if kount == 0:
    return False

  errMsg = "Failed to remove " + p_comp + "(" + str(vv) + " is depending on this)."
  if isJSON:
    dict_error = {}
    dict_error['status'] = "error"
    dict_error["msg"] = errMsg
    msg = json.dumps([dict_error])
  else:
    msg = "ERROR-DEPENDENCY-LIST: " + str(vv)

  my_logger.error(errMsg)

  print(msg)
  return True


## run external scripts #########################
def run_script (componentName, scriptName, scriptParm):
  if componentName not in installed_comp_list:
    return

  # Todo : Commented as extensions has '-' in the component name
  # componentDir = componentName.replace("-", os.sep)
  componentDir = componentName

  cmd=""
  scriptFile = os.path.join(PGC_HOME, componentDir, scriptName)

  if (os.path.isfile(scriptFile)):
    cmd = "bash"
  else:
    cmd = "python -u"
    scriptFile = scriptFile + ".py"

  rc = 0
  compState = util.get_comp_state(componentName)
  if compState == "Enabled" and os.path.isfile(scriptFile):
    run_cmd = cmd + ' ' + scriptFile + ' ' + scriptParm
    if str(platform.system()) == "Windows" and ' ' in scriptFile:
      run_cmd = '%s "%s" %s' % (cmd, scriptFile, scriptParm)
      rc = subprocess.Popen(run_cmd).wait()
    else:
      rc = os.system(run_cmd)

  if rc != 0:
    print('Error running ' + scriptName)
    exit_cleanly(1)

  return;


## Get Dependency List #########################################
def get_depend_list(p_list, p_display=True):
  if p_list == ['all']:
     if p_mode=="install":
       pp_list = available_comp_list
     else:
       pp_list = installed_comp_list
  else:
     pp_list = p_list
  ndx = 0
  deplist = []
  for c in pp_list:
    ndx = ndx + 1
    new_list = list_depend_recur(c)
    deplist.append(c)
    for c1 in new_list:
      deplist.append(c1)

  deplist = set(deplist)

  num_deplist = []
  ndx = 0
  for ndx, comp in enumerate(deplist):
    num_deplist.append(get_comp_num(comp) + ':' + str(comp))

  sorted_depend_list = []
  for c in sorted(num_deplist):
    comp = str(c[4:])
    if comp != "hub":
      sorted_depend_list.append(c[4:])

  msg = '  ' + str(sorted_depend_list)
  my_logger.info(msg)
  if isJSON:
    dictDeplist = {}
    dictDeplist["state"] = "deplist"
    dictDeplist["component"] = p_list
    dictDeplist["deps"] = sorted_depend_list
    msg = json.dumps([dictDeplist])
  if p_display:
    if not isSilent:
      print(msg)
  return sorted_depend_list


## Get Component Version ###################################################
def get_version(p_comp):
  try:
    c = connL.cursor()
    sql = "SELECT version FROM components WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return ""
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_version()")
  return str(data[0])


## Get current Version ###################################################
def get_current_version(p_comp):
  try:
    c = connL.cursor()
    sql = "SELECT version FROM versions WHERE component = ? AND is_current=1"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return ""
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_version()")
  return str(data[0])


## Check if the component is required for this platform ###################################
def is_dependent_platform(p_comp):
  try:
    c = connL.cursor()
    sql = "SELECT platform FROM versions WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return False
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"is_dependent_platform()")
  platform = str(data[0])
  if len(platform.strip()) == 0 or util.has_platform(platform) >= 0:
    return True
  return False


# Check if component is already downloaded
def is_downloaded(p_comp, component_name=None):
  conf_cache = "conf" + os.sep + "cache"
  bz2_file = p_comp + ".tar.bz2"
  checksum_file = bz2_file + ".sha512"

  if os.path.isfile(conf_cache + os.sep + checksum_file):
    if validate_checksum(conf_cache + os.sep + bz2_file, conf_cache + os.sep + checksum_file):
      return (True)

  msg = ""
  if not util.http_get_file(isJSON, checksum_file, REPO, conf_cache, False, msg, component_name):
    return (False)

  return validate_checksum(conf_cache + os.sep + bz2_file, conf_cache + os.sep + checksum_file)


## Get Component Version & Platform ########################################
def get_ver_plat(p_comp):
  try:
    c = connL.cursor()
    sql = "SELECT version, platform FROM components WHERE component = ?"
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return "-1"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_ver_plat()")
  version = str(data[0])
  platform = str(data[1])
  if platform == "":
    return(version)
  return(version + "-" + platform)


## Get latest current version & platform ###################################
def get_latest_ver_plat(p_comp, p_new_ver=""):
  try:
    c = connL.cursor()
    sql = "SELECT version, platform FROM versions " + \
          " WHERE component = ? AND is_current = 1 " + \
          "   AND " + util.like_pf("platform")
    c.execute(sql,[p_comp])
    data = c.fetchone()
    if data is None:
      return "-1"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_latest_ver_plat()")
  if p_new_ver == "":
    version = str(data[0])
  else:
    version = p_new_ver
  platform = str(data[1])
  pf = util.get_pf()
  if platform == "":
    ver_plat = version
  else:
    if pf in platform:
      ver_plat = version + "-" + pf
    else:
      ver_plat = version + "-linux64"
  return(ver_plat)


## Get platform specific version for component ###############################
def get_platform_specific_version(p_comp,p_ver):
  try:
    c = connL.cursor()
    sql = "SELECT version, platform FROM versions " + \
          " WHERE component = ? " + \
          "   AND " + util.like_pf("platform") + \
          "   AND version = ?"
    c.execute(sql,[p_comp,p_ver])
    data = c.fetchone()
    if data is None:
      return "-1"
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_platform_specific_version()")
  version = str(data[0])
  platform = str(data[1])
  if platform == "":
    return(version)
  return(version + "-" + util.get_pf())

## Get Component Number ####################################################
def get_comp_num(p_app):
  ndx = 0
  for comp in dep9:
    ndx = ndx + 1
    if comp[0] == p_app:
      if ndx < 10:
        return "00" + str(ndx)
      else:
        return "0" + str(ndx)

      return ndx
  return "000"


# get percentage of unpack progress in json format
class ProgressTarExtract(io.FileIO):
  component_name = ""

  def __init__(self, path, *args, **kwargs):
    self._total_size = os.path.getsize(path)
    io.FileIO.__init__(self, path, *args, **kwargs)

  def read(self, size):
    if not os.path.isfile(pid_file):
      raise KeyboardInterrupt("No lock file exists.")
    percentage = self.tell()*100/self._total_size
    if isJSON:
      json_dict = {}
      json_dict['state'] = "unpack"
      json_dict['status'] = "wip"
      json_dict['pct'] = int(percentage)
      json_dict['component'] = self.component_name
      print(json.dumps([json_dict]))
    return io.FileIO.read(self, size)


## Install Component ######################################################
def install_comp(p_app, p_ver=0, p_rver=None):
  if p_ver is None:
    p_ver = 0
  if p_rver:
    parent = util.get_parent_component(p_app, p_rver)
  else:
    parent = util.get_parent_component(p_app, p_ver)
  if parent !="":
    parent_state = util.get_comp_state(parent)
    if parent_state == "NotInstalled":
      print("{0} has to be installed before installing {1}".format(parent, p_app))
      exit_cleanly(1)

  state = util.get_comp_state(p_app)
  if state == "NotInstalled":
    if p_ver ==  0:
      ver = get_latest_ver_plat(p_app)
    else:
      ver = p_ver
    base_name = p_app + "-" + ver
    conf_cache = "conf" + os.sep + "cache"
    file = base_name + ".tar.bz2"
    bz2_file = conf_cache + os.sep + file
    json_dict = {}
    json_dict['component'] = p_app
    json_dict['file'] = file
    if isJSON:
      json_dict['state'] = "download"
      json_dict['status'] = "start"
      print(json.dumps([json_dict]))

    if os.path.exists(bz2_file) and is_downloaded(base_name, p_app):
      msg = "File is already downloaded."
      my_logger.info(msg)
      if isJSON:
        json_dict['status'] = "complete"
        msg = json.dumps([json_dict])
      if not isSilent:
        print(msg)
    elif not retrieve_comp(base_name, p_app):
      exit_cleanly(1)

    msg = " Unpacking " + file
    my_logger.info(msg)
    if isJSON:
      json_dict['state'] = "unpack"
      json_dict['status'] = "start"
      json_dict['msg'] = msg
      msg = json.dumps([json_dict])
    if not isSilent:
      print(msg)
    tarFileObj = ProgressTarExtract("conf" + os.sep + "cache" + os.sep + file)
    tarFileObj.component_name = p_app
    tar = tarfile.open(fileobj=tarFileObj, mode="r:bz2")
    try:
      tar.extractall(path=".")
    except KeyboardInterrupt as e:
      temp_tar_dir = os.path.join(PGC_HOME, p_app)
      util.delete_dir(temp_tar_dir)
      msg = "Unpacking cancelled for file %s" % file
      my_logger.error(msg)
      return_code = 1
      if isJSON:
        json_dict = {}
        json_dict['state'] = "unpack"
        json_dict['status'] = "cancelled"
        json_dict['component'] = p_app
        json_dict['msg'] = msg
        msg = json.dumps([json_dict])
        return_code = 0
      util.exit_message(msg, return_code)
    except Exception as e:
      temp_tar_dir = os.path.join(PGC_HOME, p_app)
      util.delete_dir(temp_tar_dir)
      msg = "Unpacking failed for file %s" % str(e)
      my_logger.error(msg)
      my_logger.error(traceback.format_exc())
      return_code = 1
      if isJSON:
        json_dict = {}
        json_dict['state'] = "error"
        json_dict['component'] = p_app
        json_dict['msg'] = str(e)
        msg = json.dumps([json_dict])
        return_code = 0
      util.exit_message(msg, return_code)

    tar.close
    if isJSON:
      json_dict['msg'] = "Unpack complete."
      json_dict['status'] = "complete"
      print(json.dumps([json_dict]))
  else:
    msg = p_app + " is already installed."
    my_logger.info(msg)
    if isJSON:
      json_dict = {}
      json_dict['state'] = "install"
      json_dict['component'] = p_app
      json_dict['status'] = "complete"
      json_dict['msg'] = msg
      msg = json.dumps([json_dict])
    print(msg)
    return 1


## Upgrade Component ######################################################
def upgrade_component(p_comp):
  present_version = get_version(p_comp)
  if not present_version:
    return
  present_state   = util.get_comp_state(p_comp)
  server_port     = util.get_comp_port(p_comp)
  try:
    c = connL.cursor()

    sql = "SELECT version, platform FROM versions " + \
          " WHERE component = '" + p_comp + "' \n" + \
          "   AND " + util.like_pf("platform") + " \n" + \
          "   AND is_current = 1"
    c.execute(sql)
    row = c.fetchone()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "upgrade_component()")

  if str(row) == 'None':
    return

  update_version = str(row[0])
  platform = str(row[1])
  if platform > "":
    platform = util.get_pf()

  is_update_available=0
  cv = Version.coerce(update_version)
  iv = Version.coerce(present_version)
  if cv>iv:
    is_update_available=1

  if is_update_available==0:
    return 1

  if present_state == "NotInstalled":
    update_component_version(p_comp, update_version)
    return 0

  server_running = False
  if server_port > "1":
    server_running = util.is_socket_busy(int(server_port), p_comp)

  if server_running:
    run_script(p_comp, "stop-" + p_comp, "stop")

  msg = "upgrading " + p_comp + " from (" + present_version + ") to (" + update_version + ")"
  my_logger.info(msg)
  if isJSON:
    print('[{"state":"update","status":"start","component":"' + p_comp + '","msg":"'+msg+'"}]')
  else:
    if not isSilent:
      print(msg)

  components_stopped = []
  dependent_components = get_dependent_components(p_comp)
  isExt = is_extension(p_comp)
  if isExt:
    parent = util.get_parent_component(p_comp, 0)
    dependent_components.append([parent])
  if not p_comp == 'hub':
    for dc in dependent_components:
      d_comp = str(dc[0])
      d_comp_present_state   = util.get_comp_state(d_comp)
      d_comp_server_port     = util.get_comp_port(d_comp)
      d_comp_server_running = False
      if d_comp_server_port > "1":
        d_comp_server_running = util.is_socket_busy(int(d_comp_server_port), p_comp)
      if d_comp_server_running:
        my_logger.info("Stopping the " + d_comp + " to upgrade the " + p_comp)
        run_script(d_comp, "stop-" + d_comp, "stop")
        components_stopped.append(d_comp)

  rc = unpack_comp(p_comp, present_version, update_version)
  if rc == 0:
    update_component_version(p_comp, update_version)
    run_script(p_comp, "update-" + p_comp, "update")
    if isJSON:
      msg = "updated " + p_comp + " from (" + present_version + ") to (" + update_version + ")"
      print('[{"status": "complete", "state": "update", "component": "' + p_comp + '","msg":"' + msg + '"}]')

  if server_running:
    run_script(p_comp, "start-" + p_comp, "start")

  for dc in components_stopped:
    my_logger.info("Starting the " + dc + " after upgrading the " + p_comp)
    run_script(dc, "start-" + dc, "start")

  return 0


def unpack_comp(p_app, p_old_ver, p_new_ver):
  state = util.get_comp_state(p_app)

  base_name = p_app + "-" + get_latest_ver_plat(p_app, p_new_ver)

  file = base_name + ".tar.bz2"
  bz2_file = os.path.join(PGC_HOME, 'conf', 'cache', file)

  if os.path.exists(bz2_file) and is_downloaded(base_name, p_app):
    msg = "File is already downloaded."
    my_logger.info(msg)
    if isJSON:
      json_dict = {}
      json_dict['state'] = "download"
      json_dict['component'] = p_app
      json_dict['status'] = "complete"
      json_dict['file'] = file
      msg = json.dumps([json_dict])
    print(msg)
  elif not retrieve_comp(base_name, p_app):
    return 1

  msg = " Unpacking " + p_app + "(" + p_new_ver + ") over (" + p_old_ver + ")"
  my_logger.info(msg)

  file = base_name + ".tar.bz2"

  if isJSON:
    print('[{"state":"unpack","status":"start","component":"' + p_comp + '","msg":"'+msg+'","file":"' + file + '"}]')
  else:
    if not isSilent:
      print(msg)

  return_value = 0

  tarFileObj = ProgressTarExtract("conf" + os.sep + "cache" + os.sep + file)
  tarFileObj.component_name = p_app
  tar = tarfile.open(fileobj=tarFileObj, mode="r:bz2")


  new_comp_dir = p_app + "_new"
  old_comp_dir = p_app + "_old"
  if p_app in ('hub'):
      new_comp_dir = p_app + "_update"
  try:
    tar.extractall(path=new_comp_dir)
  except KeyboardInterrupt as e:
    util.delete_dir(new_comp_dir)
    msg = "Unpacking cancelled for file %s" % file
    if isJSON:
      json_dict = {}
      json_dict['state'] = "unpack"
      json_dict['status'] = "cancelled"
      json_dict['component'] = p_app
      json_dict['msg'] = msg
      msg = json.dumps([json_dict])
    if not isSilent:
      print(msg)
    my_logger.error(msg)
    return 1
  except Exception as e:
    util.delete_dir(new_comp_dir)
    msg = "Unpacking failed for file %s" % str(e)
    if isJSON:
      json_dict = {}
      json_dict['state'] = "error"
      json_dict['component'] = p_app
      json_dict['msg'] = str(e)
      msg = json.dumps([json_dict])
    if not isSilent:
      print(msg)
    my_logger.error(msg)
    my_logger.error(traceback.format_exc())
    return 1

  tar.close

  isExt = is_extension(p_app)
  if isExt:
    try:
      parent = util.get_parent_component(p_app,0)
      my_logger.info("backing up the parent component %s " % parent)
      copytree(os.path.join(PGC_HOME, parent), os.path.join(backup_target_dir, parent))
      manifest_file_name = p_app + ".manifest"
      manifest_file_path = os.path.join(PGC_HOME, "conf", manifest_file_name)
      my_logger.info("backing up current manifest file " + manifest_file_path)
      copy2(manifest_file_path, backup_target_dir)
      my_logger.info("deleting existing extension files from " + parent)
      util.delete_extension_files(manifest_file_path,upgrade=True)
      my_logger.info("deleting existing manifest file : " + manifest_file_name )
      os.remove(manifest_file_path)
      my_logger.info("creating new manifest file : " + manifest_file_name)
      util.create_manifest(p_app, parent, upgrade=True)
      my_logger.info("copying new extension filess : " + manifest_file_name)
      util.copy_extension_files(p_app, parent, upgrade=True)
    except Exception as e:
      error_msg = "Error while upgrading the " + p_app + " : " + str(e)
      my_logger.error(error_msg)
      my_logger.error(traceback.format_exc())
      if isJSON:
        json_dict = {}
        json_dict['state'] = "error"
        json_dict['component'] = p_app
        json_dict['msg'] = str(e)
        error_msg = json.dumps([json_dict])
      if not isSilent:
        print(error_msg)
      return_value = 1
  else:
    try:
      if not os.path.exists(backup_dir):
        os.mkdir(backup_dir)
      if not os.path.exists(backup_target_dir):
        os.mkdir(backup_target_dir)
      my_logger.info("backing up the old version of %s " % p_app)
      copytree(os.path.join(PGC_HOME, p_app), os.path.join(backup_target_dir, p_app))
      msg = p_app + " upgrade staged for completion."
      my_logger.info(msg)
      if p_app in ('hub'):
        if util.get_platform() == "Windows":
          copy2(os.path.join(PGC_HOME, "pgc.bat"), backup_target_dir)
        else:
          copy2(os.path.join(PGC_HOME, "pgc"), backup_target_dir)
        os.rename(new_comp_dir, "hub_new")
        ## run the update_hub script in the _new directory
        upd_hub_cmd = "python hub_new" + os.sep + "hub" + os.sep + "scripts" + os.sep + "update_hub.py "
        os.system(upd_hub_cmd + p_old_ver + " " + p_new_ver)
      else:
        my_logger.info("renaming the existing folder %s" % p_app)
        os.rename(p_app, p_app+"_old")
        my_logger.info("copying the new files to folder %s" % p_app)
        copytree(os.path.join(PGC_HOME, new_comp_dir, p_app), os.path.join(PGC_HOME, p_app))
        my_logger.info("Restoring the conf and extension files if any")
        util.restore_conf_ext_files(os.path.join(PGC_HOME, p_app+"_old"), os.path.join(PGC_HOME, p_app))
        my_logger.info(p_app + " upgrade completed.")
    except Exception as upgrade_exception:
      error_msg = "Error while upgrading the " + p_app + " : " + str(upgrade_exception)
      my_logger.error(error_msg)
      my_logger.error(traceback.format_exc())
      if isJSON:
        json_dict = {}
        json_dict['state'] = "error"
        json_dict['component'] = p_app
        json_dict['msg'] = str(upgrade_exception)
        error_msg = json.dumps([json_dict])
      if not isSilent:
        print(error_msg)
      return_value = 1

  if os.path.exists(os.path.join(PGC_HOME, new_comp_dir)):
    util.delete_dir(os.path.join(PGC_HOME, new_comp_dir))
  if os.path.exists(os.path.join(PGC_HOME, old_comp_dir)):
    util.delete_dir(os.path.join(PGC_HOME, old_comp_dir))

  return return_value

def update_component_version(p_app, p_version):
  try:
    c = connL.cursor()
    update_date=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sql = "UPDATE components SET version = ?,install_dt = ? WHERE component = ?"
    c.execute(sql, [p_version,update_date, p_app])
    connL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"update_component_version()")

  return


## Delete Component #######################################################
def remove_comp(p_comp):
  msg = "Removing " + p_comp
  my_logger.info(msg)
  if isJSON:
    msg = '[{"status":"wip","msg":"'+ msg + '","component":"' + p_comp + '"}]'
  print(msg)
  if os.path.isdir(p_comp):
    script_name = "remove-" + p_comp
    run_script(c, script_name, "")
    util.delete_dir(p_comp)
  if is_extension(p_comp):
    manifest_file_name = p_comp + ".manifest"
    manifest_file_path = os.path.join(PGC_HOME, "conf", manifest_file_name)
    util.delete_extension_files(manifest_file_path)
    my_logger.info("deleted manifest file : " + manifest_file_name )
    os.remove(manifest_file_path)
  return 0


## List component dependencies recursively ###############################
def list_depend_recur(p_app):
  for i in dep9:
    if i[0] == p_app:
       if i[1] not in my_depend and is_dependent_platform(i[1]):
         my_depend.append(i[1])
         list_depend_recur(i[1])
  return my_depend


## Update component state ###############################################
def update_component_state(p_app, p_mode, p_ver=None):
  new_state = "Disabled"
  if p_mode  == "enable":
    new_state = "Enabled"
  elif p_mode == "install":
    new_state = "Enabled"
  elif p_mode == "remove":
    new_state = "NotInstalled"

  current_state = util.get_comp_state(p_app)
  ver = ""

  if current_state == new_state:
    return

  if p_mode == "disable" or p_mode == "remove":
    run_script(p_app, "stop-"  + p_app, "kill")

  try:
    c = connL.cursor()

    if p_mode in ('enable', 'disable'):
      ver = get_version(p_app)
      sql = "UPDATE components SET status = ? WHERE component = ?"
      c.execute(sql, [new_state, p_app])

    if p_mode == 'remove':
      ver = get_version(p_app)
      sql = "DELETE FROM components WHERE component = ?"
      c.execute(sql, [p_app])

    if p_mode == 'install':
      sql = "INSERT INTO components (component, project, version, platform, port, status) " + \
            "SELECT v.component, r.project, v.version, " +\
            " CASE WHEN v.platform='' THEN '' ELSE '"+ util.get_pf() +"' END, p.port, 'Enabled' " + \
            "  FROM versions v, releases r, projects p " + \
            " WHERE v.component = ? " + \
            "   AND v.component = r.component " + \
            "   AND r.project = p.project "
      if p_ver:
        sql += " AND v.version = ? "
        c.execute(sql, [p_app, p_ver])
      else:
        sql += " AND v.is_current = 1 "
        c.execute(sql, [p_app])
      ver = get_version(p_app)

    connL.commit()
    c.close()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"update_component_state()")

  msg = p_app + ' ' + new_state
  my_logger.info(msg)
  if isJSON:
    msg = '[{"status":"wip","msg":"'+ msg + '"}]'

  return


## Check component state & status ##########################################
def check_comp(p_comp, p_port, p_kount, check_status=False):
  ver = get_ver_plat(p_comp)
  app_state = util.get_comp_state(p_comp)

  if (app_state in ("Disabled", "NotInstalled")):
    api.status(isJSON, p_comp, ver, app_state, p_port, p_kount)
    return

  if ((p_port == "0") or (p_port == "1")):
    api.status(isJSON, p_comp, ver, "Installed", "", p_kount)
    return

  is_pg = util.is_postgres(p_comp)
  if is_pg or p_comp in ("devops"):
    if is_pg:
      util.read_env_file(p_comp)
    app_datadir = util.get_comp_datadir(p_comp)
    if app_datadir == "":
      if check_status:
        return "NotInitialized"
      api.status(isJSON, p_comp, ver, "Not Initialized", "", p_kount)
      return

  if util.is_socket_busy(int(p_port), p_comp):
    status = "Running"
    if check_status:
        return status
    api.status(isJSON, p_comp, ver, status, p_port, p_kount)
  else:
    if check_status:
        return "Stopped"
    api.status(isJSON, p_comp, ver, "Stopped", p_port, p_kount)

  return;


## Check component state #################################################
def check_status(p_comp, p_mode):
  if p_comp in ['all', '*']:
    try:
      c = connL.cursor()
      sql = "SELECT component, port FROM components"
      c.execute(sql)
      data = c.fetchall()
      kount = 0
      if isJSON:
        print("[")
      for row in data:
        comp = row[0]
        port = row[1]
        if (port > 1) or (p_mode == 'list'):
          kount = kount + 1
          check_comp(comp, str(port), kount)
      if isJSON:
        print("]")
    except sqlite3.Error as e:
      fatal_sql_error(e,sql,"check_status()")
  else:
    port = util.get_comp_port(p_comp)
    check_comp(p_comp, port,0)
  return;


def retrieve_remote():
  if not os.path.exists(backup_dir):
    os.mkdir(backup_dir)
  if not os.path.exists(backup_target_dir):
    os.mkdir(backup_target_dir)
  copy2(os.path.join(PGC_HOME, 'conf', 'pgc_local.db'), backup_target_dir)
  copy2(os.path.join(PGC_HOME, 'conf', 'versions.sql'), backup_target_dir)
  remote_file = util.get_versions_sql()
  msg = "Retrieving the remote list of latest component versions (" + remote_file + ") ..."
  my_logger.info(msg)
  if isJSON:
    print('[{"status":"wip","msg":"'+msg+'"}]')
    msg=""
  else:
    if not isSilent:
      print(msg)
  if not util.http_get_file(isJSON, remote_file, REPO, "conf", False, msg):
    exit_cleanly(1)
  msg=""

  sql_file = "conf" + os.sep + remote_file
  if remote_file == "versions.sql":
    if not util.http_get_file(isJSON, remote_file + ".sha512", REPO, "conf", False, msg):
      exit_cleanly(1)
    msg = "Validating checksum file..."
    my_logger.info(msg)
    if isJSON:
      print('[{"status":"wip","msg":"'+msg+'"}]')
    else:
      if not isSilent:
        print(msg)
    if not validate_checksum(sql_file, sql_file + ".sha512"):
      exit_cleanly(1)
  msg = "Updating local repository with remote entries..."
  my_logger.info(msg)
  if isJSON:
    print('[{"status":"wip","msg":"'+msg+'"}]')
  else:
    if not isSilent:
      print(msg)
  if not util.process_sql_file(sql_file, isJSON):
    exit_cleanly(1)



## Download tarball component and verify against checksum ###############
def retrieve_comp(p_base_name, component_name=None):
  conf_cache = "conf" + os.sep + "cache"
  bz2_file = p_base_name + ".tar.bz2"
  checksum_file = bz2_file + ".sha512"
  global download_count
  download_count += 1

  msg = "Get:" + str(download_count) + " " + REPO + " " + p_base_name
  my_logger.info(msg)
  display_status = True
  if isSilent:
    display_status = False
  if not util.http_get_file(isJSON, bz2_file, REPO, conf_cache, display_status, msg, component_name):
    return (False)

  msg = "Preparing to unpack " + p_base_name
  if not util.http_get_file(isJSON, checksum_file, REPO, conf_cache, False, msg, component_name):
    return (False)

  return validate_checksum(conf_cache + os.sep + bz2_file, conf_cache + os.sep + checksum_file)


def validate_checksum(p_file_name, p_checksum_file_name):
  checksum_from_file = util.get_file_checksum(p_file_name)
  checksum_from_remote_file = util.read_file_string(p_checksum_file_name).rstrip()
  checksum_from_remote = checksum_from_remote_file.split()[0]
  global check_sum_match
  check_sum_match = False
  if checksum_from_remote == checksum_from_file:
      check_sum_match = True
      return check_sum_match
  util.print_error("SHA512 CheckSum Mismatch" )
  return check_sum_match


def get_component_list():
  try:
    c = connL.cursor()
    sql = "SELECT component FROM components"
    c.execute(sql)
    t_comp = c.fetchall()
    r_comp = []
    for comp in t_comp:
      r_comp.append(str(comp[0]))
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_component_list()")
  return r_comp;


def get_installed_extensions_list(parent_c):
  try:
    c = connL.cursor()
    sql = "SELECT c.component FROM versions v ,components c " + \
          "WHERE v.component = c.component AND v.parent='" + parent_c + "'"
    c.execute(sql)
    t_comp = c.fetchall()
    r_comp = []
    for comp in t_comp:
      r_comp.append(str(comp[0]))
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_installed_extensions_list()")
  return r_comp;


def is_extension(ext_comp):
  try:
    c = connL.cursor()
    sql = "SELECT c.component,c.project,p.category " + \
          "  FROM projects p,components c " + \
          " WHERE c.component='" + ext_comp + "' " + \
          "   AND c.project=p.project " + \
          "   AND p.category=2"
    c.execute(sql)
    data = c.fetchone()
    if not data:
      return False
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"is_extension()")
  return True


def get_available_component_list():
  try:
    c = connL.cursor()
    sql = "SELECT v.component FROM versions v WHERE v.is_current = 1 \n" + \
          "   AND " + util.like_pf("v.platform")
    c.execute(sql)
    t_comp = c.fetchall()
    r_comp = []
    for comp in t_comp:
      r_comp.append(str(comp[0]))
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_available_component_list()")
  return  r_comp


def get_all_components_list(p_component=None, p_version=None, p_platform=None):
  try:
    c = connL.cursor()
    sql = "SELECT v.component, v.version, v.platform" + \
          "  FROM versions v "
    if p_version is None:
      sql = sql + " WHERE v.is_current = 1 "
    elif p_version=="all":
      sql = sql + " WHERE v.is_current >= 0 "

    if (p_platform is None):
      sql = sql + " AND " + util.like_pf("v.platform") + " "
    if p_component:
      sql = sql + " AND v.component = '" + p_component + "'"
    if p_version and p_version!="all":
      sql = sql + " AND v.version = '" + p_version + "'"

    c.execute(sql)
    t_comp = c.fetchall()
    r_comp = []
    for comp in t_comp:
      if p_platform=="all":
        if comp[2]:
          platforms = comp[2].split(',')
          for p in platforms:
            comp_dict = {}
            comp_dict['component']= str(comp[0])
            version = str(comp[1]) + "-" + p.strip()
            comp_dict['version']= version
            r_comp.append(comp_dict)
        else:
          comp_dict = {}
          comp_dict['component']= str(comp[0])
          version = str(comp[1])
          if comp[2]:
            if p_platform is None:
              version = str(comp[1]) + "-" + util.get_pf()
            else:
              version = str(comp[1]) + "-" + p_platform
          comp_dict['version']= version
          r_comp.append(comp_dict)
      else:
        comp_dict = {}
        comp_dict['component']= str(comp[0])
        version = str(comp[1])
        if comp[2]:
          if p_platform is None:
            version = str(comp[1]) + "-" + util.get_pf()
          else:
            version = str(comp[1]) + "-" + p_platform
        comp_dict['version']= version
        r_comp.append(comp_dict)
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"get_all_components_list()")
  return  r_comp



def get_list():
  r_sup_plat = util.like_pf("r.sup_plat")

  if isOLD:
    exclude_comp = ""
  else:
    exclude_comp = " AND v.component NOT IN (SELECT component FROM components)"

  parent_comp_condition = ""
  installed_category_conditions = " AND p.category > 0 "
  available_category_conditions = " AND p.category <> 2 "
  ext_component = ""

  if isExtensions:
    installed_category_conditions = " AND p.category = 2 "
    available_category_conditions = " AND p.category = 2 "
    if p_comp != "all":
      ext_component = " AND parent = '" + p_comp + "' "



  installed = \
    "SELECT p.category, g.description as category_desc, c.component, c.version, c.port, c.status, r.stage, \n" + \
    "       coalesce((select is_current from versions where c.component = component AND c.version = version),0), \n" + \
    "       c.datadir, p.short_desc, \n" + \
    "       coalesce((select parent from versions where c.component = component and c.version = version),'') as parent, \n" + \
    "       coalesce((select release_date from versions where c.component = component and c.version = version),'20160101'), \n" + \
    "       c.install_dt \n" + \
    "  FROM components c, releases r, projects p, categories g \n" + \
    " WHERE c.component = r.component AND r.project = p.project \n" + \
    "   AND p.category = g.category \n"  + \
    "   AND " + r_sup_plat + installed_category_conditions + ext_component


  available = \
    "SELECT c.category, c.description, v.component, v.version, 0, 'NotInstalled', \n" + \
    "       r.stage, v.is_current, '', p.short_desc, v.parent as parent, v.release_date, '' \n" + \
    "  FROM versions v, releases r, projects p, categories c \n" + \
    " WHERE v.component = r.component AND r.project = p.project \n" + \
    "   AND p.category = c.category \n" + \
    "   AND " + util.like_pf("v.platform") + " \n" + \
    "   AND " + r_sup_plat + exclude_comp + available_category_conditions + ext_component

  extensions = \
    "SELECT c.category, c.description, v.component, v.version, 0, 'NotInstalled', \n" + \
    "       r.stage, v.is_current, '', p.short_desc, v.parent as parent, v.release_date, '' \n" + \
    "  FROM versions v, releases r, projects p, categories c \n" + \
    " WHERE v.component = r.component AND r.project = p.project \n" + \
    "   AND p.category = 2 AND p.category = c.category \n" + \
    "   AND " + util.like_pf("v.platform") + " \n" + \
    "   AND v.parent in (select component from components) AND " + r_sup_plat + exclude_comp


  if isExtensions:
    sql = installed + "\n UNION \n" + available + "\n ORDER BY 1, 3, 4, 6"
  else:
    sql = installed + "\n UNION \n" + available + "\n UNION \n" + extensions + "\n ORDER BY 1, 3, 4, 6"

  try:
    c = connL.cursor()
    c.execute(sql)
    data = c.fetchall()

    headers = ['Category',      'Component', 'Version', 'Stage', 'ReleaseDt',    'Status',
           'Cur?',       'Updates']
    keys    = ['category_desc', 'component', 'version', 'stage', 'release_date', 'status',
               'is_current', 'current_version']

    jsonList = []
    kount = 0
    previous_version = None
    previous_comp = None
    for row in data:
      compDict = {}
      kount = kount + 1

      category = str(row[0])
      category_desc = str(row[1])
      comp = str(row[2])
      version = str(row[3])
      port = str(row[4])

      if previous_comp and previous_version:
        if previous_comp == comp and previous_version == version:
          continue

      previous_version = version
      previous_comp = comp

      if str(row[5]) == "Enabled":
        status = "Installed"
      else:
        status = str(row[5])
      if status == "NotInstalled" and isJSON == False:
        status = ""

      stage = str(row[6])
      if stage == "prod" and isJSON == False:
        stage = ""
      if stage == "test" and status in ("", "NotInstalled"):
        if not isTEST:
          continue

      is_current = str(row[7])
      if is_current == "0" and status in ("", "NotInstalled"):
        if not isOLD:
          continue

      current_version = get_current_version(comp)
      is_update_available = 0
      cv = Version.coerce(current_version)
      iv = Version.coerce(version)
      if cv>iv:
        is_update_available = 1


      if is_update_available==0:
        updates = 0
        current_version = ""
      else:
        updates = 1

      if (port == "0") or (port == "1"):
        port = ""

      datadir = row[8]
      if row[8] is None:
        datadir = ""
      else:
        datadir = str(row[8]).strip()

      short_desc = row[9]

      parent = row[10]

      release_date = '1970-01-01'
      rel_dt = str(row[11])
      if len(rel_dt) == 8:
        release_date = rel_dt[0:4] + "-" + rel_dt[4:6] + "-" + rel_dt[6:8]

      compDict['is_new'] = 0

      try:
        rd = datetime.datetime.strptime(release_date, '%Y-%m-%d')
        today_date = datetime.datetime.today()
        date_diff = (today_date - rd).days

        if date_diff <= 30:
          compDict['is_new'] = 1
        if show_latest and date_diff > 30:
          continue
      except Exception as e:
        pass

      if util.is_postgres(comp) or comp in ("devops"):
        if port > "" and status == "Installed" and datadir == "":
          status = "NotInitialized"
          port = ""

      ins_date = str(row[12])
      install_date=""
      compDict['is_updated'] = 0
      if ins_date:
        install_date = ins_date[0:4] + "-" + ins_date[5:7] + "-" + ins_date[8:10]

        try:
          insDate = datetime.datetime.strptime(install_date, '%Y-%m-%d')
          today_date = datetime.datetime.today()
          date_diff = (today_date - insDate).days
          if date_diff <= 30:
            compDict['is_updated'] = 1
        except Exception as e:
          pass


      compDict['category'] = category
      compDict['category_desc'] = category_desc
      compDict['component'] = comp
      compDict['version'] = version
      compDict['short_desc'] = short_desc
      compDict['port'] = port
      compDict['release_date'] = release_date
      compDict['install_date'] = install_date
      compDict['status'] = status
      compDict['stage'] = stage
      compDict['updates'] = updates
      compDict['is_current'] = is_current
      compDict['current_version'] = current_version
      compDict['parent'] = parent
      jsonList.append(compDict)

    if isJSON:
      print(json.dumps(jsonList, sort_keys=True, indent=2))
    else:
      if show_latest:
        print("New components released in the last 30 days.")
      print(api.format_data_to_table(jsonList, keys, headers))

  except sqlite3.Error as e:
    fatal_sql_error(e, sql, "LIST")
  exit_cleanly(0)


def is_component(p_comp):
  if p_comp in ['all', '*']:
    return True
  for comp in dep9:
    if comp[0] == p_comp:
      return True
  return False;


#############################################################################
# expand the prefix for a component's version number into the full version
#  number for the most recent version that matches
#############################################################################
def wildcard_version(p_comp, p_ver):
  try:
    ## for an exact match then don't try the wildcard
    sql = "SELECT count(*) FROM versions WHERE component = ? AND version = ?"
    c = connL.cursor()
    c.execute(sql,[p_comp, p_ver])
    data = c.fetchone()
    if data[0] == 1:
      ## return the parm that was passed into this function
      return p_ver

    sql = "SELECT release_date, version FROM versions \n" + \
          " WHERE component = ? AND version LIKE ? \n" +\
          "ORDER BY 1 DESC"
    c = connL.cursor()
    c.execute(sql,[p_comp, p_ver + "%"])
    data = c.fetchone()
    if data is None:
      ## return the parm that was passed into this function
      return p_ver

  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"wildcard_version")

  ## return the full version number from the sql statement
  return (str(data[1]))


#############################################################################
# If the prefix for a component uniquely matches only one component, then
#  expand the prefix into the full component name
#############################################################################
def wildcard_component(p_comp):
  comp = check_release("%" + p_comp + "%")
  if comp > "":
    return comp

  ## check if only a single version of PG is installed ###
  pg_ver = ""
  data = []
  sql = "SELECT component FROM components" + \
        " WHERE component >= 'pg92' AND component <= 'pg96'"
  try:
    c = connL.cursor()
    c.execute(sql)
    data = c.fetchall()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"wildcard_component")
  if len(data) == 1:
    for comp in data:
      pg_ver = str(comp[0])
  else:
    return p_comp

  ## if only single version of PG installed, see if we match with that suffix
  comp = check_release("%" + p_comp + "%-" + pg_ver)
  if comp > "":
    return comp

  return p_comp


def check_release(p_wild):
  data = []
  sql = "SELECT component FROM releases WHERE component LIKE '" + p_wild + "'"
  try:
    c = connL.cursor()
    c.execute(sql)
    data = c.fetchall()
  except sqlite3.Error as e:
    fatal_sql_error(e,sql,"check-release")
  ret = ""
  if len(data) == 1:
    for comp in data:
      ret = str(comp[0])
  return (ret)


def is_dbstat(p_stat):
  if p_stat in available_dbstats:
    return True
  return False


def get_comp_display():
  comp_display = "("
  for comp in installed_comp_list:
    if not comp_display == "(":
      comp_display += ", "
    comp_display += comp
  comp_display += ")"
  return(comp_display)


def get_mode_display():
  mode_display = "("
  for mode in mode_list:
    if not mode_display == "(":
      mode_display += ", "
    mode_display += mode
  mode_display += ")"
  return(mode_display)


def get_help_text():
  helpf = "README.md"
  helpfile = os.path.dirname(os.path.realpath(__file__)) + "/../doc/" + helpf
  s  = util.read_file_string(helpfile)

  ## filter out the awkward markdown lines
  lines = s.split('\n')
  new_s = ""
  for line in lines:
    if line not in ["```", "#!"]:
      new_s = new_s + line + '\n'
  return(new_s)


def is_valid_mode(p_mode):
  if p_mode in mode_list:
    return True
  if p_mode in mode_list_advanced:
    return True
  return False


def fatal_sql_error(err,sql,func):
  print("################################################")
  print("# FATAL SQL Error in " + func)
  print("#    SQL Message =  " + err.args[0])
  print("#  SQL Statement = " + sql)
  print("################################################")
  exit_cleanly(1)


def exit_cleanly(p_rc):
  try:
    connL.close()
  except sqlite3.Error as e:
    pass
  sys.exit(p_rc)


def pgc_lock():
  try:
    fd = os.open(pid_file, os.O_RDONLY)
    pgc_pid = os.read(fd,12)
    os.close(fd)
  except IOError as e:
    return False
  except OSError as e:
    return False
  if not pgc_pid:
    return False
  if util.get_platform() == "Windows":
    try:
      ps = subprocess.Popen('tasklist.exe /NH /FI "PID eq %s"' % pgc_pid, shell=True, stdout=subprocess.PIPE)
      output = ps.stdout.read()
      ps.stdout.close()
      ps.wait()
      if pgc_pid in output:
        return True
    except Exception as e:
      my_logger.error("Error while checking for lock with command " + p_mode + " : " + str(e))
      my_logger.error(traceback.format_exc())
      return False
  else:
    try:
      os.kill(int(pgc_pid), 0)
    except OSError as e:
      return False
    else:
      return True
  return False


####################################################################
########                    MAINLINE                      ##########
####################################################################

## Initialize Globals ##############################################
REPO=util.get_value('GLOBAL', 'REPO')
PGC_HOME=os.getenv('PGC_HOME')
local_time = time.strftime("%Y-%m-%d %H:%M:%S %Z")

os.chdir(PGC_HOME)

db_local = "conf" + os.sep + "pgc_local.db"
connL = sqlite3.connect(db_local)

## eliminate empty parameters #################
args = sys.argv
while True:
  try:
     args.remove("")
  except:
     break

## validate inputs ###########################################
if len(args) == 1:
  api.info(False, PGC_HOME, REPO)
  print(" ")
  print(get_help_text())
  exit_cleanly(0)

if ((args[1] == "--version") or (args[1] == "-v")):
  api.info(False, PGC_HOME, REPO)
  exit_cleanly(0)

p_mode = ""
p_comp = "all"
installed_comp_list = get_component_list()
available_comp_list = get_available_component_list()
download_count = 0

if ((args[1] == "help") or (args[1] == "--help")):
  print(get_help_text())
  exit_cleanly(0)

show_latest=False

## process global parameters #################
p_host=""
p_home=""
p_user=""
p_passwd=""
for i in range(0, len(args) - 1):
  if args[i] == "--host":
    p_host = args[i+1]
    args.remove("--host")
    args.remove(p_host)
    [p_home, p_user, p_passwd] = util.get_pgc_host(p_host)
    if p_home == "":
      util.exit_message("host server not defined", 1)

isJSON = False
if "--json" in args:
  isJSON = True
  args.remove("--json")
  os.environ['isJson'] = "True"

isTEST = False
if "--test" in args:
  isTEST = True
  args.remove("--test")
else:
  if util.get_stage() == "test":
    isTEST = True

isOLD = False
if "--old" in args:
  isOLD = True
  args.remove("--old")

isAUTOSTART = False
if "--autostart" in args and 'install' in args:
  isAUTOSTART = True
  args.remove("--autostart")

isRELNOTES = False
if "--relnotes" in args and 'info' in args:
  isRELNOTES = True
  args.remove("--relnotes")

isSilent = False
if "--silent" in args:
  isSilent = True
  os.environ['isSilent'] = "True"
  args.remove("--silent")

isExtensions = False
if "--extensions" in args:
  isExtensions = True
  args.remove("--extensions")

isLIST = False
if "--list" in args:
  isLIST = True
  args.remove("--list")

if len(args) == 1:
  util.exit_message("Nothing to do", 0)

arg = 1

p_mode = args[1]
if not is_valid_mode(p_mode):
  util.exit_message("Invalid option or command", 1)


if p_mode in lock_commands:
  if pgc_lock():
    msg = "Unable to execute '{0}', another pgc instance may be running. \n" \
          "HINT: Delete the lock file: '{1}' if no other instance is running.".format(p_mode, pid_file)
    if isJSON:
      msg = '[{"state":"locked","msg":"' + msg + '"}]'
    util.exit_message(msg, 0)
  pgc_pid_fd = open(pid_file, 'w')
  pgc_pid_fd.write(str(os.getpid()))
  pgc_pid_fd.close()


p_comp_list=[]
p_dbstat_list=[]
extra_args=""
p_version=""
requested_p_version=""
info_arg=0
try:
  for i in range((arg + 1), len(args)):
    if p_host > "":
      break
    if p_mode=="update":
      util.print_error("No additional parameters allowed.")
      exit_cleanly(1)
    comp1 = wildcard_component(args[i])
    if is_component(comp1):
      p_comp_list.append(comp1)
      if( p_mode == "info" and args[i]== "all"):
        info_arg=1
        p_version = "all"
    elif is_dbstat(args[i]):
      p_dbstat_list.append(args[i])
      if ( p_mode == 'dbstat' and len(p_dbstat_list) != 1):
        util.exit_message("Only one dbstat allowed per run", 1)
    else:
      if((p_mode == "config" or p_mode == "init") and (len(p_comp_list) == 1)):
        if str(args[i]) > '':
          extra_args = extra_args + '"' + str(args[i]) + '" '
      elif( p_mode in ("info", "download", "install", "update") and len(p_comp_list) == 1 and info_arg == 0 ):
        if p_mode == "info":
          p_version = args[i]
        else:
          ver1 = wildcard_version(p_comp_list[0], args[i])
          p_version = get_platform_specific_version(p_comp_list[0], ver1)
          if p_version == "-1":
            util.print_error("Invalid component version parameter  (" + ver1 + ")")
            exit_cleanly(1)
          requested_p_version=ver1
        info_arg = 1
      elif (p_mode in ("get", "set", "unset", "register", "unregister")):
        pass
      else:
        util.print_error("Invalid component parameter (" + args[i] + ")")
        exit_cleanly(1)

  if p_mode not in no_log_commands:
    my_logger.setLevel(COMMAND)
    my_logger.log(COMMAND,"pgc %s "," ".join(args[1:]))

  if len(p_comp_list) == 0:
    if p_mode == "download":
      util.print_error("No component parameter specified.")
      exit_cleanly(1)
    p_comp_list.append('all')

  if len(p_comp_list) >= 1:
    p_comp = p_comp_list[0]



  ## REGISTER & UNREGISTER #####################################################################
  if (p_mode in ('register', 'unregister')):
    bad_reg_msg = "try: pgc " + p_mode + " [ HOST | PG ] 'host[:pgc_home:user:passwd'] [--list]"

    bad_reg_msg = "try: pgc " + p_mode + " [ HOST | PG | GROUP] [host | group] [pgc_home user passwd [name] [group]] [--list]"

    if isLIST:
      if args[2]=="HOST":
        ## ignore the other parms (for now)
        util.list_registrations(isJSON)
      elif args[2]=="GROUP":
        util.list_groups(isJSON)
      exit_cleanly(0)

    args_len = len(args)
    if args[2]=="HOST":
      if p_mode == 'register':
        if args_len<7:
          print("ERROR: must be exactly 4 parms")
          util.exit_message(bad_reg_msg, 1)

        if args_len>9:
          print("ERROR: Register command accepts max 6 parms")
          util.exit_message(bad_reg_msg, 1)
      else:
        if args_len!=4:
          print("ERROR: must be exactly 4 parms")
          util.exit_message(bad_reg_msg, 1)
    elif args[2]=="GROUP":
      if args_len!=4:
        print("ERROR: must be exactly 4 parms")
        util.exit_message(bad_reg_msg, 1)


    if args[2] not in ('HOST', 'PG','GROUP'):
      print("ERROR: first parm must be HOST or PG or GROUP")
      util.exit_message(bad_reg_msg, 1)

    host_array=args[2:]

    if p_mode == 'register':
      rc=0
      if args[2]=="HOST":
        if util.check_remote_host(host_array,isJSON):
          rc = util.register(host_array,isJson=isJSON)
      elif args[2]=="GROUP":
        rc=util.register_group(host_array[1],isJson=isJSON)
    else:
      if args[2]=="HOST":
        rc = util.unregister(host_array,isJson=isJSON)
      elif args[2]=="GROUP":
        rc=util.unregister_group(host_array[1],isJson=isJSON)

    exit_cleanly(rc)


  ## SSH #######################################################################################
  if p_host > "":
      cmd = " ".join(args[1:])
      exit_cleanly(util.run_pgc_ssh(p_host, cmd, isJSON))


  ## TOP ######################################################################################
  if p_mode == 'top':
    try:
      api.top(display=False)
      if isJSON:
        time.sleep(0.5)
        api.top(display=True, isJson=isJSON)
        exit_cleanly(0)
      while True:
        api.top(display=True)
        time.sleep(1)
    except KeyboardInterrupt as e:
      pass
    exit_cleanly(0)

  ## INFO ######################################################################################
  if (p_mode == 'info'):
    if(p_comp=="all" and info_arg==0):
      api.info(isJSON, PGC_HOME, REPO)
    else:
      try:
        c = connL.cursor()
        datadir = ""
        logdir = ""
        svcname = ""
        port = 0
        is_installed = 0
        autostart = ""
        version = ""
        install_dt = ""
        if p_comp != "all":
          sql = "SELECT coalesce(datadir,''), coalesce(logdir,''), coalesce(svcname,''), port, autostart, \n" \
                "       version, install_dt " + \
                "  FROM components WHERE component = '" + p_comp + "'"
          c.execute(sql)
          data = c.fetchone()
          if not data is None:
            is_installed = 1
            datadir = str(data[0])
            logdir = str(data[1])
            svcname = str(data[2])
            port = int(data[3])
            autostart = str(data[4])
            version = str(data[5])
            install_dt = str(data[6])

        sql = "SELECT c.category, c.description, p.project, r.component, v.version, v.platform, \n" + \
              "       p.homepage_url, r.doc_url, v.is_current, \n" + \
              "       " + str(is_installed) + " as is_installed, r.stage, \n" + \
              "       r.sup_plat, v.release_date, p.short_desc \n" + \
              "  FROM projects p, releases r, versions v, categories c \n" + \
              " WHERE r.project = p.project AND v.component = r.component \n" + \
              "   AND " + util.like_pf("v.platform") + " \n" + \
              "   AND p.category = c.category"

        if(p_comp!="all"):
          sql = sql + " AND r.component = '" + p_comp + "'"

        if (p_version != "" and p_version !="all"):
          sql = sql + " and v.version = '" + p_version + "'"

        sql = sql + " ORDER BY is_installed, c.category, p.project, r.component desc, v.version desc "

        if(p_version==""):
          sql = sql + " limit 1"

        c.execute(sql)
        data = c.fetchall()

        compJson = []
        kount = 0
        for row in data:
          kount = kount + 1
          cat = row[0]
          cat_desc = row[1]
          proj = row[2]
          comp = row[3]
          ver = row[4]
          plat = row[5]
          home_url = row[6]
          doc_url = row[7]
          is_current = row[8]
          is_installed = row[9]
          stage = row[10]
          sup_plat = row[11]
          rel_dt = str(row[12])
          short_desc=row[13]
          if len(rel_dt) == 8:
            release_date = rel_dt[:4] + '-' + rel_dt[4:6] + '-' + rel_dt[6:]
          else:
            release_date = rel_dt
          if len(install_dt) == 8:
            install_date = install_dt[:4] + '-' + install_dt[4:6] + '-' + install_dt[6:]
          else:
            install_date = install_dt
          compDict = {}
          compDict['category']=cat
          compDict['project']=proj
          compDict['component']=comp
          compDict['platform']=plat
          compDict['home_url']=home_url
          compDict['doc_url']=doc_url
          compDict['is_installed']=is_installed
          compDict['short_desc']=short_desc
          current_version = get_current_version(comp)
          current_version = get_current_version(comp)
          is_current = 0
          compDict['version'] = ver
          if is_installed == 1:
            compDict['version'] = version
            is_update_available = 0
            cv = Version.coerce(current_version)
            iv = Version.coerce(version)
            if cv>iv:
              is_update_available=1
            if current_version == version:
              is_current = 1
            elif is_update_available == 1:
              compDict['current_version'] = current_version
          compDict['is_current']=is_current
          compDict['stage']=stage
          compDict['sup_plat']=sup_plat
          compDict['release_date']=release_date

          compDict['is_new'] = 0

          try:
            rd = datetime.datetime.strptime(release_date, '%Y-%m-%d')
            today_date = datetime.datetime.today()
            date_diff = (today_date - rd).days

            if date_diff <= 30:
              compDict['is_new'] = 1
          except Exception as e:
            pass

          compDict['install_date']=install_date
          compDict['datadir'] = datadir
          compDict['logdir'] = logdir
          compDict['svcname'] = svcname
          compDict['port'] = port
          compDict['autostart'] = autostart
          if isRELNOTES:
            compDict['relnotes'] = util.get_relnotes(comp, p_version)
          else:
            compDict['relnotes'] = ""
          if is_installed == 1 and port > 0:
              is_running = check_comp(comp, port, 0, True)
              if is_running == "NotInitialized":
                compDict['port'] = 0
              compDict['status'] = is_running
              compDict['current_logfile'] = ""
              if util.is_postgres(p_comp) and is_running != "NotInitialized":
                current_logfile = util.find_most_recent(logdir, "postgresql")
                if current_logfile:
                  compDict['current_logfile'] = os.path.join(logdir, current_logfile)
              if is_running == "Running" and util.is_postgres(p_comp):
                  try:
                    util.read_env_file(p_comp)
                    pg = PgInstance("localhost", "postgres", "postgres", port)
                    pg.connect()
                    server_running_version = pg.get_version()
                    version_info = server_running_version.split(",")[0].split()
                    running_version = version_info[1]
                    if not util.check_running_version(version, running_version):
                      compDict['status'] = "Stopped"
                    else:
                      compDict['built_on'] = version_info[3]
                      size = pg.get_cluster_size()
                      up_time = util.get_readable_time_diff(str(pg.get_uptime().seconds), precision=2)
                      compDict['data_size'] = size
                      compDict['up_time'] = up_time
                      if PGC_ISJSON == "False":
                        db_list = pg.get_database_list()
                        compDict['db_list'] = db_list
                        connections_list = pg.get_active_connections()
                        total = None
                        for c in connections_list:
                          if c['state'] == 'total':
                            total = c['count']
                          if c['state'] == 'max':
                            max_conn = c['count']
                        if total:
                          connections = str(total) + "/" + str(max_conn)
                          compDict['connections'] = connections
                    pg.close()
                  except Exception as e:
                    my_logger.error(traceback.format_exc())
                    pass

          compJson.append(compDict)

          if not isJSON:
            api.info_component(compDict, kount)
        if isJSON:
          print(json.dumps(compJson, sort_keys=True, indent=2))
      except sqlite3.Error as e:
        fatal_sql_error(e, sql, "INFO")
    exit_cleanly(0)


  ## STATUS ####################################################
  if (p_mode == 'status'):
    for c in p_comp_list:
      check_status(c, p_mode)
    exit_cleanly(0)


  ## CLEAN ####################################################
  if (p_mode == 'clean'):
    conf_cache = PGC_HOME + os.sep + "conf" + os.sep + "cache" + os.sep + "*"
    files = glob.glob(conf_cache)
    for f in files:
      os.remove(f)
    exit_cleanly(0)


  ## LIST ##################################################################################
  if (p_mode == 'list'):
    get_list()


  ## DEPLIST ##############################################################################
  if (p_mode == 'deplist'):
    dl = get_depend_list(p_comp_list)
    exit_cleanly(0)

  if (p_mode == 'download'):
    if p_comp == "all":
      util.print_error("Invalid component parameter (all)")
      exit_cleanly(1)
    for c in p_comp_list:
      if(p_version==""):
        ver = get_latest_ver_plat(c)
      else:
        ver = p_version
      base_name = c + "-" + ver
      conf_cache = "conf" + os.sep + "cache"
      bz2_file = conf_cache + os.sep + base_name + ".tar.bz2"
      if os.path.exists(bz2_file) and is_downloaded(base_name):
        msg = "File is already downloaded"
        util.exit_message(msg, 1)
      if not retrieve_comp(base_name, c):
        comment = "Download failed"
        util.exit_message(comment,1)
      cwd_file = os.getcwd() + os.sep + base_name + ".tar.bz2"
      copy2 (bz2_file, cwd_file)
      comment = "Sucessfully downloaded."
      file_size = util.get_file_size(os.path.getsize(bz2_file))
    exit_cleanly(0)


  ## REMOVE ##################################################
  if (p_mode == 'remove'):

    for c in p_comp_list:
      if c not in installed_comp_list:
        msg = c + " is not installed."
        print(msg)
        continue
      if util.get_platform() == "Windows" and c == "python2":
        msg = c + " cannot be removed."
        return_code = 1
        if isJSON:
          return_code = 0
          msg = '[{"status":"error","msg":"' + msg + '"}]'
        util.exit_message(msg, return_code)

      if is_depend_violation(c, p_comp_list):
        exit_cleanly(1)

      server_port = util.get_comp_port(c)

      server_running = False
      if server_port > "1":
        server_running = util.is_socket_busy(int(server_port), c)

      if server_running:
        run_script(c, "stop-" + c, "stop")
        time.sleep(5)

      remove_comp(c)

      extensions_list = get_installed_extensions_list(c)
      for ext in extensions_list:
        update_component_state(ext, p_mode)

      update_component_state(c, p_mode)
      comment = "Sucessfully removed the component."
      if isJSON:
        msg = '[{"status":"complete","msg":"' + comment + '","component":"' + c + '"}]'
        print(msg)

    exit_cleanly(0)

  ## INSTALL ################################################
  if (p_mode == 'install'):
    if isAUTOSTART:
      exit_cleanly (util.install_pg_autostart(isJSON, p_comp_list))
    deplist = get_depend_list(p_comp_list)
    component_installed = False
    dependent_components = []
    installed_commponents = []
    dependencies = [ p for p in deplist if p not in p_comp_list ]
    for c in deplist:
      if requested_p_version and c in p_comp_list:
        status = install_comp(c,p_version,p_rver=requested_p_version)
        p_version = requested_p_version
      else:
        p_version = None
        status = install_comp(c)
      update_component_state(c, p_mode, p_version)
      isExt = is_extension(c)
      if isExt:
        parent = util.get_parent_component(c,0)
      if status==1 and (c in p_comp_list or p_comp_list[0]=="all") :
        ## already installed
        pass
      elif status!=1:
        installed_comp_list.append(c)
        isExt = is_extension(c)
        if isExt:
          util.create_manifest(c, parent)
          util.copy_extension_files(c, parent)
        script_name = "install-" + c
        run_script(c, script_name, "")
        if c in p_comp_list or p_comp_list[0] == "all":
          component_installed = True
          installed_commponents.append(c)
          if isExt:
            util.delete_dir(os.path.join(PGC_HOME, c))
        else:
          dependent_components.append(c)

    exit_cleanly(0)

  # Verify data & log directories ############################
  data_home = PGC_HOME + os.sep + 'data'
  if not os.path.exists(data_home):
    os.mkdir(data_home)
    data_logs = data_home + os.sep + 'logs'
    os.mkdir(data_logs)


  script_name = ""

  ## UPDATE the remote components list ########################
  if (p_mode == 'update'):
    retrieve_remote()
    if not isJSON:
      print(" ")
    try:
      l = connL.cursor()
      sql = "SELECT component, version, platform, status FROM components"
      l.execute(sql)
      rows = l.fetchall()
      l.close()
      hasUpdates = 0
      hub_update = 0
      bam_update = 0
      for row in rows:
        c_comp = str(row[0])
        c_ver  = str(row[1])
        c_plat = str(row[2])
        c_stat = str(row[3])
        c = connL.cursor()
        sql="SELECT version FROM versions \n" + \
            " WHERE component = ? AND " + util.like_pf("platform") + " \n" + \
            "   AND is_current = 1"
        c.execute(sql, [c_comp])
        v_row = c.fetchone()
        if v_row == None:
          v_ver = c_ver
        else:
          v_ver = str(v_row[0])
        c.close()
        comp_ver_plat = c_comp + "-" + c_ver
        if c_plat > "":
          comp_ver_plat = comp_ver_plat + "-" + c_plat
        comp_ver_plat = comp_ver_plat + (' ' * (35 - len(comp_ver_plat)))

        msg = ""
        if c_ver >= v_ver:
          msg = comp_ver_plat + " is up to date."
        else:
          if c_comp=='hub':
            hub_update = 1
          elif c_comp=="bam2":
            bam_update = 1
          else:
            hasUpdates = 1
          msg = comp_ver_plat + " upgrade available to (" + v_ver + ")"
          my_logger.info(msg)
        if hub_update == 1:
          rc = upgrade_component('hub')
          hub_update = 0

      [interval, last_update_utc, next_update_utc, unique_id] = util.read_hosts('localhost')
      util.update_hosts('localhost', interval, unique_id, True)

      if isJSON:
        print('[{"status":"completed","has_updates":'+ str(hasUpdates) + '}]')
      else:
        if hasUpdates == 0 and bam_update == 0:
          if not isSilent:
            print("No updates available.\n")
            show_latest=True
            get_list()
        else:
          get_list()
    except sqlite3.Error as e:
      fatal_sql_error(e, sql, "update in mainline")

  ## Enable/Disable Individual components ######################
  if (p_mode == 'enable' or p_mode == 'disable' or p_mode == 'remove'):
    if p_comp == 'all':
      msg = 'You must ' + p_mode + ' one component at a time'
      my_logger.error(msg)
      util.exit_message(msg, 1)
    if not util.is_server(p_comp, util.get_comp_port(p_comp)) and p_mode == 'disable':
      msg = 'Only Server components can be disabled'
      my_logger.error(msg)
      util.exit_message(msg, 1)
    update_component_state(p_comp, p_mode)

  ## CONFIG, INIT, RELOAD, ACTIVITY ########################
  if (p_mode in ['config', 'init', 'reload', 'activity']):
    script_name = p_mode + "-" + p_comp
    run_script(p_comp, script_name, extra_args)


  ## STOP component(s) #########################################
  if ((p_mode == 'stop') or (p_mode == 'kill') or (p_mode == 'restart')):
    if p_comp == 'all':
      ## iterate through components in reverse list order
      for comp in reversed(dep9):
        script_name = "stop-" + comp[0]
        run_script(comp[0], script_name, p_mode)
    else:
      script_name = "stop-" + p_comp
      run_script(p_comp, script_name, p_mode)

  ## START component(s) ########################################
  if ((p_mode == 'start')  or (p_mode == 'restart')):
    if p_comp == 'all':
      ## Iterate through components in primary list order.
      ## Components with a port of "1" are client components that
      ## are only launched when explicitely started
      for comp in dep9:
        if util.get_comp_port(comp[0]) > "1":
          script_name = "start-" + comp[0]
          run_script(comp[0], script_name, p_mode)
    else:
      present_state = util.get_comp_state(p_comp)
      if (present_state == "NotInstalled"):
         msg = "Component '" + p_comp + "' is not installed."
         my_logger.info(msg)
         util.exit_message(msg, 0)
      if not util.is_server(p_comp, util.get_comp_port(p_comp)):
         msg = "'" + p_comp + "' component cannot be started."
         my_logger.error(msg)
         util.print_error(msg)
         exit_cleanly(1)
      if not present_state == "Enabled":
        update_component_state(p_comp, "enable")
      script_name = "start-" + p_comp
      run_script(p_comp, script_name, p_mode)

  ## UPGRADE component(s) #####################################
  if (p_mode == 'upgrade'):
    if p_comp == 'all':
      upgrade_flag = 1
      for comp in dep9:
        rc = upgrade_component(comp[0])
        if rc == 0:
          upgrade_flag = 0
      if upgrade_flag == 1:
        msg = "All components are already upgraded to the latest version."
        print(msg)
        my_logger.info(msg)
    else:
      if len(p_comp_list)==1 and p_comp=="bam2" and isJSON:
        update_cmd = PGC_HOME + os.sep + "pgc upgrade bam2"
        scheduler_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
        if util.get_platform()=="Windows":
          my_logger.info(scheduler_time)
          schtask_cmd = os.getenv("SYSTEMROOT", "") + os.sep + "System32" + os.sep + "schtasks"
          schedule_cmd = schtask_cmd + ' /create /RU System /tn BamUpgrade /tr "' + update_cmd + '"'\
                         + " /sc once /st " + scheduler_time.strftime('%H:%M') \
                         + " /sd " + scheduler_time.strftime('%m/%d/%Y')
          my_logger.info(schedule_cmd)

          # delete the previous scheduler if exists for upgrading the bam
          try:
            delete_previous_taks = schtask_cmd + " /delete /tn BamUpgrade /f"
            schedule_return = subprocess.Popen(delete_previous_taks, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, shell=True).communicate()
          except Exception as e:
            my_logger.error(traceback.format_exc())
            pass

          #create the scheduler to upgrade bam
          try:
            schedule_return = subprocess.Popen(schedule_cmd, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, shell=True).communicate()
            my_logger.info(schedule_return)
          except Exception as e:
            my_logger.error(traceback.format_exc())
            pass
        else:
          from crontab import CronTab
          cron_tab = CronTab(user=True)
          jobs = cron_tab.find_command(command=update_cmd)
          for job in jobs:
              job.delete()
          cron_job=cron_tab.new(command=update_cmd, comment="upgrade bam")
          cron_job.minute.on(scheduler_time.minute)
          cron_job.hour.on(scheduler_time.hour)
          cron_job.day.on(scheduler_time.day)
          cron_job.month.on(scheduler_time.month)
          cron_tab.write()
          cron_tab.run_scheduler()
      else:

        rc = upgrade_component(p_comp)

        if rc == 1:
          msg = "Nothing to upgrade."
          print(msg)
          my_logger.info(msg)


  ## DBSTAT ######################################
  if p_mode == 'dbstat':
    try:
      util.read_env_file(p_comp)
      port = util.get_comp_port(p_comp)
      pg = PgInstance("localhost", "postgres", "postgres", int(port))
      pg.connect()
      for st in p_dbstat_list:
        if (st == 'get_aggregate_tps'):
          print(json.dumps(pg.get_aggregate_tps()))
      pg.close()
    except Exception as e:
      my_logger.error(traceback.format_exc())


  ## VERIFY repo components ######################
  if p_mode == 'verify':
    util.verify(isJSON)
    exit_cleanly(0)


  ## SET #################################################
  if p_mode == 'set':
    if len(args) == 5:
      util.set_value(args[2], args[3], args[4])
    else:
      print("ERROR: The SET command must have 3 parameters.")
      exit_cleanly(1)
    exit_cleanly(0)


  ## GET ################################################
  if p_mode == 'get':
    if len(args) == 4:
      print(util.get_value(args[2], args[3]))
    else:
      print("ERROR: The GET command must have 2 parameters.")
      exit_cleanly(1)
    exit_cleanly(0)


  ## UNSET ##############################################
  if p_mode == 'unset':
    if len(args) == 4:
      util.unset_value(args[2], args[3])
    else:
      print("ERROR: The UNSET command must have 2 parameters.")
      exit_cleanly(1)
    exit_cleanly(0)


except Exception as e:
  msg = str(e)
  my_logger.error(traceback.format_exc())
  if isJSON:
    json_dict = {}
    json_dict['state'] = "error"
    json_dict['msg'] = msg
    msg = json.dumps(json_dict)
  print(msg)
  exit_cleanly(1)

exit_cleanly(0)
