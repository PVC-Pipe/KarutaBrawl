# participants.py
# By: PVCPipe01
# holds the participants command

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

async def participants(ctx, arg):

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

    participantList = []
    for id, card in participantDict.items():
        participantList.append((id, card[1]))

    currentIndex = 0
    startIndex = currentIndex
    endIndex = startIndex + 20
    if endIndex > len(participantList):
        endIndex = len(participantList)

    participantStr = ""
    for i in range(startIndex, endIndex):
        participantStr += "<@" + str(participantList[i][0]) + ">, **`" + str(participantList[i][1]) + "`**\n"

    footerStr = ""
    if len(participantList) == 0:
        footerStr = "Showing participants 0-0 out of 0"
    else:
        footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(participantList))

    embedVar = discord.Embed(title=name + " Participants", description=participantStr)
    embedVar.set_footer(text=footerStr)
    message = await ctx.channel.send(embed=embedVar)
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')
    await message.add_reaction('✅')

    confirmed = False
    while not confirmed:

        def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '✅')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '⬅️' or reaction == '➡️':
                if reaction == '⬅️':
                    startIndex = currentIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    endIndex = startIndex + 20
                    if endIndex > len(participantList):
                        endIndex = len(participantList)
                    currentIndex = startIndex
                    participantStr = ""
                    for i in range(startIndex, endIndex):
                        participantStr = participantStr + "<@" + str(participantList[i][0]) + ">, **`" + str(participantList[i][1]) + "`**\n"
                else:
                    startIndex = currentIndex + 20
                    endIndex = startIndex + 20
                    if endIndex > len(participantList):
                        endIndex = len(participantList)
                    startIndex = endIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    currentIndex = startIndex
                    participantStr = ""
                    for i in range(startIndex, endIndex):
                        participantStr = participantStr + "<@" + str(participantList[i][0]) + ">, **`" + str(participantList[i][1]) + "`**\n"

                footerStr = ""
                if len(participantList) == 0:
                    footerStr = "Showing participants 0-0 out of 0"
                else:
                    footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(participantList))

                embedVar = discord.Embed(title=name + " Participants", description=participantStr)
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

            elif reaction == '✅':
                embedVar = discord.Embed(title=name + " Participants", description=participantStr, color=discord.Color.green())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                confirmed = True

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title=name + " Participants", description=participantStr, color=discord.Color.red())
            embedVar.set_footer(text=footerStr)
            await message.edit(embed=embedVar)
        
##############################################################################################################################################

async def error(ctx, code, name):

    if code == 5:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    elif code == 4:
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is already completed."))