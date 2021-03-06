#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from discord.ext import commands
import discord
import asyncio

from .utils import checks, data


class Pokemon(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.no_pm()
    async def box(self, ctx, member: discord.Member=None):
        """Check the pokemon in your box"""
        if member is None:
            member = ctx.author
        box = await self.bot.di.get_box(member)

        pokemon = [f"{x.id}: **{x.name}**" for x in box]
        description = "\n".join(pokemon)
        embed = discord.Embed(description=description, title=f"{member.display_name}'s Pokemon")
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.group(aliases=["p"], invoke_without_command=True)
    @checks.no_pm()
    async def pokemon(self, ctx, member: discord.Member=None):
        """Subcommands for Pokemon management, see rp!help pokemon
        Same use as rp!box"""
        if member is None:
            member = ctx.author
        box = await self.bot.di.get_box(member)

        pokemon = [f"{x.id}: **{x.name}**" for x in box]
        description = "\n".join(pokemon)
        embed = discord.Embed(description=description, title=f"{member.display_name}'s Pokemon")
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @pokemon.command(aliases=["new"])
    @checks.no_pm()
    async def create(self, ctx):
        """Create a new Pokemon to add to your box"""
        try:
            check = lambda x: x.channel is ctx.channel and x.author is ctx.author
            pokemon = dict()
            await ctx.send("In any step type 'cancel' to cancel")
            await ctx.send("What will its nickname be?")
            response = await self.bot.wait_for("message", check=check, timeout=30)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelled")
                return
            else:
                pokemon["name"] = response.content

            await ctx.send("What species of Pokemon is it?")
            response = await self.bot.wait_for("message", check=check, timeout=30)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelled")
                return
            else:
                pokemon["type"] = response.content

            await ctx.send("In any order, what are its stats? (level, health, attack, defense, spatk, spdef, speed)"
                           "For example `level: 5, health: 22, attack: 56`"
                           " Type 'skip' to skip.")

            pokemon["stats"] = dict()
            valid_stats = ["level", "health", "attack", "defense", "spatk", "spdef", "speed"]
            while True:
                response = await self.bot.wait_for("message", check=check, timeout=60)
                if response.content.lower() == "cancel":
                    await ctx.send("Cancelled")
                    return
                elif response.content.lower() == "skip":
                    await ctx.send("Skipping")
                    break
                else:
                    try:
                        if "\n" in response.content:
                            res = response.content.split("\n")
                        else:
                            res = response.content.split(",")
                        for val in res:
                            key, value = val.split(": ")
                            key = key.strip().lower()
                            value = value.strip()
                            if key not in valid_stats:
                                await ctx.send(f"{key} is not a valid stat! Try again")
                                break
                            pokemon["stats"][key] = int(value)
                        else:
                            break
                    except:
                        await ctx.send("Invalid formatting! Try again")
                        continue
                    continue

            pokemon["meta"] = dict()
            await ctx.send("Any additional data? (Format like the above, for example "
                           "nature: hasty, color: brown)")

            while True:
                response = await self.bot.wait_for("message", check=check, timeout=60)
                if response.content.lower() == "cancel":
                    await ctx.send("Cancelling!")
                    return
                elif response.content.lower() == "skip":
                    await ctx.send("Skipping!")
                    break
                else:
                    try:
                        if "\n" in response.content:
                            res = response.content.split("\n")
                        else:
                            res = response.content.split(",")
                        for val in res:
                            key, value = val.split(": ")
                            key = key.strip().lower()
                            value = value.strip()
                            pokemon["meta"][key] = value
                        else:
                            break
                    except:
                        await ctx.send("Invalid formatting! Try again")
                        continue

            id = await self.bot.di.add_pokemon(ctx.author, pokemon)
            await ctx.send(f"Finished! Pokemon has been added to box with ID {id}")

        except asyncio.TimeoutError:
            await ctx.send("Timed out! Try again")
        except Exception:
            import traceback
            traceback.print_exc()

    @pokemon.command()
    @checks.no_pm()
    async def info(self, ctx, id: data.NumberConverter):
        """Get info on a Pokemon"""
        pokemon = await self.bot.di.get_pokemon(ctx.author, id)

        embed = discord.Embed(title=f"{pokemon.name}")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        embed.add_field(name="Nickname", value=pokemon.name)
        embed.add_field(name="Species", value=pokemon.type)
        embed.add_field(name="ID", value=pokemon.id)
        stats = "\n".join(f"{x}: {y}" for x, y in pokemon.stats.items())
        meta = "\n".join(f"{x}: {y}" for x, y in pokemon.meta.items())
        embed.add_field(name="Stats", value=stats)
        embed.add_field(name="Additional Info", value=meta)

        await ctx.send(embed=embed)

    @pokemon.command(aliases=["delete", "rm", "remove"])
    @checks.no_pm()
    async def release(self, ctx, id: data.NumberConverter):
        """Release a Pokemon from your box"""
        pk = await self.bot.di.remove_pokemon(ctx.author, id)
        await ctx.send(f"This Pokemon has been released! Goodbye {pk.name}!")

    @pokemon.command()
    @checks.no_pm()
    async def trade(self, ctx, your_id: data.NumberConverter, their_id: data.NumberConverter, other: discord.Member):
        """Offer a trade to a user.
        `your_id` is the ID of the Pokemon you want to give, `their_id` is the Pokemon you want from them.
        `other` being the user you want to trade with"""

        await ctx.send("Say rp!accept or rp!decline to respond to the trade!")
        try:
            resp = await self.bot.wait_for("message", timeout=60, check=lambda x: x.author == other and x.channel == ctx.channel and ctx.message.content in ["rp!accept", "rp!decline"])
        except asyncio.TimeoutError:
            await ctx.send("Failed to respond in time! Cancelling.")
            return

        if resp.content == "rp!accept":
            yud = await self.bot.db.get_user_data(ctx.author)
            tud = await self.bot.db.get_user_data(other)

            for your_pokemon in yud["box"]:
                if your_pokemon[0] == your_id:
                    break
            else:
                raise KeyError(f"{your_id} is not a valid ID!")
            yud["box"].remove(your_pokemon)
            tud["box"].append(your_pokemon)

            for their_pokemon in tud["box"]:
                if their_pokemon[0] == your_id:
                    break
            else:
                raise KeyError(f"{their_id} is not a valid ID!")
            tud["box"].remove(their_pokemon)
            yud["box"].append(their_pokemon)

            your_pokemon["id"], their_pokemon["id"] = their_pokemon["id"], your_pokemon["id"]

            await self.bot.db.update_user_data(ctx.author, yud)
            await self.bot.db.update_user_data(other, tud)
            await ctx.send(f"Trade completed! Traded {your_pokemon['name']} for {their_pokemon['name']}!")

        else:
            await ctx.send("Trade declined! Cancelling.")

    @commands.command(hidden=True)
    async def accept(self, ctx):
        pass

    @commands.command(hidden=True)
    async def decline(self, ctx):
        pass
