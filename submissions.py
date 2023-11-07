# submissions.py
# By: PVCPipe01
# holds the submissions command

import discord
import os
from discord.ext import commands

import asyncio
import urllib.request
from urllib.request import urlopen
from PIL import Image
import pickle
import random
import math
import time

import globalValues
import host

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX

async def submissions(ctx, arg):

    name = arg

    participantInfo = None
    participantDict = None

    errorCode = -1

    async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5
        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 4:
            errorCode = 4
        else:
            async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).reader_lock:
                participantInfo = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX]
                participantDict = participantInfo[0]

    if errorCode != -1:
        await error(ctx, errorCode, name)
        return

    for card in participantDict.values():

        globalValues.getFile(str(ctx.guild.id), card[0])
        imageFile = discord.File(card[0])
        embedVar = discord.Embed(title="")
        embedVar.set_image(url="attachment://" + card[0])
        await ctx.channel.send(file=imageFile, embed=embedVar)
        os.remove(card[0])

##############################################################################################################################################

async def error(ctx, code, name):

    if code == 5:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    elif code == 4:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is already completed."))