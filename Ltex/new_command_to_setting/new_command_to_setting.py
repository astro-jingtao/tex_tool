import re
import json

NEW_COMMAND_FILE = './new_command.tex'
SETTING_FILE = './setting.json'

with open(NEW_COMMAND_FILE) as f:
    new_commands = f.readlines()

pattern = r'\{(.*?)\}'
setting = {
    re.findall(pattern, line)[0]: "dummy"
    for line in new_commands
}

json.dump(setting, open(SETTING_FILE, 'w'), indent=4)