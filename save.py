import json, os

JSON_PATH = "save.json"
data : dict = {}

def save():
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=4)

if not os.path.exists(JSON_PATH):
    data = {"guilds": {}}
    save()
else:
    with open(JSON_PATH) as f:
        data = json.load(f)

def getModuleData(guild_id, module_name):
    return data["guilds"][str(guild_id)]["modules"][module_name]

def getGuildData(guild_id):
    return data["guilds"][str(guild_id)]