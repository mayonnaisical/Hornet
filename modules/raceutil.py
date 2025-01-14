from discord import AllowedMentions, VoiceChannel, RawReactionActionEvent, Message
from discord.ext.commands import Bot, Cog, Context, command, cooldown, BucketType
from pytimeparse.timeparse import timeparse
import asyncio, time

from components import embeds, auth, emojiUtil

import save

MODULE_NAME = __name__.split(".")[-1]

async def setup(bot: Bot):
    save.add_module_template(MODULE_NAME, {"raceVCs" : [], "readyEmote": "\uD83C\uDDF7"})
    await bot.add_cog(RaceUtilCog(bot))

async def teardown(bot: Bot):
    await bot.remove_cog("RaceUtil")

class RaceUtilCog(Cog, name="RaceUtil", description="Commands for configuring race util commands"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.readies = {} # Message ID : count

    def cog_unload(self):
        pass

    @command(help="Start a countdown (default 15s)",
         aliases=["c", "cd", "countdown"])
    @cooldown(rate=1, per=5, type=BucketType.channel)
    async def count(self, context: Context, duration: str = "15s"):
        if duration.isnumeric(): duration += "s" # For unformatted times, we expect seconds by default
        duration = timeparse(duration)
        if duration is None:
            await embeds.embed_reply(context, message="Could not parse time string! Enter in format `60s`")
            return
        exit_time = int(time.time() + duration)
        send_time = time.time()
        msg = await context.reply(f"<t:{exit_time}:R>", mention_author=False)
        await asyncio.sleep(duration - (2*(time.time() - send_time)))
        await msg.edit(content=f"{msg.content} Go!", allowed_mentions=AllowedMentions().none())

    @command(help="Ping everyone in racing vcs to tell them to pause")
    @cooldown(rate=1, per=300, type=BucketType.guild)
    async def pause(self, context: Context):
        mod_data = save.get_module_data(context.guild.id, MODULE_NAME)
        racers = []
        for vc_id in mod_data["raceVCs"]:
            vc: VoiceChannel = context.guild.get_channel(vc_id)
            racers += vc.members
        await context.send(content=f"Pause {' '.join([f'<@{r.id}>' for r in racers])}", allowed_mentions=AllowedMentions.all())

    @command(help="Creates a ready emote for *count* players.",
             aliases=["r"])
    async def ready(self, context: Context, count: int = 0):
        mod_data = save.get_module_data(context.guild.id, MODULE_NAME)
        emoji = mod_data["readyEmote"]
        message = await context.reply(f"{emoji}")
        if count > 0:
            self.readies[message.id] = count
        await message.add_reaction(emoji)

    @command(help="Add a race VC")
    @auth.check_admin
    async def addRaceVC(self, ctx: Context, channel: VoiceChannel):
        mod_data = save.get_module_data(ctx.guild.id, MODULE_NAME)
        if channel.id in mod_data["raceVCs"]:
            await embeds.embed_reply(ctx, message=f"Voice channel is already set as a race VC!")
            return
        mod_data["raceVCs"].append(channel.id)
        save.save()
        await embeds.embed_reply(ctx, message=f"Voice channel {channel.jump_url} set as a race VC")

    @command(help="Remove a race vc")
    @auth.check_admin
    async def removeRaceVC(self, ctx: Context, channel: VoiceChannel):
        mod_data = save.get_module_data(ctx.guild.id, MODULE_NAME)
        mod_data["raceVCs"].remove(channel.id)
        save.save()
        await embeds.embed_reply(ctx, message=f"Race channel {channel.jump_url} removed")

    @command(help="Sets the emote for ;ready")
    @auth.check_admin
    async def setReadyEmote(self, ctx: Context, emote: str):
        emoji = await emojiUtil.to_emoji(ctx, emote)
        emoji_str = emojiUtil.to_string(emoji)
        mod_data = save.get_module_data(ctx.guild.id, MODULE_NAME)
        mod_data["readyEmote"] = emoji_str
        save.save()
        await embeds.embed_reply(ctx, message=f"Ready emote set to {emoji_str}")

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.message_id not in self.readies: return
        if payload.user_id == self.bot.user.id: return

        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        refstring = emojiUtil.to_string(payload.emoji)
        reactions = list(filter(lambda x: emojiUtil.to_string(x.emoji) == refstring, message.reactions))
        reaction = reactions[0]

        if reaction.count > self.readies[payload.message_id]:
            exit_time = int(time.time() + 15)
            send_time = time.time()
            msg = await message.reply(f"<t:{exit_time}:R>", mention_author=False)
            await asyncio.sleep(15 - (2*(time.time() - send_time)))
            await msg.edit(content=f"{msg.content} Go!", allowed_mentions=AllowedMentions().none())
            self.readies.pop(payload.message_id)