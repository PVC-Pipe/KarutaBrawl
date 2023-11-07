# globalValues.py
# By: PVCPipe01
# module to store global variables

import discord
import os
from discord.ext import commands
import aiorwlock
import pickle

import boto3

TYPE_INDEX = 0
ACCESS_INDEX = 1
PARTICIPANT_INDEX = 2
TIME_INDEX = 3
BACKGROUND_INDEX = 4
REACTION_INDEX = 5
FILE_INDEX = 6
WINNER_INDEX = 2

bot = None
savedCompetitions = None
guildLocks = None
brawlLocks = None
backgrounds = None
backgroundNames = None
passCards = None
sampleCards = None
cardCoordinates = None
header = None
pickleLock = None
KARUTA_ID = None
s3 = None
bucket = None

def init(inbot, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    global bot
    global savedCompetitions
    global guildLocks
    global brawlLocks
    global backgrounds
    global backgroundNames
    global passCards
    global sampleCards
    global cardCoordinates
    global header
    global pickleLock
    global KARUTA_ID
    global s3
    global bucket

    s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    bucket = 'karuta-brawl'

    bot = inbot

    savedCompetitions = {}

    # populate savedCompetitions with the info from the json
    try:
        s3.Object(bucket, 'savedCompetitions.txt').download_file('savedCompetitions.txt')
        with open('savedCompetitions.txt', 'rb') as f:
            savedCompetitions = pickle.load(f)
    except:
        pass

    for guild in bot.guilds:
        if savedCompetitions.get(str(guild.id)) == None:
            savedCompetitions[str(guild.id)] = {}

    guildLocks = {}
    for guild in savedCompetitions:
        lock = aiorwlock.RWLock()
        guildLocks[guild] = lock

    brawlLocks = {}
    for guild, brawls in savedCompetitions.items():
        brawlLocks[guild] = {}
        for brawl in brawls:
            brawlLocks[guild][brawl] = aiorwlock.RWLock()

    backgrounds = {}

    try:
        s3.Object(bucket, 'backgrounds.txt').download_file('backgrounds.txt')
        with open('backgrounds.txt', 'rb') as f:
            backgrounds = pickle.load(f)
    except:
        pass

    passCards = "https://media.discordapp.net/attachments/829392725248835656/829394796539019334/pass_card.png"

    sampleCards = ["https://media.discordapp.net/attachments/829392752630300716/829394731456004186/sample_01.png", "https://media.discordapp.net/attachments/829392752630300716/829394757637111878/sample_02.png"]

    cardCoordinates = {2 : ((50, 50), (564, 50))}

    header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}

    pickleLock = aiorwlock.RWLock()

    KARUTA_ID = 646937666251915264

async def store():

    async with pickleLock.writer_lock:
        with open('savedCompetitions.txt', 'wb') as f:
            pickleFile = pickle.dump(savedCompetitions, f)
        s3.Object(bucket, 'savedCompetitions.txt').upload_file(Filename='savedCompetitions.txt')


def removeFile(guild, fileName):

    obj = s3.Object(bucket, guild + "/" + fileName)
    obj.delete()

def addFile(guild, fileName):

    s3.Object(bucket, guild + "/" + fileName).upload_file(fileName)

def getFile(guild, fileName):

    s3.Object(bucket, guild + "/" + fileName).download_file(fileName)
