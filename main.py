import discord
import webserver
import os
import sys
import argparse
import json
import requests
import asyncio
from communication import WebsocketClient

from threading import Thread

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--development", help="Runs outside raspberry pi")

args = parser.parse_args()

if not args.development:
    os.chdir("/home/bongo/Downloads/FederationBankAccountant")

def getConfig(key):
    with open("config.json", "r") as f:
        data = json.load(f)

    return data[key]

bot = discord.Bot(intents=discord.Intents.all())

@bot.command(name="calculate-interest", guild_ids=[1132706354415534162])
async def addcredits(ctx):
    if ctx.author.id == 485513915548041239:
        await ctx.defer()
        request = requests.post(
            "https://bank.federationfleet.xyz/calcinterest",
            json={
                "auth": getConfig("token")
            }
        )

        await ctx.respond(request.status_code)

@bot.command(name="add-credits", guild_ids=[1132706354415534162])
async def addcredits(ctx, account, adder, amount:int, reason="No Reason Specified"):
    if ctx.author.id == 485513915548041239:
        await ctx.defer()
        request = requests.post(
            "https://bank.federationfleet.xyz/admin/transaction/{}/{}".format(account, adder),
            json={
                "reason": reason,
                "amount": amount,
                "auth": getConfig("token")
            }
        )

        await ctx.respond(request.status_code)

@bot.command(description="restart")
async def restart(ctx):
    if not ctx.author.id == 485513915548041239:
        return
    await ctx.defer()
    await ctx.respond("Restarting...")
    requests.get("http://localhost:6060/fbdc")
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.event
async def on_ready():
    loop = asyncio.get_running_loop() 

    async def isConnected():
        guild = await bot.fetch_guild(1132706354415534162)
        channel = await guild.fetch_channel(1199146381873516676)
        await channel.send("Websocket Connection Established")

    async def newTransactionAdmin(data):
        guild = await bot.fetch_guild(1132706354415534162)
        reserve = await guild.fetch_channel(1132707139866075186)
        circulation = await guild.fetch_channel(1144438545025597491)

        transactions = await guild.fetch_channel(1134906690588901377)

        adder = data["adder"]
        amount = data["amount"]
        account = data["account"]
        description = data["description"]

        totalbalance = data["totalbalance"]
        reservebalance = data["reservebalance"]

        if amount > 0:
            embed = discord.Embed(
                title="New Transaction",
                color=0x00ff00 if amount > 0 else 0xff0000,
                description="`{}` **({} Credits)** > **{}'s Account** (`#{}` \"{}\")\n\nDescription: {}".format(adder, amount, account["ownerName"], account["_id"], account["name"], description)   
            )
        else:
            embed = discord.Embed(
                title="New Transaction",
                color=0x00ff00 if amount > 0 else 0xff0000,
                description="**{}'s Account** (`#{}` \"{}\") **({} Credits)** > `{}` \n\nDescription: {}".format(account["ownerName"], account["_id"], account["name"], amount, adder, description)   
            )

        await transactions.send(embed=embed)
        await reserve.edit(name="[RESERVE]: {}".format(reservebalance))
        await circulation.edit(name="[CREDITS]: {}".format(totalbalance))

    async def newTransaction(data):
        guild = await bot.fetch_guild(1132706354415534162)
        reserve = await guild.fetch_channel(1132707139866075186)
        circulation = await guild.fetch_channel(1144438545025597491)

        transactions = await guild.fetch_channel(1134906690588901377)

        amount = data["amount"]
        account = data["account"]
        recievingAccount = data["recieving"]
        authorizer = data["authorizer"]
        description = data["description"]

        totalbalance = data["totalbalance"]
        reservebalance = data["reservebalance"]

        embed = discord.Embed(
            title="New Transaction",
            color=0x00ff00 if amount > 0 else 0xff0000,
            description="{}**{}'s Account** (`#{}` \"{}\") **({} Credits)** > **{}'s Account** (`#{}` \"{}\")\n\nDescription: {}".format("" if not authorizer else "`" + authorizer + "`\n\n", account["ownerName"], account["_id"], account["name"], amount, recievingAccount["ownerName"], recievingAccount["_id"], recievingAccount["name"], description)   
        )

        await transactions.send(embed=embed)
        await reserve.edit(name="[RESERVE]: {}".format(reservebalance))
        await circulation.edit(name="[CREDITS]: {}".format(totalbalance))

    bot.socketClient = WebsocketClient(loop, isConnected, newTransaction, newTransactionAdmin)
    Thread(target=bot.socketClient.start).start()

Thread(target=webserver.run).start()
bot.run(getConfig("token"))
