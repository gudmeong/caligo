import asyncio
from datetime import datetime, timedelta
from typing import Any, ClassVar, Dict, Optional, Tuple

from pyrogram import filters, types

from caligo import command, listener, module
from caligo.core import database
from caligo.util.cache_limiter import CacheLimiter
from caligo.util.time import format_duration_td


class AFK(module.Module):
    name: ClassVar[str] = "afk"

    db: database.AsyncCollection
    cache: CacheLimiter

    async def on_load(self) -> None:
        self.db = self.bot.db[self.name.upper()]
        self.cache = CacheLimiter(ttl=60, max_value=3)

    async def get_afk_status(self) -> Tuple[Optional[Dict[str, Any]], timedelta]:
        """Query the database to retrieve the AFK setting and duration."""
        setting = await self.db.find_one({"_id": 0})
        if setting and "time" in setting:
            duration = datetime.now() - setting["time"]
            return (setting, duration)
        else:
            return (setting, timedelta(0))

    async def set_afk(self, afk: bool = False, reason: str = None) -> bool:
        """Update the AFK setting in the database."""
        afk_setting = {"afk_setting": afk, "time": datetime.now()}
        if reason is not None:
            afk_setting["reason"] = reason
        await self.db.update_one({"_id": 0}, {"$set": afk_setting}, upsert=True)
        return afk

    @listener.filters(filters.outgoing)
    async def on_message(self, message: types.Message) -> None:
        afk_setting, _ = await self.get_afk_status()
        if afk_setting and afk_setting.get("afk_setting", False):
            await self.set_afk(False)
            rest = await message.reply("__You are no longer AFK!__")
            await asyncio.sleep(5)
            await rest.delete()

    @listener.filters(
        ~filters.bot & ~filters.channel & ~filters.service & filters.private
        | filters.mentioned
    )
    async def on_message(self, ctx: command.Context, message: types.Message) -> None:
        # sanity check
        if message.from_user is None or message.from_user.is_bot:
            return
        user_id = message.from_user.id
        if await self.cache.exceeded(user_id):
            # User has exceeded rate limit, do not send AFK message
            return
        else:
            # User has not exceeded rate limit, increment the rate limit and send AFK message
            await self.cache.increment(user_id)
            afk_setting, afk_duration = await self.get_afk_status()
            if afk_setting and afk_setting.get("afk_setting", False):
                if user_id != self.bot.uid:
                    reason = afk_setting.get("reason", "No reason provided")
                    duration = format_duration_td(afk_duration)
                    reply_text = f"__I'm currently AFK!__\n**Duration:** `{duration}`"
                    if reason:
                        reply_text += f"\n**Reason:** `{reason}`"
                    return await ctx.respond(reply_text, delete_after=10)

    @command.desc("Set your AFK status")
    @command.alias("brb")
    @command.usage("afk [reason] or leave it empty", optional=True)
    async def cmd_afk(self, ctx: command.Context) -> str:
        afk_setting, _ = await self.get_afk_status()
        if afk_setting and afk_setting.get("afk_setting", False):
            await self.set_afk(False, reason=False)
            return await ctx.respond("__You are no longer AFK!__", delete_after=5)
        else:
            reason = ctx.input if ctx.input else None
            await self.set_afk(True, reason)
            return await ctx.respond("__You are now AFK!__", delete_after=5)
