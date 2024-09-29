import discord
from discord.ext import commands
import yt_dlp
import os

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

# Function to get the audio source from yt-dlp
def get_audio_source(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': 'in_playlist',
        'noplaylist': True,
        'no_warnings': True,
        'outtmpl': 'downloaded_music/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        return discord.FFmpegPCMAudio(audio_url)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='join')
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command.")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.command(name='play')
async def play(ctx, url: str):
    if not ctx.voice_client:
        await ctx.send("I'm not connected to a voice channel.")
        return

    # Check if a file is already playing
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    # Play the audio source
    audio_source = get_audio_source(url)
    ctx.voice_client.play(audio_source)
    await ctx.send(f'Now playing: {url}')

# Replace 'your_token_here' with your bot's token
bot.run('')
