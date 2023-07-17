import asyncio
from typing import ClassVar

from caligo import command, listener, module


class Magisk(module.Module):
    name: ClassVar[str] = "Magisk"
    disabled: ClassVar[bool] = False
    helpable: ClassVar[bool] = True

    async def fetch_json(self, url):
        async with self.bot.http.get(url) as response:
            return await response.json()

    @command.desc("Get the version of Magisk from different sources")
    @command.usage("magisk")
    async def cmd_magisk(self, ctx: command.Context) -> None:
        urls = [
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/debug.json",
        ]
        tasks = [self.fetch_json(url) for url in urls]
        json_data_list = await asyncio.gather(*tasks)

        # Access the data using the keys
        for json_data in json_data_list:
            magisk_version = json_data["magisk"]["version"]
            await ctx.respond(f"Magisk version: {magisk_version}")
