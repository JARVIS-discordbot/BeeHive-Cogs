import requests
import asyncio
import discord
from redbot.core import commands
import time


class VirusTotal(commands.Cog):
    """Virus Total Inspection"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if vt_key.get("api_key") is None:
                return await ctx.send("The Virus Total API key has not been set.")
            else:
                if file_url:
                    response = requests.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url})
                    data = response.json()
                    if "permalink" in data:
                        permalink = data["permalink"]
                        await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                        await self.check_results(ctx, permalink.split('-')[1])
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                elif ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    response = requests.get(attachment.url)
                    if response.status_code != 200:
                        return await ctx.send("Failed to download the attached file.")
                    file_content = response.content
                    response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, files={"file": file_content})
                    data = response.json()
                    analysis = data['data']['id']
                    await self.check_results(ctx, analysis)
                else:
                    await ctx.send("No file URL or attachment provided.")
    async def check_results(self, ctx, analysis_id):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}
        while True:
            response = requests.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers)
            data = response.json()
            if "attributes" in data and "results" in data["attributes"]:
                results = data["attributes"]["results"]
                malicious_results = [result for result in results.values() if result["category"] == "malicious"]
                if malicious_results:
                    await ctx.send(f"The file has been detected as malicious by the following engines:")
                    for result in malicious_results:
                        await ctx.send(f"{result['engine_name']}: {result['result']}")
                    break
                else:
                    await ctx.send("The file is not detected as malicious by any scanner.")
                    break
            else:
                await asyncio.sleep(3)
