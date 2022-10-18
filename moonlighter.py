from datetime import datetime
from dateutil.relativedelta import relativedelta
from shutil import copy
from dateutil.parser import parse
from genericpath import exists
import json
from os import makedirs, mkdir, path, remove
from ppadb.client import Client as AdbClient
import ppadb.device
from Pcolors import cprint
from Pcolors.shortcuts import light, format
import Pcolors

LOCAL_SAVE_PATH = (
    "C:/Program Files (x86)/Steam/userdata/334423095/606150/remote/gameslot"
)
ANDROID_SAVE_PATH = "/storage/emulated/0/Android/data/com.netflix.NGP.Moonlighter/files/AQEEMwABASBcNDhG5tN6Aa5mx0ODvdOfH2HiPM2bNF1btyNjgZc4GJT4gameslot"
HISTORY_PATH = "./history/moonlighter"

GREY = Pcolors.code(light.black)
RED = Pcolors.code(light.red)
GREEN = Pcolors.code(light.black)
BLUE = Pcolors.code(light.blue)
MAGENTA = Pcolors.code(light.magenta)
RESET = Pcolors.code(0)

if not exists(HISTORY_PATH):
    makedirs(HISTORY_PATH)


client = AdbClient(host="127.0.0.1", port=5037)
device: "ppadb.device.Device|None" = client.device("b8400628")

if not device:
    cprint("> ERROR < Device not connected", light.red)
    exit(1)

if device.get_pid("com.netflix.NGP.Moonlighter"):
    cprint("> ERROR < Please close moonlighter before sync", light.red)
    exit(1)


timestamp = str(datetime.now()).split(".")[0].replace(" ", "_").replace(":", ".")
ANDROID_DOWNLOAD_FILE = path.join(HISTORY_PATH, timestamp + "__android")

print(f"{GREY}Downloading {BLUE}{ANDROID_DOWNLOAD_FILE} {RESET}", end="")
e = device.pull(ANDROID_SAVE_PATH, ANDROID_DOWNLOAD_FILE)
cprint(f"Done.", light.green)


def humanDuration(seconds):
    delta = relativedelta(seconds=int(seconds))
    result = ""
    if delta.hours:
        result += str(delta.hours) + "h "
    if delta.minutes:
        result += str(delta.minutes) + "m "
    if delta.seconds:
        result += str(delta.seconds) + "s"
    return result


def keepLocalOrNot():
    with open(ANDROID_DOWNLOAD_FILE, "r") as f:
        androidData = json.load(f)
        androidLatestSave = parse(androidData["gameSlots"][0]["timeLastSave"])
        androidTotalPlayed = int(
            androidData["gameSlots"][0]["achievements"]["totalPlayTime"]
        )
        androidTotalPlayedReadable = humanDuration(androidTotalPlayed)
    with open(LOCAL_SAVE_PATH, "r") as f:
        localData = json.load(f)
        localLatestSave = parse(localData["gameSlots"][0]["timeLastSave"])

        localTotalPlayed = int(
            localData["gameSlots"][0]["achievements"]["totalPlayTime"]
        )
        localTotalPlayedReadable = humanDuration(localTotalPlayed)

    localLatest = False
    if localLatestSave > androidLatestSave:
        localLatest = True
    elif localLatestSave == androidLatestSave:
        print("saves are identical")
        remove(ANDROID_DOWNLOAD_FILE)
        exit(0)

    localLonger = False
    if localTotalPlayed > androidTotalPlayed:
        localLonger = True
    elif localTotalPlayed == androidTotalPlayed:
        print("saves are identical")
        remove(ANDROID_DOWNLOAD_FILE)
        exit(0)

    cprint("Last save on Android  :", light.black, end="")
    cprint(
        androidLatestSave.strftime("%Y-%m-%d %I:%M %p"),
        light.red if localLatest else light.green,
        end=" ",
    )
    cprint(
        androidTotalPlayedReadable,
        light.red if localLonger else light.green,
    )
    cprint("Last save on Desktop  :", light.black, end="")

    cprint(
        localLatestSave.strftime("%Y-%m-%d %I:%M %p"),
        light.green if localLatest else light.red,
        end=" ",
    )
    cprint(
        localTotalPlayedReadable,
        light.green if localLonger else light.red,
    )

    if localLatest:
        r = input(f"{GREY} Upload to android {MAGENTA}    {GREY}? (y/n) {RESET}")
        if r == "y":
            return True
        else:
            r = input(f"{GREY} Pull from android {MAGENTA}    {GREY}? (y/n) {RESET}")
            if r == "y":
                return False
            else:
                remove(ANDROID_DOWNLOAD_FILE)
                exit(0)
    else:
        r = input(f"{GREY} Pull from android {MAGENTA}    {GREY}? (y/n) {RESET}")
        if r == "y":
            return False
        else:
            r = input(f"{GREY} Upload to android {MAGENTA}    {GREY}? (y/n) {RESET}")
            if r == "y":
                return True
            else:
                remove(ANDROID_DOWNLOAD_FILE)
                exit(0)


keepLocal = keepLocalOrNot()

if keepLocal:
    print("Copying  to ...")
    print(f"\t {GREY}backup: {BLUE}{ANDROID_DOWNLOAD_FILE}{RESET}")
    device.push(LOCAL_SAVE_PATH, ANDROID_SAVE_PATH)
    print(f"{GREEN}done. {RESET}")
else:
    print("Copying  to ...")
    backup = ANDROID_DOWNLOAD_FILE.replace("android", "local")
    copy(LOCAL_SAVE_PATH, backup)
    print(f"\t {GREY}backup: {BLUE}{backup}{RESET}")
    copy(ANDROID_DOWNLOAD_FILE, LOCAL_SAVE_PATH)
    remove(ANDROID_DOWNLOAD_FILE)
