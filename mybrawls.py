# myBrawls.py
# By: PVCPipe01
# contains the myBrawls command

import discord
import os
from discord.ext import commands

import globalValues

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX
WINNER_INDEX = globalValues.WINNER_INDEX

async def mybrawls(ctx):

    brawlSavedStr = ""
    tournamentSavedStr = ""
    brawlCompletedStr = ""
    tournamentCompletedStr = ""
    guildBrawls = {}
    async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
        guildBrawls = globalValues.savedCompetitions.get(str(ctx.guild.id))
        
        if guildBrawls:
            for name, info in guildBrawls.items():
                if info[TYPE_INDEX] == "brawl" and info[ACCESS_INDEX] != 4:
                    brawlSavedStr = brawlSavedStr + name + "\n"
                elif info[TYPE_INDEX] == "tournament" and info[ACCESS_INDEX] != 4:
                    tournamentSavedStr = tournamentSavedStr + name + "\n"
                elif info[TYPE_INDEX] == "brawl" and info[ACCESS_INDEX] == 4:
                    brawlCompletedStr = brawlCompletedStr + name + "\n"
                else:
                    tournamentCompletedStr = tournamentCompletedStr + name + "\n"

    if brawlSavedStr == "":
        brawlSavedStr = "\u200b"
    if tournamentSavedStr == "":
        tournamentSavedStr = "\u200b"
    if brawlCompletedStr == "":
        brawlCompletedStr = "\u200b"
    if tournamentCompletedStr == "":
        tournamentCompletedStr = "\u200b"

    embedVar = discord.Embed(title="", description="")
    embedVar.add_field(name="Currently Saved Brawls", value=brawlSavedStr, inline=False)
    embedVar.add_field(name="Currently Saved Tournaments", value=tournamentSavedStr, inline=False)
    embedVar.add_field(name="Completed Brawls", value=brawlCompletedStr, inline=False)
    embedVar.add_field(name="Completed Tournaments", value=tournamentCompletedStr, inline=False)
    await ctx.channel.send(embed=embedVar)