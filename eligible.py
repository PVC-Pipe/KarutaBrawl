# eligible.py
# By: PVCPipe01
# holds the eligible command

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

async def eligible(ctx, arg1, arg2):

    name = arg1
    id = arg2
    id = id.replace('<', '').replace('@', '').replace('!', '').replace('>', '')
    id = id.strip()

    errorCode = -1

    try:
        id = int(id)

        success = False

        async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
            if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
                errorCode = 5
            elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 1:
                errorCode = 1
            elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 3:
                errorCode = 3
            elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 4:
                errorCode = 4
            elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][1][0] == None:
                errorCode = 6
            else:
                async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).writer_lock:
                    eligibilityList = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][1][0][0]

                    if id in eligibilityList:
                        errorCode = 7
                    else:
                        eligibilityList.append(id)
                        success = True

                    globalValues.savedCompetitions[str(ctx.guild.id)][name][PARTICIPANT_INDEX][1][0][0] = eligibilityList

            if success:
                await ctx.channel.send(embed=discord.Embed(description=arg2 + " successfully added to the " + name + " eligibility list."))
    except:
        await ctx.channel.send(embed=discord.Embed(description="Failed to add " + arg2))

    if errorCode != -1:
        await error(ctx, errorCode, name)

##############################################################################################################################################

async def error(ctx, code, name):

    if code == 5:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))
    elif code == 1:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and cannot be accessed."))
    elif code == 3:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is closed, and the eligibility list cannot be edited."))
    elif code == 4:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is completed, and the eligibility list cannot be edited."))
    elif code == 6:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + "'s participants are not restricted and therefore there is no eligibility list."))
    elif code == 7:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is already in the eligibility list."))