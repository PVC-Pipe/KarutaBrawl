# open.py
# By: PVCPipe01
# holds the open command

import discord
import os
from discord.ext import commands

import asyncio
import pickle
import random

import globalValues
import host

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX

async def open(ctx, name):

    errorCode = -1

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5

        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 0:
            errorCode = 0
            
        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 1:
            errorCode = 1

        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 3:
            errorCode = 3

        else:
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 1

    if errorCode != -1:
        if errorCode == 5:
            await error(ctx, 5, name)
        elif errorCode == 1:
            await error(ctx, 1, name)
        elif errorCode == 2:
            await error(ctx, 2, name)
        return

    await openSub(ctx, name)

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 0

        await globalValues.store()

    await ctx.channel.send(embed=discord.Embed(description=name + " is now open"))

##############################################################################################################################################

async def openSub(ctx, name):

    typeOfBrawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[TYPE_INDEX]
    fileList = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[FILE_INDEX]

    if typeOfBrawl == "brawl":
        try:
            globalValues.removeFile(str(ctx.guild.id), fileList[0])
        except:
            pass
    else:
        for match in fileList:
            try:
                globalValues.removeFile(str(ctx.guild.id), match[0])
            except:
                pass

    globalValues.savedCompetitions[str(ctx.guild.id)][name][FILE_INDEX] = []
        
##############################################################################################################################################

async def error(ctx, code, *args):

    # invalid name
    if code == 5:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist"))

    # currently open
    elif code == 0:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is already open"))

    # currently being edited
    elif code == 1:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and cannot be accessed"))

    # currently live
    elif code == 3:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently live and cannot be edited"))
