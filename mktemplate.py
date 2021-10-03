#!/usr/bin/python3
import os.path
import sys
import inspect
import datetime

template_cfg=None
replacements={}
filters={}
shortline=0
shortname='<file>'
fullname='<file>'
activeoutname='<Out>'
activeoutline=0
activedatetime=str(datetime.datetime.now().timestamp())
iserr=False

def get_active_input_file():
  return fullname
def get_active_output_file():
  return activeoutname
def get_active_output_line():
  return activeoutline
def get_active_timestamp():
  return activedatetime
replacements['__INPUT__'] = get_active_input_file
replacements['__FILE__'] = get_active_output_file
replacements['__LINE__'] = get_active_output_line
replacements['__DATE__'] = get_active_timestamp

def filter_identifier_only(s):
  out = ''
  for ch in s:
    if ch.isalnum() or ch == '_':
      out += ch
  return out
def filter_spaceline(s):
  out = ''
  for ch in s:
    if ch.isalnum():
      out += ch
    elif ch.isspace() or ch == '_':
      out += '_'
  return out
def filter_alnum_only(s):
  out = ''
  for ch in s:
    if ch.isalnum():
      out += ch
  return out
def filter_alnumspace_only(s):
  out = ''
  for ch in s:
    if ch.isalnum() or ch.isspace():
      out += ch
  return out
def filter_pathslash(s):
  return os.path.join(s,'')
def filter_splitext_0(s):
  return os.path.splitext(s)[0]
def filter_splitext_1(s):
  return os.path.splitext(s)[1]
def filter_repr(s):
  """Use repr(...) on the given string."""
  return repr(s)
def filter_replace(s,old=None,new=None,count=None):
  xcount = None
  if count:
    try:
      xcount = int(count)
    except ValueError as e:
      xcount = None
  return s.replace(old,new,xcount)
def filter_slice(s,start=None,stop=None,step=None):
  """slice(s,start=0,stop=-1,step=1) -> str

Extract a slice of the given string, from start to stop, taking
every step characters."""
  xstart = None
  xstop = None
  xstep = None
  if start:
    try:
      xstart = int(start)
    except ValueError as e:
      xstart = 0
  if stop:
    try:
      xstop = int(stop)
    except ValueError as e:
      xstop = -1
  if step:
    try:
      xstep = int(step)
    except ValueError as e:
      xstep = 1
  return s[slice(xstart,xstop,xstep)]
def filter_dropchars(s,chars=None):
  xchars = str(chars)
  out = ''
  for x in s:
    if x in xchars:
      continue
    else:
      out += x
  return out
def filter_onlychars(s,chars=None):
  xchars = str(chars)
  out = ''
  for x in s:
    if x in xchars:
      out += x
    else:
      continue
  return out
def filter_insertchars(s,chars=None,space=' '):
  """insertchars(s,chars=None,space=' ') -> str

Insert space before each occurence of a character in chars."""
  xchars = str(chars)
  out = ''
  for x in s:
    if x in xchars:
      out += space
    out += x
  return out
def filter_upper_only(s):
  out = ''
  for x in s:
    if x.isupper():
      out += x
  return out
def filter_lower_only(s):
  out = ''
  for x in s:
    if x.islower():
      out += x
  return out
def filter_help(s):
  """Get help on the filter of the given name."""
  global filters
  if s in filters:
    out = inspect.getdoc(filters[s])
  elif len(s) == 0:
    out = str('\n').join(filters.keys())
  else:
    out = None
  return str(out) if out else ''

def filter_date(s, f=None):
  """date(s, f=None) -> str

Generate a strftime-style string based on the given timestamp
number (use `__DATE__` for "today and now"), using `f` as the
format."""
  ts = datetime.datetime.fromtimestamp(float(s))
  return ts.strftime(f if f else '%c')


filters['date'] = filter_date
filters['help'] = filter_help
filters['onlychars'] = filter_onlychars
filters['lower_only'] = filter_lower_only
filters['upper_only'] = filter_upper_only
filters['insertchars'] = filter_insertchars
filters['dropchars'] = filter_dropchars
filters['slice'] = filter_slice
filters['replace'] = filter_replace
filters['pathslash'] = filter_pathslash
filters['basename'] = os.path.basename
filters['abspath'] = os.path.abspath
filters['dirname'] = os.path.dirname
filters['expanduser'] = os.path.expanduser
filters['expandvars'] = os.path.expandvars
filters['normcase'] = os.path.normcase
filters['normpath'] = os.path.normpath
filters['realpath'] = os.path.realpath
filters['splitext_0'] = filter_splitext_0
filters['splitext_1'] = filter_splitext_1
filters['identifier_only'] = filter_identifier_only
filters['spaceline'] = filter_spaceline
filters['alnum_only'] = filter_alnum_only
filters['alnumspace_only'] = filter_alnumspace_only
filters['repr'] = filter_repr
filters['lower'] = str.lower
filters['upper'] = str.upper
filters['strip'] = str.strip
filters['capitalize'] = str.capitalize
filters['casefold'] = str.casefold
filters['lstrip'] = str.lstrip
filters['rstrip'] = str.rstrip
filters['swapcase'] = str.swapcase
filters['title'] = str.title
  
def warn(message):
  print('%s:%i: warning: %s'%(shortname,shortline,message),file=sys.stderr)
  return
def err(message):
  global iserr
  iserr=True
  print('%s:%i: error: %s'%(shortname,shortline,message),file=sys.stderr)
  return

class FilterRef:
  def __init__(self, name, kwvals=None):
    self.name = name
    self.kwargs = kwvals if kwvals else {}

def string_subst(s):
  global replacements
  global filters
  global current_line
  out = ''
  l = len(s)
  mode = 0
  varname = None
  varfilter = None
  nextfilter = None
  nextkwlist = None
  nextkw = ''
  nextkwval = ''
  parencount = 0
  j = 0
  def lookup_var(varname):
    if varname and (varname in replacements):
      varx = replacements[varname]
      if hasattr(varx,'__call__'):
        varvalue = str(varx())
      else:
        varvalue = str(varx)
    elif varname:
      warn('unknown variable %s'%repr(varname))
      varvalue = ''
    else:
      warn('substitution without variable name')
      varvalue = ''
    return varvalue
  def post_to_out():
    # https://stackoverflow.com/a/11987499
    nonlocal varname, varfilter, nextfilter, out, nextkwlist
    varvalue = lookup_var(varname)
    if varfilter:
      for f in varfilter:
        if f.name in filters:
          try:
            varvalue = filters[f.name](varvalue, **f.kwargs)
          except TypeError as e:
            warn(e)
            warn('...while using filter %s'%repr(f.name))
          except ValueError as e:
            warn(e)
            warn('...while using filter %s'%repr(f.name))
        elif f.name:
          warn('skipping unknown filter %s'%repr(f.name))
        else:
          warn('skipping empty filter expression')
    out += varvalue
    varname = None
    varfilter = None
    nextfilter = None
    nextkwlist = None
    return
  for ch in s:
    if mode == 0: #normal copy
      if (ch == '$'):
        mode = 1
      else:
        out += ch
    elif mode == 1: #substitute?
      if (ch == '{'): #substitute!
        mode = 3
        varname = ''
      elif (ch == '$'): #literal $
        mode = 0
        out += '$'
      elif (ch == '#'): #comment
        mode = 2
      else:
        mode = 0
        warn('unexpected char %s after "$"'%(repr(ch)))
    elif mode == 2: #comment
      if (ch == '#'): #end comment
        mode = 0
      else:
        pass
    elif mode == 3: #varname
      if (ch == ':'): #on to filters
        mode = 4
        varfilter = []
        nextfilter = ''
      elif ch == '}':
        mode = 0
        post_to_out()
      else:
        varname += ch
    elif mode == 4 or mode == 5: #filter
      if (ch == ':'): #on to next filter
        varfilter.append(FilterRef(nextfilter,nextkwlist))
        mode = 4
        nextfilter = ''
        nextkwlist = None
      elif ch == '}':
        varfilter.append(FilterRef(nextfilter,nextkwlist))
        mode = 0
        post_to_out()
      elif mode == 4 and ch == '(':
        mode = 6 #start the arglist
        nextkwlist = {}
        nextkw = ''
      elif mode == 5:
        warn('unexpected char %s after ")"'%(repr(ch)))
      else:
        nextfilter += ch
    elif mode == 6: #keyword argument name
      if parencount == 0 and ch == ')' or ch == ',':
        #pack up the keyword
        if nextkw:
          nextkwlist[nextkw] = None
        if ch == ')':
          mode = 5
        else:
          nextkw = ''
      elif ch == '=':
        nextkwval = ''
        mode = 7
      else:
        if ch == '(':
          parencount += 1
        elif ch == ')':
          parencount -= 1
        nextkw += ch
    elif mode == 7: #keyword argument value
      if parencount == 0 and ch == ')' or ch == ',':
        #parse the keyword value
        if len(nextkwval) > 0 and nextkwval[0].isdigit():
          try:
            nextkwlist[nextkw] = str(int(nextkwval,0))
          except ValueError as e:
            warn(str(e))
            nextkwlist[nextkw] = str(0)
        else: #assert a variable name
          nextkwlist[nextkw] = lookup_var(nextkwval)
        #pack up the keyword
        if ch == ')':
          mode = 5
        else:
          mode = 6
        nextkw = ''
      else:
        if ch == '(':
          parencount += 1
        elif ch == ')':
          parencount -= 1
        nextkwval += ch
    else:
      warn('unexpected subst machine state %s'%repr(mode))
      break
  if mode != 0:
    if (mode in [3,4]):
      warn('unterminated replacement')
    elif (mode == 2):
      warn('unterminated comment')
  return out

class FileHeader:
  def __init__(self,s=None):
    if s:
      self.parse(s)
    else:
      self.fname = None
      self.stoptoken = None
    return
  def parse(self,s):
    mode = 0
    fname = None
    token = None
    stoptoken = None
    if s[0] != '>':
      raise ValueError('mktemplate.FileHeader.parse')
    for ch in s[1:]:
      if mode == 0:
        if ch == '"': #filename
          mode = 1
          fname = ''
        elif ch == '<':
          token = ch
          mode = 3
        elif ch.isspace():
          continue
        else:
          warn("unexpected file header character %s"%repr(ch))
      elif mode == 1:
        if ch == '\\': #escape
          mode = 2
        elif ch == '"': #next part
          mode = 0
        else:
          fname += ch
      elif mode == 2:
        fname += ch
        mode = 1
      elif mode == 3:
        if ch.isspace():
          #inspect
          if token == '<<<': #stop token next
            mode = 4
            stoptoken = ''
          elif len(token) > 3 and token[0:3] == '<<<':
            mode = 0
            stoptoken = token[3:]
          else:
            warn("unexpected file header token %s"%repr(token))
            token = None
            mode = 0
        else:
          token += ch
      elif mode == 4:
        if ch.isspace():
          if len(stoptoken):
            mode = 0
        else:
          stoptoken += ch
      else:
        warn('unexpected file header machine state %s'%repr(mode))
        break
    self.fname = string_subst(fname) if fname else fname
    self.stoptoken = stoptoken
    self.cmnt = False
    return

class VarHeader:
  def __init__(self,s=None):
    if s:
      self.parse(s)
    else:
      self.varname = None
      self.rtext = None
    return
  def parse(self,s):
    mode = 0
    rtext = None
    varname = None
    isreq = False
    if s[0] not in '!=':
      raise ValueError('mktemplate.VarHeader.parse')
    elif s[0] == '!':
      isreq = True
    for ch in s[1:]:
      if mode == 0:
        if ch == '"': #text
          mode = 1
          rtext = ''
        elif ch.isalnum() or ch == '_':
          varname = ch
          mode = 3
        elif ch.isspace():
          continue
        else:
          warn("unexpected variable header character %s"%repr(ch))
      elif mode == 1:
        if ch == '\\': #escape
          mode = 2
        elif ch == '"': #next part
          mode = 0
        else:
          rtext += ch
      elif mode == 2:
        rtext += ch
        mode = 1
      elif mode == 3:
        if ch.isspace():
          mode = 0
        elif ch.isalnum() or ch == '_':
          varname += ch
        else:
          warn("unexpected variable header token %s"%repr(token))
          mode = 0
      else:
        warn('unexpected variable header machine state %s'%repr(mode))
        break
    self.varname = varname
    self.rtext = string_subst(rtext) if rtext else rtext
    self.isreq = isreq
    return

if __name__ == '__main__':
  def main(argc, argv):
    # parse args
    global replacements
    argi = 1
    want_help = False
    fname = None
    while argi < argc:
      if argv[argi] == '-?':
        want_help = True
        break
      elif argv[argi] == '-D':
        argi += 1
        if argi < argc:
          varname = argv[argi]
          argi += 1
        if argi < argc:
          replacements[varname] = argv[argi]
        else:
          err('incomplete "-D" option')
      else:
        fname = argv[argi]
      argi += 1
    if want_help or not fname:
      print('''mktemplate.py: generate files from template

usage: python3 mktemplate.py [options] (template_file)

options:
  -D (name) (value)
          Add a variable named (name) with string (value) to the list
          of replacement variables.

syntax (outside of string):
# ...
          comment
=var "...string..."
          assign a (possibly expanded) string to a variable name
!var
          request a variable from the user
>"filename" <<<END_MARKER
          begin a string of output to a file (or to `stdout` if
          filename is missing). output ends with the END_MARKER
          on a line by itself. (note that filename is also a
          string.)
syntax (inside a string):
  text...text
          literal text output
  ${var}
          output the latest string stored in `var`
  ${var:filter1:filter2:...}
          output the string of `var` with filters applied to it
  ${var:filter(key=value):...}
          give a key-value argument to a filter. value can be either
          an integer or a variable name. (to pass a string as a
          key-value argument, use a variable.)

  use the `help` filter to get information on the available filters:

=filter_name "upper"
=empty ""
> <<<EOF
Help text for the "upper" filter:
${filter_name:help}

List of all filters:
${empty:help}
EOF
''',file=sys.stderr)
      return 1
    if fname != '-':
      try:
        f = open(fname,'rt')
      except IOError as e:
        print(e, file=sys.stderr)
        return 1
    else:
      f = sys.stdin
    global fullname, shortname, shortline, activeoutline, activeoutname
    global iserr
    fullname=fname
    shortname=os.path.basename(fname)
    activeoutname=''
    activeoutline=0
    shortline=0
    shortstop=None
    mode=0
    g_to_close = False
    g = None
    g_usable = False
    done = False
    while not done:
      ln = f.readline()
      shortline += 1
      activeoutline += 1
      if not ln:
        done = True
        break
      elif mode == 0:
        if ln[0] == '#': #comment
          pass
        elif ln[0] in '=!': #require a variable
          vh = VarHeader(ln)
          if not vh.varname:
            err('variable line missing variable name')
          elif vh.isreq:
            if vh.varname not in replacements:
              err('missing definition for required variable %s'%repr(vh.varname))
              break
          elif vh.rtext is not None:
            replacements[vh.varname] = vh.rtext
          else:
            del replacements[vh.varname]
        elif ln[0] == '>': #output file
          fh = FileHeader(ln)
          if fh.fname:
            try:
              g = open(fh.fname, 'wt')
              g_usable = True
              g_to_close = True
            except IOError as e:
              print(e, file=sys.stderr)
              warn('skipping file %s'%repr(fh.fname))
              g_usable = False
              g_to_close = False
            activeoutname = fh.fname
          else:
            g = sys.stdout
            g_usable = True
            g_to_close = False
            activeoutname = '<stdout>'
          shortstop = fh.stoptoken
          mode = 1
          activeoutline = 0
      elif mode == 1: #in a file
        if shortstop and len(ln) <= len(shortstop)+2 \
            and ln.rstrip() == shortstop:
          mode = 0
          if g_to_close:
            g.close()
          g = None
          g_usable = False
          g_to_close = False
        elif g_usable:
          g.write(string_subst(ln))
        else:
          pass
    f.close()
    return 1 if iserr else 0
  res = main(len(sys.argv), sys.argv)
  exit(int(res))
