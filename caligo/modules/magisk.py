import asyncio
from typing import Any, ClassVar, Dict, List

from caligo import command, listener, module


class Magisk(module.Module):
    """A module for fetching information about Magisk."""

    name: ClassVar[str] = "Magisk"
    disabled: ClassVar[bool] = False
    helpable: ClassVar[bool] = True

    async def fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data from the specified URL.

        Args:
            url (str): The URL to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data as a dictionary.

        Raises:
            Exception: If the response has an unexpected mimetype.
        """
        async with self.bot.http.get(url) as response:
            if response.headers["Content-Type"] == "application/json":
                return await response.json()
            raise Exception(f'Unexpected mimetype: {response.headers["Content-Type"]}')
            return None

    @command.desc("Get the version and download link of Magisk from different sources")
    @command.usage("magisk")
    async def cmd_magisk(self, ctx: command.Context) -> None:
        """Get the version and download link of Magisk from different sources.

        Args:
            ctx (command.Context): The command context.
        """
        urls = [
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json",
            "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/debug.json",
        ]
        tasks = [self.fetch_json(url) for url in urls]
        json_data_list: List[Dict[str, Any]] = await asyncio.gather(*tasks)

        # Access the data using the keys
        for json_data in json_data_list:
            magisk_version = json_data["magisk"]["version"]
            magisk_link = json_data["magisk"]["link"]
            await ctx.respond(
                f"Magisk version: {magisk_version}\nDownload link: {magisk_link}"
            )
