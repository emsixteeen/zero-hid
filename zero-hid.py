#!/usr/bin/env python

import sys
import os
import stat
import time

# Code Pages: https://gist.github.com/MightyPork/6da26e382a7ad91b5496ee55fdc73db2

codes_atoz = [c for c in range(0x04, 0x1d+1)]
lowercase = [chr(c) for c in range(ord('a'), ord('z')+1)]
uppercase = [chr(c) for c in range(ord('A'), ord('Z')+1)]

codes_digits = [c for c in range(0x1e, 0x27+1)]
numbers = [c for c in "1234567890"]
numbers_p = [c for c in "!@#$%^&*()"]

codes_other = {
  "NONE": 0x00,
  "ENTER": 0x28,
  "SPACE": 0x2c,
  "LCTRL": 0xe0,
  "LALT": 0xe2,
  "DELETE": 0x4c,
  "DOWN": 0x51,
}

modifiers = {
  None: 0x00,
  'LCTRL':  0x01,
  'LSHIFT': 0x02,
  'LALT':   0x04,
}

codes = {}
codes.update({ k: { 'code': v, 'modifier': None } for k,v in zip(lowercase, codes_atoz)})
codes.update({ k: { 'code': v, 'modifier': 'LSHIFT' } for k,v in zip(uppercase, codes_atoz)})
codes.update({ k: { 'code': v, 'modifier': None } for k,v in zip(numbers, codes_digits)})
codes.update({ k: { 'code': v, 'modifier': 'LSHIFT' } for k,v in zip(numbers_p, codes_digits)})
codes.update({ k: { 'code': v, 'modifier': None } for k,v in codes_other.items()})

def make_code(code, modifiers):
  # 8 bytes
  #
  # 1   = Modifier
  # 2   = NULL
  # 3   = Code
  # 4-8 = NULL
  modifier = 0
  for m in modifiers:
    modifier |= m

  return chr(modifier) + chr(0) + chr(code) + chr(0)*5

def make_code_seq(data):
  results = []

  for c in data:
    if c == ' ':
      c = 'SPACE'

    if c == '\n':
      c = 'ENTER'

    code = codes[c]
    modifier = modifiers[code['modifier']]
    results.append(make_code(code['code'], [modifier]))
    results.append(make_code(codes['NONE']['code'], []))
  return results

def write_seq(dev, codes):
  with open(dev, 'rb+') as hid:
    for c in codes:
      hid.write(c.encode())

def dump_seq(codes):
  for c in codes:
    print(''.join('\\x{:02x}'.format(ord(y)) for y in c))
  
def make_salute():
  # 3-finger salute = Ctrl+Alt+Delete
  mods = [modifiers['LCTRL'], modifiers['LALT']]
  code = codes['DELETE']['code']

  return [make_code(code, mods)]

def make_enter():
  return make_code_seq('\n')

def read_file(file):
  with open(file, 'r') as fh:
    return fh.read().splitlines() 

def check_dev(dev):
  if stat.S_ISCHR(os.stat(dev).st_mode) != True:
    print("%s is not expected device" % dev)
    sys.exit(1)

def check_usage():
  if len(sys.argv) != 5:
    print("usage: zero-hid <device> <file> <step> <wait>")
    print("  <device> - the usb gadget device to use")
    print("  <file>   - the file with the list of entries")
    print("  <step>   - how many attempts before reboot")
    print("  <wait>   - how long to wait after reboot")
    sys.exit(1)

def main():
  check_usage()
  check_dev(sys.argv[1])

  dev = sys.argv[1]
  file = sys.argv[2]
  step = int(sys.argv[3])
  wait = int(sys.argv[4])

  print("device = %s, file = %s, step = %d, wait = %d" % (dev, file, step, wait))

  entries = read_file(file)
  counter = 0
  linenumber = 0

  for entry in entries:
    linenumber += 1

    if entry.startswith('#') or len(entry) == 0:
      continue

    codes = make_code_seq(entry)
    enter = make_code_seq('\n')
    counter += 1

    print("sending: [ % 2d ] %s" % (linenumber, entry))
    write_seq(dev, codes)
    time.sleep(1)
    write_seq(dev, enter) 
    time.sleep(2)

    if counter % step == 0:
      print("sending reboot, sleeping for %d seconds" % wait)
      write_seq(dev, make_salute())  
      time.sleep(wait)

      print("sending: <ENTER>")
      write_seq(dev, make_enter())
      time.sleep(wait)

if __name__ == "__main__":
  main()
  
