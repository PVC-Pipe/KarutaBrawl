# winners.py
# By: PVCPipe01
# holds the winners command

import discord
import os
from discord.ext import commands

import math
import random
import asyncio
import urllib.request
from urllib.request import urlopen
from PIL import Image
import time
import aiorwlock
import operator
import pickle

import globalValues

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX
WINNER_INDEX = globalValues.WINNER_INDEX

async def winners(ctx, arg):

    name = arg
    info = None
    errorCode = -1
    accessState = -1

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        info = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
        if not info:
            errorCode = 5
        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] != 4:
            errorCode = 0
        else:
            accessState = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX]
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 1

    if errorCode != -1:
        await error(ctx, errorCode, name)
        return
    
    await ctx.message.delete()

    typeOfBrawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[TYPE_INDEX]

    if typeOfBrawl == "brawl":
        firstPlaceList = winnerList[0]
        secondPlaceList = winnerList[1]
        thirdPlaceList = winnerList[2]

        if len(secondPlaceList) == 0 and len(thirdPlaceList) == 0:
            if len(firstPlaceList) == 1:
                embedVar = firstPlaceList[0][0]
                globalValues.getFile(str(ctx.guild.id), firstPlaceList[0][1])
                imageFile = discord.File(firstPlaceList[0][1])
                embedVar.set_image(url="attachment://" + firstPlaceList[0][1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(firstPlaceList[0][1])
            else:
                await ctx.channel.send(embed=discord.Embed(title="Winners of " + name + "!", color=discord.Color.gold()))
                for card in firstPlaceList:
                    embedVar = card[0]
                    globalValues.getFile(str(ctx.guild.id), card[1])
                    imageFile = discord.File(card[1])
                    embedVar.set_image(url="attachment://" + card[1])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(card[1])

        else:
            if len(firstPlaceList) == 1:
                embedVar = firstPlaceList[0][0]
                globalValues.getFile(str(ctx.guild.id), firstPlaceList[0][1])
                imageFile = discord.File(firstPlaceList[0][1])
                embedVar.set_image(url="attachment://" + firstPlaceList[0][1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(firstPlaceList[0][1])
            else:
                await ctx.channel.send(embed=discord.Embed(title="1st Place Winners of " + name + "!", color=discord.Color.gold()))
                for card in firstPlaceList:
                    embedVar = card[0]
                    globalValues.getFile(str(ctx.guild.id), card[1])
                    imageFile = discord.File(card[1])
                    embedVar.set_image(url="attachment://" + card[1])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(card[1])

            if len(secondPlaceList) == 1:
                embedVar = secondPlaceList[0][0]
                globalValues.getFile(str(ctx.guild.id), secondPlaceList[0][1])
                imageFile = discord.File(secondPlaceList[0][1])
                embedVar.set_image(url="attachment://" + secondPlaceList[0][1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(secondPlaceList[0][1])
            elif len(secondPlaceList) > 0:
                await ctx.channel.send(embed=discord.Embed(title="2nd Place Winners of " + name + "!", color=0xAAA9AD))
                for card in secondPlaceList:
                    embedVar = card[0]
                    globalValues.getFile(str(ctx.guild.id), card[1])
                    imageFile = discord.File(card[1])
                    embedVar.set_image(url="attachment://" + card[1])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(card[1])

            if len(thirdPlaceList) == 1:
                embedVar = thirdPlaceList[0][0]
                globalValues.getFile(str(ctx.guild.id), thirdPlaceList[0][1])
                imageFile = discord.File(thirdPlaceList[0][1])
                embedVar.set_image(url="attachment://" + thirdPlaceList[0][1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(thirdPlaceList[0][1])
            elif len(thirdPlaceList) > 0:
                await ctx.channel.send(embed=discord.Embed(title="3rd Place Winners of " + name + "!", color=0xCD7F32))
                for card in thirdPlaceList:
                    embedVar = card[0]
                    globalValues.getFile(str(ctx.guild.id), card[1])
                    imageFile = discord.File(card[1])
                    embedVar.set_image(url="attachment://" + card[1])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(card[1])
    else:
        for card in globalValues.savedCompetitions.get(str(ctx.guild.id)).get(arg)[WINNER_INDEX]:
            embed = card[0]
            globalValues.getFile(str(ctx.guild.id), card[1])
            imageFile = discord.File(card[1])
            embed.set_image(url="attachment://" + card[1])
            await ctx.channel.send(file=imageFile, embed=embed)
            os.remove(card[1])


    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = accessState

async def error(ctx, code, *args):

    if code == 5:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    elif code == 0:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " has not been run and therefore has no winners."))
        