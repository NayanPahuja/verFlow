import configparser
import os

class verFlowRepository(object):
  """A git repository"""

  worktree = None
  gitdir = None
  conf = None

  def __init__(self, path, force=False):
    self.worktree = path
    self.gitdir = os.path.join(path, ".ver_flow")

    if not (force or os.path.isdir(self.gitdir)):
      raise Exception("Not a verFlow repository %s" % path)

    # Read configuration file in .git/config
    self.conf = configparser.ConfigParser()
    cf = repoFile(self, "config")

    if cf and os.path.exists(cf):
      self.conf.read([cf])
    elif not force:
      raise Exception("Configuration file missing")
    
    if not force:
      vers = int(self.conf.get("core", "repositoryformatversion"))
      if vers != 0 and not force:
        raise Exception("Unsupported repositoryformatversion %s" % vers)

def repoPath(repo, *path):
  """Compute path under repo's gitdir."""
  return os.path.join(repo.gitdir, *path)

def repoFile(repo, *path, mkdir=False):
  """Same as repoPath, but create dirname(*path) if absent."""

  if repoDir(repo, *path[:-1], mkdir=mkdir):
    return repoPath(repo, *path)

def repoDir(repo, *path, mkdir=False):
  """Same as repoPath, but mkdir *path if absent if mkdir."""

  path = repoPath(repo, *path)

  if os.path.exists(path):
    if(os.path.isdir(path)):
      return path
    else:
      raise Exception("Not a directory %s" % path)

  if mkdir:
    os.makedirs(path)
    return path
  else:
    return None
  
def repoCreate(path):
  """Create a new repository at path."""

  repo = verFlowRepository(path, True)

  # First we make sure the path either doesn't exist or is an
  # empty dir

  if os.path.exists(repo.worktree):
    if not os.path.isdir(repo.worktree):
      raise Exception ("%s is not a directory!" % path)
    if os.listdir(repo.worktree):
      raise Exception("%s is not empty!" % path)

  else:
    os.makedirs(repo.worktree)

  assert(repoDir(repo, "branches", mkdir=True))
  assert(repoDir(repo, "objects", mkdir=True))
  assert(repoDir(repo, "refs", "tags", mkdir=True))
  assert(repoDir(repo, "refs", "heads", mkdir=True))

  # .git/description
  with open(repoFile(repo, "description"), "w") as f:
    f.write("Unnamed repository; edit this file 'description' to name the repository.\n")
  
  # .git/HEAD
  with open(repoFile(repo, "HEAD"), "w") as f:
    f.write("ref: refs/heads/master\n")

  with open(repoFile(repo, "config"), "w") as f:
    config = repoDefaultConfig()
    config.write(f)

  return repo
  
def repoDefaultConfig():
  defConfig = configparser.ConfigParser()

  defConfig.add_section("core")
  defConfig.set("core", "repositoryformatversion", "0")
  defConfig.set("core", "filemode", "false")
  defConfig.set("core", "bare", "false")

  return defConfig

#function for finding the root of repo
def repoFind(path = ".",required = True):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".git")):
    return verFlowRepository(path)
  
  #if we don't find the repo, recurse back in directories to find it in parent dirs
  parent = os.path.realpath(os.path.join(path,".."))
  
  #if we are already in parent?

  if parent == path:
    #bottom case
    if required:
      raise Exception("No verFlow repository found %s" % path)
    else:
      return None
    
  return repoFind(parent,required)
    