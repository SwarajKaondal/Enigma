"""
This file is responsible for all bot commands regarding songs such /poll for generating recommendations,
/next_song for playing next song and so on
"""
import discord
from src.get_all import *
from dotenv import load_dotenv
from discord.ext import commands
from src.utils import searchSong, random_25
from src.songs_queue import Songs_Queue
import yt_dlp as youtube_dl 

FFMPEG_OPTIONS = {
    'before_options':
    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': [
        'ffmpeg', '-i', './assets/sample.mp4', '-vn', '-f', 'mp3',
        './assets/sample.mp3'
    ]
}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}

def get_audio_source(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': 'in_playlist',
        'noplaylist': True,
        'no_warnings': True,
        'cookies': '../cookies.txt',
        'outtmpl': 'downloaded_music/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        return discord.FFmpegPCMAudio(audio_url)


class Songs(commands.Cog):
    """
    Cog for bot that handles all commands related to songs
    """

    def __init__(self, bot):
        self.bot = bot

    """
    Function for handling resume capability
    """

    @commands.command(name='resume', help='Resumes the song')
    async def resume(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send(
                "The bot was not playing anything before this. Use play command"
            )

    """
    Function for playing a custom song
    """

    @commands.command(name='play_custom', help='To play custom song')
    async def play_custom(self, ctx):
        user_message = str(ctx.message.content)
        song_name = user_message.split(' ', 1)[1]
        await self.play_song(song_name, ctx)

    """
    Function to stop playing the music
    """

    @commands.command(name='stop', help='Stops the song')
    async def stop(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    """
    Helper function for playing song on the voice channel
    """

    async def play_song(self, song_name, ctx):
        
        url = searchSong(song_name)
        print(url)
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

        # await self.stop(ctx)
        # try:
        #     server = ctx.message.guild
        #     voice_channel = server.voice_client
        #     async with ctx.typing():
        #         with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        #             info = ydl.extract_info(url, download=False)
        #             audio_url = info['url']
        #             source = await discord.FFmpegPCMAudio(audio_url)
        #             print(source)
        #             voice_channel.play(source)
        #             voice_channel.is_playing()
        #     await ctx.send('**Now playing:** {}'.format(song_name))
        # except Exception as e:
        #     await ctx.send("The bot is not connected to a voice channel.")

    """
    Helper function to handle empty song queue
    """

    async def handle_empty_queue(self, ctx):
        try:
            songs_queue
        except NameError:
            await ctx.send(
                "No recommendations present. First generate recommendations using /poll"
            )
            return True
        if songs_queue.get_len() == 0:
            await ctx.send(
                "No recommendations present. First generate recommendations using /poll"
            )
            return True
        return False

    """
    Function to play the next song in the queue
    """

    @commands.command(name='next_song', help='To play next song in queue')
    async def next_song(self, ctx):
        empty_queue = await self.handle_empty_queue(ctx)
        if not empty_queue:
            await self.play_song(songs_queue.next_song(), ctx)

    """
    Function to play the previous song in the queue
    """

    @commands.command(name='prev_song', help='To play prev song in queue')
    async def play(self, ctx):
        empty_queue = await self.handle_empty_queue(ctx)
        if not empty_queue:
            await self.play_song(songs_queue.prev_song(), ctx)

    """
    Function to pause the music that is playing
    """

    @commands.command(name='pause', help='This command pauses the song')
    async def pause(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    """
    Function to generate poll for playing the recommendations
    """

    @commands.command(name='poll', help='Poll for recommendation')
    async def poll(self, ctx):
        reactions = ['👍', '👎']
        selected_songs = []
        count = 0
        bot_message = "Select song preferences by reaction '👍' or '👎' to the choices. \nSelect 3 songs"
        await ctx.send(bot_message)
        ten_random_songs = random_25()
        for ele in zip(ten_random_songs["track_name"],
                       ten_random_songs["artist"]):
            bot_message = str(ele[0]) + " By " + str(ele[1])
            description = []
            poll_embed = discord.Embed(title=bot_message,
                                       color=0x31FF00,
                                       description=''.join(description))
            react_message = await ctx.send(embed=poll_embed)
            for reaction in reactions[:len(reactions)]:
                await react_message.add_reaction(reaction)
            res, user = await self.bot.wait_for('reaction_add')
            if (res.emoji == u'👍'):
                selected_songs.append(str(ele[0]))
                count += 1
            if (count == 3):
                bot_message = "Selected songs are : " + \
                    ' , '.join(selected_songs)
                await ctx.send(bot_message)
                break
        global songs_queue
        recommended_songs = recommend(selected_songs)
        songs_queue = Songs_Queue(recommended_songs)
        await self.play_song(songs_queue.next_song(), ctx)

    """
    Function to display all the songs in the queue
    """

    @commands.command(name='queue',
                      help='Show active queue of recommendations')
    async def queue(self, ctx):
        empty_queue = await self.handle_empty_queue(ctx)
        if not empty_queue:
            queue, index = songs_queue.return_queue()
            await ctx.send("Queue of recommendations: ")
            for i in range(len(queue)):
                if i == index:
                    await ctx.send("Currently Playing: " + queue[i])
                else:
                    await ctx.send(queue[i])

    """
    Function to shuffle songs in the queue
    """

    @commands.command(name='shuffle', help='To shuffle songs in queue')
    async def shuffle(self, ctx):
        empty_queue = await self.handle_empty_queue(ctx)
        if not empty_queue:
            songs_queue.shuffle_queue()
            await ctx.send("Playlist shuffled")

    """
    Function to add custom song to the queue
    """

    @commands.command(name='add_song', help='To add custom song to the queue')
    async def add_song(self, ctx):
        user_message = str(ctx.message.content)
        song_name = user_message.split(' ', 1)[1]
        songs_queue.add_to_queue(song_name)
        await ctx.send("Song added to queue")


"""
    Function to add the cog to the bot
"""


async def setup(client):
    await client.add_cog(Songs(client))
