import re
import json

NEW_COMMAND_FILE = './new_command.tex'
SETTING_FILE = './setting.json'

def is_empty_line(line):
    return len(line.replace(' ', '').replace('\n', '')) == 0

with open(NEW_COMMAND_FILE) as f:
    new_commands = f.readlines()

# print(new_commands)

pattern = r'\{(.*?)\}'
setting = {
    re.findall(pattern, line)[0]: "dummy"
    for line in new_commands if not is_empty_line(line)
}

json.dump(setting, open(SETTING_FILE, 'w'), indent=4)
