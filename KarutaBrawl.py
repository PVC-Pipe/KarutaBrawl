# Karuta Brawl Bot
# By: PVCPipe01
# TODO: Tournament

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

import asyncio
import aiorwlock
import urllib.request
from urllib.request import urlopen
from PIL import Image

import json
import time
import math

import globalValues
from setup import setup
from host import host
from submit import submit
from close import close
from open import open
from start import start
from winners import winners
from edit import edit
from delete import delete
from submissions import submissions
from participants import participants
from eligible import eligible
from mybrawls import mybrawls

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

PREFIX = "kb!"

bot = commands.Bot(command_prefix=['kb!', 'KB!', 'Kb!', 'kB!'], case_insensitive=True, help_command=commands.DefaultHelpCommand(no_category='Commands'))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    globalValues.init(bot, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Valkyrie Drive: Mermaid"))


@bot.command(
    name="setup",
    help="Returns information on setting up the bot and the roles required to use commands.",
    brief="Returns info on the bot.")
async def setup_command(ctx):

    if ctx.author.guild_permissions.manage_guild:
        await setup(ctx)
        return

    roles = ctx.author.roles

    for role in roles:
        if role.name == "Brawls":
            await setup(ctx)
            break

@bot.command(
    name="host",
    help="Creates a Karuta brawl or tournament.\n" +
         "eg. " + PREFIX + "host <brawl or tournament>",
    brief="Creates a Karuta brawl or tournament.")
@commands.has_role("Brawls")
async def host_command(ctx, arg):
    await host(ctx, arg)

@bot.command(
    name="start",
    help="Starts the Karuta brawl or tournament. Requires the name of the brawl or tournament. If the name is multiple words, surround the name in quotation marks.\n" + 
         "eg. " + PREFIX + "start \"<name>\"",
    brief="Starts a Karuta brawl or tournament")
@commands.has_role("Brawls")
async def start_command(ctx, arg):
    await start(ctx, arg)

@bot.command(
    name="close",
    help="Closes a brawl or tournament to submissions.\n" +
         "eg. " + PREFIX + "close <brawl or tournament name>",
    brief="Closes a brawl or tournament"
    )
@commands.has_role("Brawls")
async def close_command(ctx, arg):
    await close(ctx, arg)
    
@bot.command(
    name="open",
    help="Opens a brawl or tournament to submissions after it has been closed.\n" +
         "eg. " + PREFIX + "open <brawl or tournament name>",
    brief="Opens a brawl or tournament"
    )
@commands.has_role("Brawls")
async def open_command(ctx, arg):
    await open(ctx, arg)

@bot.command(
    name="edit",
    help="Opens the editor for saved brawls and tournaments.\n" +
         "eg. " + PREFIX + "edit <brawl or tournament name>",
    brief="Edits a saved brawl or tournament")
@commands.has_role("Brawls")
async def edit_command(ctx, arg):
    await edit(ctx, arg)
            
@bot.command(
    name="delete",
    help="Deletes a saved brawl or tournament.\n" +
         "eg. " + PREFIX + "delete <brawl or tournament name>",
    brief="Deletes a saved brawl or tournament")
@commands.has_role("Brawls")
async def delete_command(ctx, arg):
    await delete(ctx, arg)

@bot.command(
    name="eligible",
    help="Adds a participant to the eligibility list of the given brawl or tournament.\n" +
         "eg. " + PREFIX + "eligible <brawl or tournament name> <id or @>",
    brief="Adds a person to the eligibility list")
@commands.has_role("Brawls")
async def eligible_command(ctx, arg1, arg2):
    await eligible(ctx, arg1, arg2)

@bot.command(
    name="mybrawls",
    help="Lists the saved brawls and tournaments that correspond to the server where the command is given.\n" +
         "eg. " + PREFIX + "mybrawls",
    brief="Lists your server's saved brawls and tournaments")
@commands.has_role("Brawls")
async def mybrawls_command(ctx):
    await mybrawls(ctx)

@bot.command(
    name="winners",
    help="Views the winners of the given brawl or tournament.\n" +
         "eg. " + PREFIX + "winners <brawl or tournament name>",
    brief="Views the winners")
@commands.has_role("Brawls")
async def winners_command(ctx, arg):
    await winners(ctx, arg)

@bot.command(
    name="submissions",
    help="Displays all of the cards in the brawl or tournament.\n" +
         "eg. kb!submissions <brawl or tournament name>",
    brief="Displaays all the participants' cards")
@commands.has_role("Brawls")
async def submissions(ctx, arg):
    await submissions(ctx, arg)

@bot.command(
    name="submit",
    help="Submits a card into a brawl or tournament. If the name is multiple words, surround it in quotation marks.\n" + 
         "eg. kb!submit \"<name>\" <card code>",
    brief="Submits a card")
async def submit_command(ctx, arg1, arg2):
    await submit(ctx, arg1, arg2)

@bot.command(
    name="participants",
    help="Views the current participant list for the given brawl or tournament.\n" +
         "eg. " + PREFIX + "participants <brawl or tournament name>",
    brief="Views the participant list")
async def participants_command(ctx, arg):
    await participants(ctx, arg)


@bot.event
async def on_guild_join(guild):

    if not globalValues.guildLocks.get(str(guild.id)):
        globalValues.guildLocks[str(guild.id)] = aiorwlock.RWLock()
        if globalValues.savedCompetitions.get(str(guild.id)) == None:
            globalValues.savedCompetitions[str(guild.id)] = {}

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            inviteChannel = bot.get_channel(829395553946304592)
            invite = await inviteChannel.create_invite()
            await channel.send("Hey there! Thank you for inviting Karuta Brawl to your server. Type \"kb!setup\" to get started! \nJoin the server to stay in the loop on updates and bug fixes.")
            await channel.send(invite)
            break

@bot.command()
@commands.is_owner()
async def addBackground(ctx, arg1, arg2, arg3):
    
    num = int(arg1)
    url = arg2
    name = arg3

    async with globalValues.backgroundLock.writer_lock:
        backgroundList = globalValues.backgrounds.get(num)
        backgroundList.append((arg2, arg3))

        globalValues.backgrounds[num] = backgroundList

        with open('backgrounds.txt', 'wb') as f:
            pickle.dump(globalValues.backgrounds, f)

bot.run(TOKEN)


