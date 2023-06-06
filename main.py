import math
import os
import os.path
import random
import re
import datetime
import json
from discord.interactions import Interaction
import requests
import asyncio
import discord
from discord import ui
import openai
from discord.ext import tasks, commands
import sqlite3
import urllib.request
from osu_apy_v2 import OsuApiV2
from rosu_pp_py import Beatmap, Calculator
import aiohttp
from server import keep_alive

TOKEN = os.environ['discord_TOKEN']
api = OsuApiV2(client_id=os.environ['client_id'],
               client_secret=os.environ['client_secret'])
api_key = os.environ['osuAPI_KEY']

openai.api_key = os.environ['openAI_secret']

dbname = 'osubot.db'

conn = sqlite3.connect(dbname)

cur = conn.cursor()

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='.', intents=intents)


class Buttons(discord.ui.View):

  def __init__(self, *, timeout=30):
    super().__init__(timeout=timeout)


class osutop_modal(ui.Modal, title='Enter Page Number'):
  answer = ui.TextInput(label='Enter Target Page Number',
                        style=discord.TextStyle.short,
                        placeholder="Page number",
                        default="1",
                        max_length=20)

  async def on_submit(self, inter: Interaction):
    cur.execute(
      "SELECT user_id, i, max, mode FROM osutop_temp WHERE message_id = ?",
      (inter.message.id, ))

    for r in cur:
      pass

    try:
      user_id = r[0]
      i = int(self.answer.value)
      max = r[2]
      mode = r[3]

      if i > max:
        i = max
      elif i < 0:
        i = 1
    except:
      return await inter.response.edit_message()

    cur.execute(
      "UPDATE osutop_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
        i,
        inter.message.id,
      ))
    conn.commit()

    view = await osutop_button(i, max)
    await inter.response.edit_message(view=view)

    embed = await _osu_top(user_id, i, mode)
    await inter.followup.edit_message(embed=embed[0],
                                      message_id=inter.message.id)


class recent_modal(ui.Modal, title='Enter Page Number'):
  answer = ui.TextInput(label='Enter Target Page Number',
                        style=discord.TextStyle.short,
                        placeholder="Page number",
                        default="1",
                        max_length=20)

  async def on_submit(self, inter: discord.Interaction):
    cur.execute(
      "SELECT username, user_id, i, max, mode FROM rs_temp WHERE message_id = ?",
      (inter.message.id, ))

    for r in cur:
      pass

    try:
      user_id = r[1]
      i = int(self.answer.value) - 1
      max = r[3]
      mode = r[4]

      if i > max:
        i = max
      elif i < 0:
        i = 0
    except:
      return await inter.response.edit_message()

    cur.execute(
      "UPDATE rs_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
        i,
        inter.message.id,
      ))
    conn.commit()

    view = await recent_button(i, max)
    await inter.response.edit_message(view=view)

    embed = await _recent(user_id, i, mode)
    await inter.followup.edit_message(embed=embed, message_id=inter.message.id)


@bot.event
async def on_ready():
  print('//////////////////////////////')
  print('//// OSUBOT HAS LOGGED IN ////')
  print('//////////////////////////////')

  count = len(bot.guilds)
  print("\nbotが利用されているサーバ数：{}\n".format(count))
  await bot.change_presence(activity=discord.Game(name="osu!"))

  flag_fpath = "data/latest-notice.json"
  with open(flag_fpath, "r") as json_file:
    latest_notice = json.load(json_file)

  t_delta = datetime.timedelta(hours=9)
  JST = datetime.timezone(t_delta, 'JST')
  now = datetime.datetime.now(JST)

  if latest_notice["year"] != now.year or latest_notice[
      "month"] != now.month or latest_notice["day"] != now.day:
    await new_beatmap()

  new_beatmap.start()
  add_beatmap.start()


@bot.event
async def on_guild_join(self):
  count = len(bot.guilds)
  print("\nサーバに参加しました")
  print("botが利用されているサーバ数：{}\n".format(count))


@bot.command()
async def sasuke(ctx):

  famous_quote = [
    'これだけは言えることなんですけど、俺には……SASUKEしかないんですよ',
    'SASUKEにね、敬意を示さな駄目ですよ。皆甘く考え過ぎとるから。',
    'SASUKEが何十年続こうが、見届けていきたい気持ちがあります',
    '俺もうボロボロになって潰れても構わないんですよ、ここで。そのまま死のうが寝たきりになろうが。それだけ自分の生き方に自信があるというか。',
    '俺の作った看板が重すぎる…',
    'SASUKE難しいっすね',
    '寝てる時もサスケのこと考える',
    '俺の人生ですかね。目標を持って今までやってきたこと、それが人生になっているし、これから先もたぶん、死ぬまでSASUKEと関わっていく',
    'SASUKEを楽しいと思ったことは一度もない',
    'もし叶うなら、もう一度、第１回大会から出たい',
    '夢を諦めるわけにはいきません',
    '誰も俺がクリアすると思ってないだろうけど、山田勝己はまだ死んでいないというところを見せたい',
    '自分の気持ちの続く限りは、挑戦続けたい',
    '仲間のクリアは勇気を与え、仲間のリタイアは力を与える',
    '年齢を言い訳にしたら、SASUKEに出場する資格はない',
    '負けたくないっていう……ただそれだけです',
    'この反り加減では無理',
    '長野誠が俺の分までやってくれると思います。本当は一緒に行きたかったですけど申し訳ないです。',
    '完全制覇という昔からの思いは置いていくので若い奴らが必ず取り戻してくれると思います',
    'オールスターズっていうのはSASUKEがすごく大好きで、ずっと十何年間も一緒に戦い続けて来て、いいメンバーに巡り会えて、俺はすごい幸せです',
  ]

  length = len(famous_quote)

  r = random.randrange(length)

  await ctx.send("**{}**".format(famous_quote[r]))

  user = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.sasuke [ {} ]".format(user))


@bot.command()
async def osuset(ctx, *, arg):
  try:
    user_id = api.get_user_id(arg)
    username = api.get_username(user_id)
    profile = api.get(f"/users/{user_id}/osu")
  except:
    return await ctx.send("**プレイヤーが見つかりませんでした。**")

  jsonData = profile.json()

  flag_url = 'https://osu.ppy.sh/images/flags/{}.png'.format(
    jsonData['country_code'])

  playmode = jsonData['playmode']

  cur = conn.cursor()
  cur.execute(
    'INSERT INTO user(discord_user_id, osu_username, osu_user_id, playmode) values(?, ?, ?, ?) ON CONFLICT(discord_user_id) DO UPDATE SET osu_username = ?, osu_user_id = ?, playmode = ?',
    (ctx.author.id, username, user_id, playmode, username, user_id, playmode),
  )
  conn.commit()

  embed = await _osu_profile(ctx, username, playmode)
  embed.color = discord.Colour.red()
  embed.set_author(
    name="{}'s osu profile has been registered".format(username),
    url="https://osu.ppy.sh/users/{}".format(user_id),
    icon_url=flag_url)
  await ctx.send(embed=embed)
  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.osuset {} [ {} ]".format(username, cuser))


@bot.command()
async def osu(ctx, *arg):

  username = ""
  mode = ""

  if arg:
    mode = await fetch_mode(arg)
    username = await fetch_user(arg)
  else:
    mode = await fetch_mode(arg)

  if username == "":

    r = [""]
    cur = conn.cursor()
    id = ctx.author.id
    cur.execute(
      'SELECT osu_user_id, playmode FROM user WHERE discord_user_id = ?',
      (id, ))

    for r in cur:
      pass
    if r[0] == '':
      return await ctx.send("**アカウントを登録してください！\n.osuset <ユーザー名>**")

    user_id = r[0]
    if mode == "":
      mode = r[1]

    profile = api.get(f"/users/{user_id}/osu")
    jsonData = profile.json()

    username = jsonData['username']

    cur.execute('UPDATE user SET osu_username = ? WHERE discord_user_id = ?', (
      username,
      id,
    ))
    conn.commit()

  else:
    if mode == "":
      mode = "osu"
    try:
      user_id = api.get_user_id(username)
      username = api.get_username(user_id)
    except:
      return await ctx.send("**プレイヤーが見つかりませんでした。**")

  embed = await _osu_profile(ctx, username, mode)
  await ctx.send(embed=embed)

  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.osu {} [ {} ]".format(username, cuser))


async def _osu_profile(ctx, username, mode):
  try:
    user_id = api.get_user_id(username)
    game_id = api.get_username(user_id)
    profile = api.get(f"/users/{user_id}/{mode}")
  except:
    return await ctx.send("**プレイヤーが見つかりませんでした。**")

  jsonData = profile.json()

  flag_url = 'https://osu.ppy.sh/images/flags/{}.png'.format(
    jsonData['country_code'])
  avatar = jsonData['avatar_url']
  globalrank = jsonData['statistics']['global_rank']

  if type(globalrank) == int:
    countryrank = jsonData['statistics']['country_rank']

  try:
    rank_highest = jsonData['rank_highest']['rank']
    rank_highest_at = jsonData['rank_highest']['updated_at']
    temp = re.findall(r"\d+", rank_highest_at)
    datetime_rank_highest = datetime.datetime(int(temp[0]), int(temp[1]),
                                              int(temp[2]), int(temp[3]),
                                              int(temp[4]), int(temp[5]))
    datetime_rank_highest = datetime.datetime.timestamp(datetime_rank_highest)
  except:
    rank_highest_at = None

  rank_SSH = jsonData['statistics']['grade_counts']['ssh']
  rank_SH = jsonData['statistics']['grade_counts']['sh']
  rank_SS = jsonData['statistics']['grade_counts']['ss']
  rank_S = jsonData['statistics']['grade_counts']['s']
  rank_A = jsonData['statistics']['grade_counts']['a']
  pp = jsonData['statistics']['pp']
  acc = jsonData['statistics']['hit_accuracy']
  level = jsonData['statistics']['level']['current']
  levelplus = jsonData['statistics']['level']['progress']
  playcount = jsonData['statistics']['play_count']
  playtime = jsonData['statistics']['play_time'] / 3600

  if type(globalrank) != int:
    if rank_highest_at == None:
      embed = discord.Embed(
        description=
        "▸ **Global Ranking**: #-\n▸ **Country Ranking**: #-\n▸ **Peak Rank**: #-\n▸ **Level**: {:d} + {:.2f}%\n▸ **PP**: {:,.2f} **ACC**: {:.2f}%\n▸ **Playcount**: {:,d} ({:,.0f}hrs)\n▸ **Ranks**: **SSH** {:d} **SS** {:d} **SH** {:d} **S** {:d} **A** {:d}"
        .format(level, levelplus, pp, acc, playcount, playtime, rank_SSH,
                rank_SS, rank_SH, rank_S, rank_A),
        color=discord.Colour.green())
    else:
      embed = discord.Embed(
        description=
        "▸ **Global Ranking**: #-\n▸ **Country Ranking**: #-\n▸ **Peak Rank**: #{:,d} achieved <t:{}:R>\n▸ **Level**: {:d} + {:.2f}%\n▸ **PP**: {:,.2f} **ACC**: {:.2f}%\n▸ **Playcount**: {:,d} ({:,.0f}hrs)\n▸ **Ranks**: **SSH** {:d} **SS** {:d} **SH** {:d} **S** {:d} **A** {:d}"
        .format(rank_highest, int(datetime_rank_highest), level, levelplus, pp,
                acc, playcount, playtime, rank_SSH, rank_SS, rank_SH, rank_S,
                rank_A),
        color=discord.Colour.green())
  else:
    embed = discord.Embed(
      description=
      "▸ **Global Ranking**: #{:,d}\n▸ **Country Ranking**: #{:,d}\n▸ **Peak Rank**: #{:,d} achieved <t:{}:R>\n▸ **Level**: {:d} + {:.2f}%\n▸ **PP**: {:,.2f} **ACC**: {:.2f}%\n▸ **Playcount**: {:,d} ({:,.0f}hrs)\n▸ **Ranks**: **SSH** {:d} **SS** {:d} **SH** {:d} **S** {:d} **A** {:d}"
      .format(globalrank, countryrank, rank_highest,
              int(datetime_rank_highest), level, levelplus, pp, acc, playcount,
              playtime, rank_SSH, rank_SS, rank_SH, rank_S, rank_A),
      color=discord.Colour.green())
  embed.set_thumbnail(url=avatar)
  mode = await _mode(mode)
  embed.set_author(name=f"osu! {mode} Profile for {game_id}",
                   url=f"https://osu.ppy.sh/users/{user_id}",
                   icon_url=flag_url)

  return embed


@bot.command()
async def osudel(ctx):
  user = '0'
  cur = conn.cursor()
  id = ctx.author.id
  cur.execute('SELECT osu_username FROM user WHERE discord_user_id = ?',
              (id, ))

  for row in cur:
    user = row
  if user[0] == '0':
    return await ctx.send("**すでに削除されています！！**")

  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.osudel {} [ {} ]".format(user[0], cuser))

  cur.execute('DELETE FROM user WHERE discord_user_id = ?', (id, ))
  conn.commit()
  await ctx.send("**アカウントの紐付けが解除されました。**")


@bot.command()
async def rs(ctx, *arg):

  index = 0
  cur = conn.cursor()

  username = ""
  mode = ""
  r = [""]

  if arg:
    mode = await fetch_mode(arg)
    username = await fetch_user(arg)
  else:
    mode = await fetch_mode(arg)

  if username == "":

    cur = conn.cursor()
    id = ctx.author.id
    cur.execute(
      'SELECT osu_user_id, playmode FROM user WHERE discord_user_id = ?',
      (id, ))

    for r in cur:
      pass
    if r[0] == "":
      return await ctx.send("**アカウントを登録してください！\n.osuset <ユーザー名>**")

    user_id = r[0]
    if mode == "":
      mode = r[1]

    profile = api.get(f"/users/{user_id}/osu")
    jsonData = profile.json()

    username = jsonData['username']

    cur.execute('UPDATE user SET osu_username = ? WHERE discord_user_id = ?', (
      username,
      id,
    ))
    conn.commit()

  else:
    if mode == "":
      mode = "osu"
    try:
      user_id = api.get_user_id(username)
      username = api.get_username(user_id)
    except:
      return await ctx.send("**プレイヤーが見つかりませんでした。**")

  recent = api.get(
    f"/users/{user_id}/scores/recent?include_fails=1&limit=50&mode={mode}")
  jsonData = recent.json()

  if not jsonData:
    cuser = await bot.fetch_user(ctx.author.id)
    print("コマンドが使用されました：.rs {} [ {} ]".format(username, cuser))
    return await ctx.send("**最近のプレイはありません！！**")

  embed = await _recent(user_id, index, mode)

  count = 0
  flag = True
  while (flag == True):
    try:
      jsonData[count]['beatmap']['id'] = jsonData[count]['beatmap']['id']
      count += 1
    except:
      flag = False

  view = await recent_button(index, count - 1)

  gamemode = await _mode(mode)

  message_id = await ctx.send(
    f"**Recent osu! {gamemode} Play for {username}:**", embed=embed, view=view)
  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.rs {} [ {} ]".format(username, cuser))

  cur.execute(
    "INSERT INTO rs_temp(message_id, user_id, username, i, max, mode) VALUES(?, ?, ?, ?, ?, ?)",
    (
      message_id.id,
      user_id,
      username,
      index,
      count - 1,
      mode,
    ))
  conn.commit()

  inter = True

  while inter == True:
    cur.execute("UPDATE rs_temp SET inter = 'False' WHERE message_id = ?",
                (str(message_id.id), ))
    conn.commit()
    await asyncio.sleep(30)
    cur.execute("SELECT inter FROM rs_temp WHERE message_id = ?",
                (str(message_id.id), ))
    for r in cur:
      if r[0] == "False":
        inter = False
      else:
        inter = True
  await message_id.edit(view=None)
  cur.execute("DELETE FROM rs_temp WHERE message_id = ?",
              (str(message_id.id), ))
  conn.commit()
  print("ボタンを削除しました：.rs {} [ {} ]".format(username, cuser))


async def _recent(user_id, i, mode):

  datetime_recent_ = []

  recent = api.get(
    f"/users/{user_id}/scores/recent?include_fails=1&limit={i + 1}&mode={mode}"
  )
  jsonData = recent.json()

  beatmap_id = jsonData[i]['beatmap']['id']
  mapset_id = jsonData[i]['beatmap']['beatmapset_id']

  beatmap = api.get(f"/beatmaps/{beatmap_id}")
  mapData = beatmap.json()

  objects = mapData['count_circles'] + mapData['count_sliders'] + mapData[
    'count_spinners']

  avatar = jsonData[i]['user']['avatar_url']

  mod = jsonData[i]['mods']
  acc = round(jsonData[i]['accuracy'] * 100, 2)
  score = jsonData[i]['score']
  combo = jsonData[i]['max_combo']
  maxcombo = mapData['max_combo']
  count_300 = jsonData[i]['statistics']['count_300']
  count_100 = jsonData[i]['statistics']['count_100']
  count_50 = jsonData[i]['statistics']['count_50']
  count_miss = jsonData[i]['statistics']['count_miss']
  rank = jsonData[i]['rank']
  title = jsonData[i]['beatmapset']['title']
  artist = jsonData[i]['beatmapset']['artist']
  version = jsonData[i]['beatmap']['version']
  difficulty = jsonData[i]['beatmap']['difficulty_rating']
  created_at = jsonData[i]['created_at']

  flag_url = 'https://osu.ppy.sh/images/flags/{}.png'.format(
    jsonData[0]['user']['country_code'])

  datetime_recent_ = re.findall(r"\d+", created_at)
  datetime_recent = datetime.datetime(int(datetime_recent_[0]),
                                      int(datetime_recent_[1]),
                                      int(datetime_recent_[2]),
                                      int(datetime_recent_[3]),
                                      int(datetime_recent_[4]),
                                      int(datetime_recent_[5]))
  pp = await pp_calc_user(beatmap_id, rank, mod, acc, combo, maxcombo,
                          count_300, count_100, count_50, count_miss, objects,
                          mode)

  mods = re.sub(r"[^a-zA-Z,]", "", str(mod))
  if mods == "":
    mod = "No Mod"
  else:
    mod = mods

  pp_curr = round(pp['pp_curr'], 2)
  difficulty = pp['difficulty']
  pp_fc = pp['pp_fc']

  if pp_fc is None:
    embed = discord.Embed(
      description=
      "▸ Rank: **{}**\n▸ Performance: **{:.2f}PP**\n▸ Accuracy: **{:.2f}%**\n▸ Score: {:,d}\n▸ Combo: x{}/{} [{}/{}/{}/{}]"
      .format(rank, pp_curr, acc, score, combo, maxcombo, count_300, count_100,
              count_50, count_miss),
      color=discord.Colour.green())
    embed.set_author(name='{} - {} [{}] + {} [{:.2f}★]'.format(
      artist, title, version, mod, difficulty),
                     url="https://osu.ppy.sh/beatmaps/{}".format(beatmap_id),
                     icon_url=str(avatar))
    embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(mapset_id))

  elif rank != 'F':
    pp_fc = pp['pp_fc']
    acc_fc = pp['acc_fc'] / 100
    embed = discord.Embed(
      description=
      "▸ Rank: **{}**\n▸ Performance: **{:.2f}PP** ({:.2f}PP for {:.2%} FC)\n▸ Accuracy: **{:.2f}%**\n▸ Score: {:,d}\n▸ Combo: x{}/{} [{}/{}/{}/{}]"
      .format(rank, pp_curr, pp_fc, acc_fc, acc, score, combo, maxcombo,
              count_300, count_100, count_50, count_miss),
      color=discord.Colour.green())
    embed.set_author(name='{} - {} [{}] + {} [{:.2f}★]'.format(
      artist, title, version, mod, difficulty),
                     url="https://osu.ppy.sh/beatmaps/{}".format(beatmap_id),
                     icon_url=str(avatar))
    embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(mapset_id))

  else:
    pp_fc = pp['pp_fc']
    acc_fc = pp['acc_fc'] / 100
    map_completion = pp['map_completion']
    embed = discord.Embed(
      description=
      "▸ Rank: **{}** ({:.1%})\n▸ Performance: **{:.2f}PP** ({:.2f}PP for {:.2%} FC)\n▸ Accuracy: **{:.2f}%**\n▸ Score: {:,d}\n▸ Combo: x{}/{} [{}/{}/{}/{}]"
      .format(rank, map_completion, pp_curr, pp_fc, acc_fc, acc, score, combo,
              maxcombo, count_300, count_100, count_50, count_miss),
      color=discord.Colour.green())
    embed.set_author(name='{} - {} [{}] + {} [{:.2f}★]'.format(
      artist, title, version, mod, difficulty),
                     url="https://osu.ppy.sh/beatmaps/{}".format(beatmap_id),
                     icon_url=str(avatar))
    embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(mapset_id))

  embed.timestamp = datetime_recent
  embed.set_footer(text="Score Set", icon_url=flag_url)

  return embed


async def recent_button(i, max):
  view = discord.ui.View()
  if i == 0:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="recent_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="recent_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_last"))
  elif i == max:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="recent_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="recent_last"))
  else:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="recent_last"))

  return view


async def recent_top(inter: discord.Interaction):
  cur.execute(
    "SELECT username, user_id, i, max, mode FROM rs_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[1]
  i = 0
  max = r[3]
  mode = r[4]

  cur.execute("UPDATE rs_temp SET i = ?, inter = 'True' WHERE message_id = ?",
              (
                i,
                inter.message.id,
              ))
  conn.commit()

  view = await recent_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _recent(user_id, i, mode)
  await inter.followup.edit_message(embed=embed, message_id=inter.message.id)


async def recent_prv(inter: discord.Interaction):
  cur.execute(
    "SELECT username, user_id, i, max, mode FROM rs_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[1]
  i = r[2] - 1
  max = r[3]
  mode = r[4]

  cur.execute("UPDATE rs_temp SET i = ?, inter = 'True' WHERE message_id = ?",
              (
                i,
                inter.message.id,
              ))
  conn.commit()

  view = await recent_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _recent(user_id, i, mode)
  await inter.followup.edit_message(embed=embed, message_id=inter.message.id)


async def recent_next(inter: discord.Interaction):
  cur.execute(
    "SELECT username, user_id, i, max, mode FROM rs_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[1]
  i = r[2] + 1
  max = r[3]
  mode = r[4]

  cur.execute("UPDATE rs_temp SET i = ?, inter = 'True' WHERE message_id = ?",
              (
                i,
                inter.message.id,
              ))
  conn.commit()

  view = await recent_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _recent(user_id, i, mode)
  await inter.followup.edit_message(embed=embed, message_id=inter.message.id)


async def recent_last(inter: discord.Interaction):
  cur.execute(
    "SELECT username, user_id, i, max, mode FROM rs_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[1]
  max = r[3]
  i = max
  mode = r[4]

  cur.execute("UPDATE rs_temp SET i = ?, inter = 'True' WHERE message_id = ?",
              (
                i,
                inter.message.id,
              ))
  conn.commit()

  view = await recent_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _recent(user_id, i, mode)
  await inter.followup.edit_message(embed=embed, message_id=inter.message.id)


async def recent_select(inter: discord.Interaction):
  modal = recent_modal()
  await inter.response.send_modal(modal)


@bot.command()
async def osutop(ctx, *arg):

  cur = conn.cursor()

  username = ""
  mode = ""

  if arg:
    mode = await fetch_mode(arg)
    username = await fetch_user(arg)
  else:
    mode = await fetch_mode(arg)

  if username == "":

    r = [""]
    cur = conn.cursor()
    id = ctx.author.id
    cur.execute(
      'SELECT osu_user_id, playmode FROM user WHERE discord_user_id = ?',
      (id, ))

    for r in cur:
      pass
    if r[0] == '':
      return await ctx.send("**アカウントを登録してください！\n.osuset <ユーザー名>**")

    user_id = r[0]
    if mode == "":
      mode = r[1]

    profile = api.get(f"/users/{user_id}/osu")
    jsonData = profile.json()

    username = jsonData['username']

    cur.execute('UPDATE user SET osu_username = ? WHERE discord_user_id = ?', (
      username,
      id,
    ))
    conn.commit()

  else:
    if mode == "":
      mode = "osu"
    try:
      user_id = api.get_user_id(username)
      username = api.get_username(user_id)
    except:
      return await ctx.send("**プレイヤーが見つかりませんでした。**")

  res = api.get(f"/users/{user_id}/scores/best?mode=osu&limit=100&mode={mode}")
  jsonData = res.json()
  max = len(jsonData) // 5
  if len(jsonData) % 5 != 0:
    max += 1

  embed = await _osu_top(user_id, 1, mode)
  view = await osutop_button(1, max)
  if embed[1] == True:
    return await ctx.send(embed=embed[0])

  message_id = await ctx.send(embed=embed[0], view=view)
  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.osutop {} [ {} ]".format(username, cuser))

  cur.execute(
    "INSERT INTO osutop_temp(message_id, user_id, username, i, max, mode) VALUES(?, ?, ?, ?, ?, ?)",
    (
      message_id.id,
      user_id,
      username,
      1,
      max,
      mode,
    ))
  conn.commit()

  inter = True

  while inter == True:
    cur.execute("UPDATE osutop_temp SET inter = 'False' WHERE message_id = ?",
                (str(message_id.id), ))
    conn.commit()
    await asyncio.sleep(30)
    cur.execute("SELECT inter FROM osutop_temp WHERE message_id = ?",
                (str(message_id.id), ))
    for r in cur:
      if r[0] == "False":
        inter = False
      else:
        inter = True
  await message_id.edit(view=None)
  cur.execute("DELETE FROM osutop_temp WHERE message_id = ?",
              (str(message_id.id), ))
  conn.commit()
  print("ボタンを削除しました：.osutop {} [ {} ]".format(username, cuser))


async def _osu_top(user_id, page, mode):

  top = ""

  try:
    game_id = api.get_username(user_id)
    res = api.get(
      f"/users/{user_id}/scores/best?mode=osu&limit={page * 5}&mode={mode}")
    profile = api.get(f"/users/{user_id}/osu")
  except:
    embed = discord.Embed(title="Error", description="**プレイヤーが見つかりませんでした。**")
    error = True
    return embed, error

  jsonData = res.json()
  icon = profile.json()

  flag_url = 'https://osu.ppy.sh/images/flags/{}.png'.format(
    icon['country_code'])

  try:
    avatar = jsonData[0]['user']['avatar_url']
  except:
    embed = discord.Embed(title="Error", description="**ベストパフォーマンスが存在しません！！**")
    error = True
    return embed, error

  if len(jsonData) < page * 5:
    page = len(jsonData) // 5
    if len(jsonData) % 5 != 0:
      page += 1

  for i in range((page - 1) * 5, len(jsonData)):
    beatmap = api.get(f"/beatmaps/{jsonData[i]['beatmap']['id']}")
    jsonmap = beatmap.json()

    mods = re.sub(r"[^a-zA-Z]", "", str(jsonData[i]['mods']))
    if mods == "":
      mods = "NM"

    acc = jsonData[i]['accuracy'] * 100
    combo = jsonData[i]['max_combo']
    maxcombo = jsonmap['max_combo']
    objects = jsonmap['count_circles'] + jsonmap['count_sliders'] + jsonmap[
      'count_spinners']
    timeago = jsonData[i]['created_at']
    datetime_recent_ = re.findall(r"\d+", timeago)
    datetime_recent = datetime.datetime(int(datetime_recent_[0]),
                                        int(datetime_recent_[1]),
                                        int(datetime_recent_[2]),
                                        int(datetime_recent_[3]),
                                        int(datetime_recent_[4]),
                                        int(datetime_recent_[5]))
    datetime_recent = datetime.datetime.timestamp(datetime_recent)

    pp = await pp_calc_user(jsonData[i]['beatmap']['id'], jsonData[i]['rank'],
                            jsonData[i]['mods'], acc, combo, maxcombo,
                            jsonData[i]['statistics']['count_300'],
                            jsonData[i]['statistics']['count_100'],
                            jsonData[i]['statistics']['count_50'],
                            jsonData[i]['statistics']['count_miss'], objects,
                            mode)

    diff = pp['difficulty']
    pp_fc = pp['pp_fc']

    if pp['pp_fc'] is None:
      top += "**{}**. **[{} - {} [{}]]({}) + {}** [{:.2f}★]\n▸ Rank: **{}** \n▸ Performance: **{:.2f}PP**\n▸ Accuracy: **{:.2f}%**\n▸ Score: {:,d}\n▸ Combo: x{}/{} [{}/{}/{}/{}]\n▸ Score Set: <t:{}:R>\n\n".format(
        i + 1, jsonData[i]['beatmapset']['artist'],
        jsonData[i]['beatmapset']['title'], jsonData[i]['beatmap']['version'],
        jsonData[i]['beatmap']['url'], mods, diff, jsonData[i]['rank'],
        jsonData[i]['pp'], acc, jsonData[i]['score'], combo, maxcombo,
        jsonData[i]['statistics']['count_300'],
        jsonData[i]['statistics']['count_100'],
        jsonData[i]['statistics']['count_50'],
        jsonData[i]['statistics']['count_miss'], int(datetime_recent))
    else:
      acc_fc = pp['acc_fc'] / 100
      top += "**{}**. **[{} - {} [{}]]({}) + {}** [{:.2f}★]\n▸ Rank: **{}** \n▸ Performance: **{:.2f}PP** ({:.2f}PP for {:.2%} FC)\n▸ Accuracy: **{:.2f}%**\n▸ Score: {:,d}\n▸ Combo: x{}/{} [{}/{}/{}/{}]\n▸ Score Set: <t:{}:R>\n\n".format(
        i + 1, jsonData[i]['beatmapset']['artist'],
        jsonData[i]['beatmapset']['title'], jsonData[i]['beatmap']['version'],
        jsonData[i]['beatmap']['url'], mods, diff, jsonData[i]['rank'],
        jsonData[i]['pp'], pp_fc, acc_fc, acc, jsonData[i]['score'], combo,
        maxcombo, jsonData[i]['statistics']['count_300'],
        jsonData[i]['statistics']['count_100'],
        jsonData[i]['statistics']['count_50'],
        jsonData[i]['statistics']['count_miss'], int(datetime_recent))

  embed = discord.Embed(description=top, color=discord.Colour.green())

  mode = await _mode(mode)

  embed.set_author(name=f"Top osu! {mode} Profile for {game_id}",
                   url="https://osu.ppy.sh/users/{}".format(user_id),
                   icon_url=flag_url)
  embed.set_thumbnail(url=avatar)

  error = False
  return embed, error


async def osutop_button(page, max):

  view = discord.ui.View()
  if page == 1:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="osutop_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="osutop_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_last"))
  elif page == max:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="osutop_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        disabled=True,
                        custom_id="osutop_last"))
  else:
    view.add_item(
      discord.ui.Button(label="◂◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_top"))
    view.add_item(
      discord.ui.Button(label="◂",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_prv"))
    view.add_item(
      discord.ui.Button(label="*",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_select"))
    view.add_item(
      discord.ui.Button(label="▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_next"))
    view.add_item(
      discord.ui.Button(label="▸▸",
                        style=discord.ButtonStyle.gray,
                        custom_id="osutop_last"))

  return view


async def osutop_top(inter: discord.Interaction):
  cur.execute(
    "SELECT user_id, i, max, mode FROM osutop_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[0]
  i = 1
  max = r[2]
  mode = r[3]

  cur.execute(
    "UPDATE osutop_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
      i,
      inter.message.id,
    ))
  conn.commit()

  view = await osutop_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _osu_top(user_id, i, mode)
  await inter.followup.edit_message(embed=embed[0],
                                    message_id=inter.message.id)


async def osutop_prv(inter: discord.Integration):
  cur.execute(
    "SELECT user_id, i, max, mode FROM osutop_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[0]
  i = r[1] - 1
  max = r[2]
  mode = r[3]

  cur.execute(
    "UPDATE osutop_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
      i,
      inter.message.id,
    ))
  conn.commit()

  view = await osutop_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _osu_top(user_id, i, mode)
  await inter.followup.edit_message(embed=embed[0],
                                    message_id=inter.message.id)


async def osutop_next(inter: discord.Interaction):
  cur.execute(
    "SELECT user_id, i, max, mode FROM osutop_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[0]
  i = r[1] + 1
  max = r[2]
  mode = r[3]

  cur.execute(
    "UPDATE osutop_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
      i,
      inter.message.id,
    ))
  conn.commit()

  view = await osutop_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _osu_top(user_id, i, mode)
  await inter.followup.edit_message(embed=embed[0],
                                    message_id=inter.message.id)


async def osutop_last(inter: discord.Interaction):
  cur.execute(
    "SELECT user_id, i, max, mode FROM osutop_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  user_id = r[0]
  max = r[2]
  i = max
  mode = r[3]

  cur.execute(
    "UPDATE osutop_temp SET i = ?, inter = 'True' WHERE message_id = ?", (
      i,
      inter.message.id,
    ))
  conn.commit()

  view = await osutop_button(i, max)
  await inter.response.edit_message(view=view)

  embed = await _osu_top(user_id, i, mode)
  await inter.followup.edit_message(embed=embed[0],
                                    message_id=inter.message.id)


async def osutop_select(inter: discord.Interaction):
  modal = osutop_modal()
  await inter.response.send_modal(modal)


@bot.command()
async def command(ctx):
  embed = discord.Embed(title="**コマンド一覧**")

  embed.add_field(
    name=".osuset <username(Required)>",
    value=
    "アカウントを紐付けする\n※自動的にプレイモードが登録されます。\n※すべてのコマンドは、モードを指定していない場合に登録されているプレイモードと対応した結果が返されます。"
  )

  embed.add_field(name=".osu <username> <mode>",
                  value="プロフィールを確認する\n",
                  inline=False)

  embed.add_field(name=".osutop <username> <mode>",
                  value="ベストパフォーマンスを確認する",
                  inline=False)

  embed.add_field(name=".rs <username> <mode>",
                  value="最新のプレイを確認する\n",
                  inline=False)

  embed.add_field(name=".osudel", value="アカウントの紐付けを解除する\n", inline=False)

  embed.add_field(
    name=".pp <URL(Required)> <mod>",
    value=
    "譜面の情報を確認する\n**<mod>**\n・EZ・NF・HT\n・HR ・DT ・HD・FL\n※複数のmodを選ぶ際は、必ず半角空白を入れてください\n※EZ・HRとHT・DTは共存できません。必ず難易度上昇modが優先されます。\n",
    inline=False)

  embed.add_field(
    name=".r <difficulty> <length> <mode>",
    value=
    "山田勝己がランダムにRanked譜面を投げる\n**▸ .r **\n**▸ .r 5.5** (5.5～6.5)\n**▸ .r 5.5 5.6** (5.5～5.6)\n**▸ .r 6.2 length>=180 ** (6.2～7.2) (3分以上)\n**▸ .r 6.2 6.5 length>=180 length<300** (6.2～6.5) (3分以上5分未満)",
    inline=False)

  embed.add_field(name=".maps <mode>",
                  value="データベースに格納されている譜面の数を確認する",
                  inline=False)

  embed.add_field(
    name=".nbon (現在使用不可)",
    value='山田勝己が毎日0時に新着Ranked譜面のリストを送る\n **▸ ".nboff"** により登録を解除できます。',
    inline=False)

  embed.add_field(
    name="モードの指定方法",
    value=
    '▸ **"mode=x"** or **"m=x"**\n▸ osu!standard: **s**\n▸ osu!taiko: **t**\n▸ osu!catch: **c**\n▸ osu!mania: **m**',
    inline=False)

  await ctx.send(embed=embed)
  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.command [ {} ]".format(cuser))


@bot.command()
async def r(ctx, *args):
  diff = []
  diff_min = 'NULL'
  diff_max = 'NULL'
  length = []
  mode = "osu"
  user = await bot.fetch_user(ctx.author.id)

  cur = conn.cursor()

  cur.execute("SELECT playmode FROM user WHERE discord_user_id = ?",
              (ctx.author.id, ))

  for r in cur:
    mode = r[0]

  if args:
    for list in args:
      if re.match(r'length(<|>|<=|>=|=)\d+', list):
        length.append(list)
        if len(length) >= 3:
          return await r_error(ctx)
      elif re.match(r'(mode|m)=(s|t|c|m)', list):
        mode = await fetch_mode(args)
      else:
        if len(diff) < 2:
          try:
            diff.append(float(list))
          except:
            return await r_error(ctx)
        else:
          return await r_error(ctx)

  if diff:
    diff_len = len(diff)
    if diff_len >= 2:
      if diff[0] < diff[1]:
        diff_min = diff[0]
        diff_max = diff[1]
      else:
        diff_min = diff[1]
        diff_max = diff[0]
    else:
      diff_min = diff[0]
      diff_max = diff[0] + 1

  temp = await _random(diff_min, diff_max, length, mode)
  try:
    embed = temp[0]
    option = temp[1]
  except:
    embed = temp
    return await ctx.send(embed=embed)
  view = discord.ui.View()
  view.add_item(
    discord.ui.Button(label="もう一回",
                      style=discord.ButtonStyle.green,
                      custom_id="r_retry"))
  message_id = await ctx.send("**俺には…この譜面しかないんですよ**", embed=embed, view=view)

  print("コマンドが使用されました：.r {} {} [ {} ]".format(mode, option, user))

  cur.execute(
    "INSERT INTO r_temp(message_id, diff_min, diff_max, length, mode) values(?, ?, ?, ?, ?)",
    (
      message_id.id,
      diff_min,
      diff_max,
      str(length),
      mode,
    ))
  conn.commit()

  inter = True

  while inter == True:
    cur.execute("UPDATE r_temp SET inter = 'False' WHERE message_id = ?",
                (str(message_id.id), ))
    conn.commit()
    await asyncio.sleep(30)
    cur.execute("SELECT inter FROM r_temp WHERE message_id = ?",
                (str(message_id.id), ))
    for r in cur:
      if r[0] == "False":
        inter = False
      else:
        inter = True
  await message_id.edit(view=None)
  cur.execute("DELETE FROM r_temp WHERE message_id = ?",
              (str(message_id.id), ))
  conn.commit()
  user = await bot.fetch_user(ctx.author.id)
  print("ボタンを削除しました：.r {} {} [ {} ]".format(mode, option, user))


async def _random(diff_min, diff_max, length, mode):

  mods = ()
  option = ""
  diff_option = ""
  length_option = ""
  r = 0
  cur = conn.cursor()

  if diff_min != 'NULL' and diff_max != 'NULL':
    option += f"AND difficulty BETWEEN {diff_min} AND {diff_max} "
    diff_option += f"{diff_min} - {diff_max}"

  if len(length) != 0:
    for i in range(len(length)):
      option += f"AND {length[i]} "
    length_option = ' '.join(length)

  option += f"AND type_id = (SELECT id FROM maptype WHERE type = '{mode}')"
  cur.execute(
    f"SELECT beatmap_id FROM beatmaps WHERE 1 = 1 {option} ORDER BY RANDOM () LIMIT 1"
  )

  for r in cur:
    pass
  if r != 0:
    embed = await beatmap_info(r[0], mods, mode)
    option = f"{diff_option} {length_option}"
    return embed, option
  else:
    embed = discord.Embed(title="**Error**", description="譜面が見つかりませんでした")
    return embed


async def r_retry(inter: discord.Interaction):

  cur = conn.cursor()

  cur.execute("UPDATE r_temp SET inter = 'True' WHERE message_id = ?",
              (inter.message.id, ))
  conn.commit()

  cur.execute(
    "SELECT diff_min, diff_max, length, mode FROM r_temp WHERE message_id = ?",
    (inter.message.id, ))

  for r in cur:
    pass

  diff_min = r[0]
  diff_max = r[1]
  length = eval(r[2])
  mode = r[3]

  await inter.response.edit_message(content='**俺には...この譜面もあるんですよ**')

  temp = await _random(diff_min, diff_max, length, mode)

  embed = temp[0]
  option = temp[1]

  await inter.followup.edit_message(embed=embed, message_id=inter.message.id)

  print("ボタンが押されました：.r {} {}".format(mode, option))


async def r_error(ctx):
  embed = discord.Embed(title="**引数**")
  embed.add_field(name="難易度", value="整数、または小数のみ有効です。\n", inline=False)
  embed.add_field(
    name="長さ",
    value="条件式には空白を入れないでください。\n▸ .r 5.5 5.7 length>180\n▸ .r length>=240\n",
    inline=False)
  return await ctx.send(embed=embed)


@bot.command()
async def pp(ctx, url, *mods):
  try:
    urllib.request.urlopen(url)
    result = re.findall(r"\d+", url)
    i = len(result) - 1
    jsonmap = api.get_beatmap(int(result[i]))
    jsonData = jsonmap.json()
  except:
    return await ctx.send("**URLが間違っています。**")

  beatmap_id = jsonData['id']
  mode = jsonData['mode']

  embed = await beatmap_info(beatmap_id, mods, mode)

  await ctx.send(embed=embed)
  user = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.pp {} [ {} ]".format(jsonData['url'], user))


async def beatmap_info(beatmap_id, mods, mode):

  jsonmap = api.get_beatmap(beatmap_id)
  jsonData = jsonmap.json()

  title = jsonData['beatmapset']['title']
  artist = jsonData['beatmapset']['artist']
  status = jsonData['status']
  version = jsonData['version']
  bpm = jsonData['bpm']
  cs = jsonData['cs']
  ar = jsonData['ar']
  od = jsonData['accuracy']
  hp = jsonData['drain']
  map_url = jsonData['url']
  mapset_id = jsonData['beatmapset']['id']
  map_id = beatmap_id

  total_length = float(jsonData['total_length']) / 60

  length = len(mods)
  mod_integer = 0
  mod = list(mods)

  for i in range(length):
    mod[i] = str.upper(mod[i])
    if mod[i] == "NF":
      mod_integer += 1
    elif mod[i] == "EZ":
      flag = False
      for j in range(length):
        mod[j] = str.upper(mod[j])
        if mod[j] == "HR":
          flag = True
      if flag == False:
        mod_integer += 2
        cs *= 0.5
        hp *= 0.5
    elif mod[i] == "TD":
      mod_integer += 4
    elif mod[i] == "HD":
      mod_integer += 8
    elif mod[i] == "HR":
      mod_integer += 16
      cs *= 1.3
      hp *= 1.4
      if cs >= 10:
        cs = 10
      if hp >= 10:
        hp = 10
    elif mod[i] == "DT":
      mod_integer += 64
      total_length /= 1.5
      bpm *= 1.5
    elif mod[i] == "HT":
      flag = False
      for j in range(length):
        mod[j] = str.upper(mod[j])
        if mod[j] == "DT":
          flag = True
      if flag == False:
        mod_integer += 256
        total_length /= 0.75
        bpm *= 0.75
    elif mod[i] == "FL":
      mod_integer += 1024

  pp = await pp_calc_map(map_id, mod_integer, mode)

  pp_ss = pp['pp_ss']
  pp_99 = pp['pp_99']
  pp_98 = pp['pp_98']
  pp_95 = pp['pp_95']
  if pp["ar"] is not None:
    ar = pp['ar']
  if pp["od"] is not None:
    od = pp['od']
  diff_rating = pp['difficulty']

  x = total_length - int(total_length)
  y = int(total_length)
  x = math.floor(x * 60)
  x_zero = str(x).zfill(2)

  embed = discord.Embed(title="{} - {} [{}]".format(artist, title, version),
                        url=map_url,
                        color=discord.Colour.green())

  if mode == "osu" or mode == "fruits":
    embed.description = '▸ **Difficulty:** {:.2f}★\n▸ **Length:** {}:{}\n▸ **BPM:** {}\n▸ **CS:** {:.1f} **AR:** {:.1f} **OD:** {:.1f} **HP:** {:.1f}\n▸ **95%:** {:.2f}PP | **98%:** {:.2f}PP | **99%:** {:.2f}PP | **100%:** {:.2f}PP\n▸ **Status:** {}\n▸ [Download](https://osu.ppy.sh/beatmapsets/{}/download) | osu!direct: <osu://b/{}>'.format(
      diff_rating, y, x_zero, bpm, cs, ar, od, hp, pp_95, pp_98, pp_99, pp_ss,
      str.upper(status), mapset_id, map_id)
  elif mode == "taiko":
    embed.description = '▸ **Difficulty:** {:.2f}★\n▸ **Length:** {}:{}\n▸ **BPM:** {}\n▸ **OD:** {:.1f} **HP:** {:.1f}\n▸ **95%:** {:.2f}PP | **98%:** {:.2f}PP | **99%:** {:.2f}PP | **100%:** {:.2f}PP\n▸ **Status:** {}\n▸ [Download](https://osu.ppy.sh/beatmapsets/{}/download) | osu!direct: <osu://b/{}>'.format(
      diff_rating, y, x_zero, bpm, od, hp, pp_95, pp_98, pp_99, pp_ss,
      str.upper(status), mapset_id, map_id)
  elif mode == "mania":
    embed.description = '▸ **Difficulty:** {:.2f}★\n▸ **Length:** {}:{}\n▸ **BPM:** {}\n▸ **Keys:** {} **OD:** {:.1f} **HP:** {:.1f}\n▸ **95%:** {:.2f}PP | **98%:** {:.2f}PP | **99%:** {:.2f}PP | **100%:** {:.2f}PP\n▸ **Status:** {}\n▸ [Download](https://osu.ppy.sh/beatmapsets/{}/download) | osu!direct: <osu://b/{}>'.format(
      diff_rating, y, x_zero, bpm, cs, od, hp, pp_95, pp_98, pp_99, pp_ss,
      str.upper(status), mapset_id, map_id)
  embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(mapset_id))

  return embed


@bot.command()
async def maps(ctx, *args):
  Maps = ""
  mode = ""
  prompt = "'1' = '1'"

  if args:
    mode = await fetch_mode(args)
    if mode != "":
      prompt += f"AND type_id = (SELECT id FROM maptype WHERE type = '{mode}')"
      mode = await _mode(mode)

  cur = conn.cursor()
  cur.execute(
    f"SELECT CASE WHEN difficulty < 1 THEN 'Below 1 star' WHEN difficulty >= 1 AND difficulty < 2 THEN '1 Star' WHEN difficulty >= 2 AND difficulty < 3 THEN '2 Stars' WHEN difficulty >= 3 AND difficulty < 4 THEN '3 Stars' WHEN difficulty >= 4 AND difficulty < 5 THEN '4 Stars' WHEN difficulty >= 5 AND difficulty < 6 THEN '5 Stars' WHEN difficulty >= 6 AND difficulty < 7 THEN '6 Stars' WHEN difficulty >= 7 AND difficulty < 8 THEN '7 Stars' WHEN difficulty >= 8 AND difficulty < 9 THEN '8 Stars' WHEN difficulty >= 9 AND difficulty < 10 THEN '9 Stars' WHEN difficulty >= 10 AND difficulty < 11 THEN '10 Stars' WHEN difficulty >= 11 THEN 'Above 10 stars' ELSE 'others' END AS 'Stars', count(*) FROM beatmaps WHERE {prompt} GROUP BY Stars ORDER BY difficulty",
  )
  for r in cur:
    Maps += '**{}**：{}\n'.format(r[0], r[1])
  embed = discord.Embed(title=f'ALL RANKED MAPS: {mode}',
                        description=Maps,
                        color=discord.Colour.green())
  await ctx.send(embed=embed)
  user = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.maps [ {} ]".format(user))


@bot.command()
async def clean(ctx):
  cur.execute("DELETE FROM r_temp")
  cur.execute("DELETE FROM rs_temp")
  cur.execute("DELETE FROM osutop_temp")
  conn.commit()

  await ctx.send("削除されていない一時データを削除しました。")


async def fetch_user(args):
  name = ""
  for list in args:
    if re.match(r'(mode=|m=)(s|t|m|c)', list):
      pass
    else:
      name += list
      name += ' '
  username = name.rstrip()

  return username


async def fetch_mode(args):
  mode = ""
  for list in args:
    if re.match(r'(mode=|m=)(s|t|m|c)', list):
      list = re.sub(r'm=|mode=', '', list)
      if list == "s":
        mode = "osu"
      elif list == "t":
        mode = "taiko"
      elif list == "m":
        mode = "mania"
      elif list == "c":
        mode = "fruits"

  return mode


async def _mode(mode):
  if mode == "osu":
    mode = "Standard"
  elif mode == "taiko":
    mode = "Taiko"
  elif mode == "mania":
    mode = "Mania"
  elif mode == "fruits":
    mode = "Catch"

  return mode


async def pp_calc_user(map_id, rank, mod, acc, combo, maxcombo, count300,
                       count100, count50, misses, objects, mode):
  url = 'https://osu.ppy.sh/osu/{}'.format(map_id)

  file_path = 'data/osu/temp/{}.osu'.format(map_id)
  await download_file(url, file_path)
  map = Beatmap(path=file_path)

  mod_integer = 0
  i = 0
  for mods in mod:
    mods = re.sub(r"[^a-zA-Z,]", "", mod[i])
    if mods == "NF":
      mod_integer += 1
    elif mods == "EZ":
      mod_integer += 2
    elif mods == "TD":
      mod_integer += 4
    elif mods == "HD":
      mod_integer += 8
    elif mods == "HR":
      mod_integer += 16
    elif mods == "DT" or mods == "NC":
      mod_integer += 64
    elif mods == "HT":
      mod_integer += 256
    elif mods == "FL":
      mod_integer += 1024
    i += 1

  if mode == "osu":
    mode = 0
  elif mode == "taiko":
    mode = 1
  elif mode == "fruits":
    mode = 2
  elif mode == "mania":
    mode = 3

  calc = Calculator(mods=mod_integer, mode=mode)

  max_perf = calc.performance(map)
  calc.set_difficulty(max_perf.difficulty)

  calc.set_n300(count300)
  calc.set_n100(count100)
  calc.set_n50(count50)
  calc.set_n_misses(misses)
  calc.set_combo(combo)

  curr_perf = calc.performance(map)

  if maxcombo - combo <= count100 and misses == 0:
    pp_json = {
      'pp_curr': curr_perf.pp,
      'pp_fc': None,
      'difficulty': max_perf.difficulty.stars
    }
  elif rank != 'F':
    acc = ((count300 * 300 + count100 * 100 + count50 * 50) /
           ((count300 + count100 + count50) * 300)) * 100

    calc = Calculator(mods=mod_integer, mode=mode)
    calc.set_acc(acc)
    fc_perf = calc.performance(map)
    pp_json = {
      'pp_curr': curr_perf.pp,
      'pp_fc': fc_perf.pp,
      'acc_fc': acc,
      'difficulty': max_perf.difficulty.stars
    }
  else:
    passed_objects = count300 + count100 + count50 + misses
    calc.set_passed_objects(passed_objects)
    curr_perf = calc.performance(map)
    acc = ((count300 * 300 + count100 * 100 + count50 * 50) /
           ((count300 + count100 + count50) * 300)) * 100
    calc = Calculator(mods=mod_integer, mode=mode)
    calc.set_acc(acc)
    fc_perf = calc.performance(map)
    pp_json = {
      'pp_curr': curr_perf.pp,
      'pp_fc': fc_perf.pp,
      'acc_fc': acc,
      'difficulty': max_perf.difficulty.stars,
      'map_completion': passed_objects / objects
    }

  os.remove(file_path)
  return pp_json


async def pp_calc_map(map_id, mod, mode):
  url = 'https://osu.ppy.sh/osu/{}'.format(map_id)

  file_path = 'data/osu/temp/{}.osu'.format(map_id)
  await download_file(url, file_path)
  map = Beatmap(path=file_path)

  if mode == "osu":
    mode = 0
  elif mode == "taiko":
    mode = 1
  elif mode == "fruits":
    mode = 2
  elif mode == "mania":
    mode = 3

  calc = Calculator(mods=mod, mode=mode)

  perf_max = calc.performance(map)
  calc.set_difficulty(perf_max.difficulty)

  calc.set_acc(99)
  perf_99 = calc.performance(map)
  calc.set_acc(98)
  perf_98 = calc.performance(map)
  calc.set_acc(95)
  perf_95 = calc.performance(map)

  pp_json = {
    'pp_ss': perf_max.pp,
    'pp_99': perf_99.pp,
    'pp_98': perf_98.pp,
    'pp_95': perf_95.pp,
    'difficulty': perf_max.difficulty.stars,
    'ar': perf_max.difficulty.ar,
    'od': perf_max.difficulty.od
  }

  os.remove(file_path)
  return pp_json


async def download_file(url, filename):
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        with open(filename, 'wb') as f:
          while True:
            chunk = await response.content.read(1024)
            if not chunk:
              break
            f.write(chunk)
        return await response.release()
  except:
    return -1


@bot.event
async def on_interaction(inter: discord.Interaction):
  try:
    if inter.data['component_type'] == 2:
      custom_id = inter.data['custom_id']
      await eval("{}".format(custom_id))(inter)

  except:
    pass


@bot.command()
async def chat(ctx, *, question):
  past_conversations = await get_past_conversations(ctx.author.id)
  msg = [{
    "role": "system",
    "content": "あなたは「山田勝己(やまだかつみ)」という名前の男性アシスタントです。関西弁で会話をしてください。"
  }]
  for row in past_conversations:
    msg.append(row)
  dict = {"role": "user", "content": "{}".format(question)}
  msg.append(dict)

  try:
    async with ctx.typing():
      response = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo",
                                                     messages=msg)
  except:
    embed = discord.Embed(title="**Rate Limit Error**",
                          description="**少し待ってからもう一度お試しください**\n")
    cuser = await bot.fetch_user(ctx.author.id)
    print("コマンドが使用されました：.chat {} [ {} ]\n".format(question, cuser))
    print("RATE LIMIT ERRORが発生しました。エラーメッセージを送ります。\n")
    return await ctx.reply(embed=embed)

  response_text = response["choices"][0]["message"]["content"].strip() + "\n"
  await ctx.reply(response_text)

  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.chat {} [ {} ]\n".format(question, cuser))
  print("AIによる返答：{}\n".format(response_text))

  cur.execute(
    "INSERT INTO conversation_history (user_id, message, response) VALUES (?, ?, ?)",
    (ctx.author.id, question, response_text))

  cur.execute(
    "DELETE FROM conversation_history WHERE datetime(timestamp, '+5 minutes') < CURRENT_TIMESTAMP or timestamp < (SELECT MIN(timestamp) FROM (SELECT timestamp FROM conversation_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5)) AND user_id = ?",
    (ctx.author.id, ctx.author.id))

  conn.commit()


async def get_past_conversations(user_id):
  history = []
  cur.execute(
    "SELECT message, response FROM (SELECT * FROM conversation_history WHERE user_id = ? AND datetime(timestamp, '+5 minutes') > CURRENT_TIMESTAMP ORDER BY timestamp DESC LIMIT 5) ORDER BY timestamp",
    (user_id, ))

  for row in cur:
    history.append({"role": "user", "content": "{}".format(row[0])})
    history.append({"role": "assistant", "content": "{}".format(row[1])})

  return history


@bot.command()
async def rchat(ctx):
  cur.execute("DELETE FROM conversation_history WHERE user_id = ?",
              (ctx.author.id, ))

  await ctx.reply("今までの会話全部忘れてしもたわ！！")


utc = datetime.timezone.utc

time = datetime.time(hour=15, minute=0, second=0, tzinfo=utc)


@tasks.loop(time=time)
async def new_beatmap():

  flag = 0
  count = 0
  Channel_id = []

  t_delta = datetime.timedelta(hours=9)
  JST = datetime.timezone(t_delta, 'JST')
  now = datetime.datetime.now(JST)

  print(
    f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}")

  flag_fpath = "data/latest-notice.json"
  dump_flag = {"year": now.year, "month": now.month, "day": now.day}

  with open(flag_fpath, "w") as json_file:
    json.dump(dump_flag, json_file)

  while (flag == 0):

    maps = []

    beatmap_id = []
    beatmapset_id = []
    beatmapset_Max_difficulty = []
    beatmapset_Min_difficulty = []
    approved = []
    approved_date = []

    f_path = "data/new-beatmap.json"

    with open(f_path, "r") as json_file:
      json_data = json.load(json_file)

    date = json_data["date"]

    print(f"{date}以降にランク付けされた譜面を出力します。")

    request_url = f"https://osu.ppy.sh/api/get_beatmaps?k={api_key}&since={date}&m=0"

    try:
      response = requests.get(request_url)
    except:
      return

    req_json = response.json()

    if len(req_json) == 0:
      print(f"\n{date}以降にランク付けされた譜面はありませんでした。\n")
      cur.execute("SELECT channel_id FROM notice_new_beatmaps")

      embed = discord.Embed(title="新着譜面一覧",
                            description="新たにランク付けされた譜面はありませんでした。",
                            color=discord.Colour.green())
      for r in cur:
        Channel_id.append(r[0])

      for i in range(len(Channel_id)):
        channel = bot.get_channel(Channel_id[i])
        try:
          await channel.send(embed=embed)
          print(f"通知を送信しました。Channel_ID：{Channel_id[i]}")
          print("")
        except AttributeError:
          cur.execute("DELETE FROM notice_new_beatmaps WHERE channel_id = ?",
                      (Channel_id[i], ))
          conn.commit()
          print(f"チャンネルが見つかりませんでした。Channel_ID：{Channel_id[i]}")

      return

    for i in range(len(req_json)):

      if req_json[i]["approved"] == "1" or req_json[i]["approved"] == "2":

        beatmap_id.append(req_json[i]["beatmap_id"])
        beatmapset_id.append(req_json[i]["beatmapset_id"])
        beatmapset_Max_difficulty.append(req_json[i]["difficultyrating"])
        beatmapset_Min_difficulty.append(req_json[i]["difficultyrating"])
        approved.append(req_json[i]["approved"])
        approved_date.append(req_json[i]["approved_date"])

        for j in range(len(beatmapset_id) - 1):
          if req_json[i]["beatmapset_id"] == beatmapset_id[j]:
            if req_json[i]["difficultyrating"] < beatmapset_Max_difficulty[j]:
              beatmapset_Max_difficulty[len(beatmapset_Max_difficulty) -
                                        1] = beatmapset_Max_difficulty[j]
            if req_json[i]["difficultyrating"] > beatmapset_Min_difficulty[j]:
              beatmapset_Min_difficulty[len(beatmapset_Min_difficulty) -
                                        1] = beatmapset_Min_difficulty[j]
            beatmapset_Max_difficulty.pop(j)
            beatmapset_Min_difficulty.pop(j)
            beatmapset_id.pop(j)
            beatmap_id.pop(j)
            approved.pop(j)
            approved_date.pop(j)

    for i in range(len(beatmap_id)):

      url = 'https://osu.ppy.sh/osu/{}'.format(beatmap_id[i])
      file_path = 'data/{}.osu'.format(beatmap_id[i])
      temp = await download_file(url, file_path)

      if temp != -1:
        try:
          beatmap = api.get_beatmap(id=beatmap_id[i])
          jsonData = beatmap.json()

          if jsonData['mode'] == 'osu' and (jsonData['ranked'] == 1
                                            or jsonData['ranked'] == 2):
            beatmap = api.get_beatmap(id=beatmap_id[i])
            jsonData = beatmap.json()

            artist = jsonData["beatmapset"]["artist"]
            title = jsonData['beatmapset']['title']
            url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id[i]}"
            creator = jsonData["beatmapset"]["creator"]
            bpm = jsonData["beatmapset"]["bpm"]
            total_length = float(jsonData['total_length']) / 60
            diff_min = round(float(beatmapset_Min_difficulty[i]), 2)
            diff_max = round(float(beatmapset_Max_difficulty[i]), 2)

            x = total_length - int(total_length)
            y = int(total_length)
            x = math.floor(x * 60)
            x_zero = str(x).zfill(2)

            count += 1

            maps.append(
              f"**{count}**. **[ {artist} - {title} ]({url})** by {creator}\n▸ **Difficulty:** {diff_min} – {diff_max}★\n ▸ **Length: **{y}:{x_zero}\n ▸ **BPM:** {bpm}\n ▸ osu!direct: <osu://dl/{beatmapset_id[i]}>\n ▸ [Download](https://osu.ppy.sh/beatmapsets/{beatmapset_id[i]}/download)\n\n"
            )

            print("Added Beatmapset info：{}".format(count))
          else:
            print("Beatmap is not Ranked：{}".format(beatmap_id[i]))
        except:
          print("Not Found：{}".format(beatmap_id[i]))
        os.remove(file_path)
      else:
        print("ERR_HTTP2_PROTOCOL_ERROR：{}".format(beatmap_id[i]))

    if count == 0:
      print(f"\n{date}以降にランク付けされた譜面はありませんでした。\n")
      cur.execute("SELECT channel_id FROM notice_new_beatmaps")

      embed = discord.Embed(title="新着譜面一覧",
                            description="新たにランク付けされた譜面はありませんでした。",
                            color=discord.Colour.green())
      for r in cur:
        Channel_id.append(r[0])

      for i in range(len(Channel_id)):
        channel = bot.get_channel(Channel_id[i])
        try:
          await channel.send(embed=embed)
          print(f"通知を送信しました。Channel_ID：{Channel_id[i]}")
          print("")
        except AttributeError:
          cur.execute("DELETE FROM notice_new_beatmaps WHERE channel_id = ?",
                      (Channel_id[i], ))
          conn.commit()
          print(f"チャンネルが見つかりませんでした。Channel_ID：{Channel_id[i]}")

      return

    dump_date = {"date": approved_date[len(approved_date) - 1]}

    with open(f_path, "w") as json_file:
      json.dump(dump_date, json_file)

    cur.execute("SELECT channel_id FROM notice_new_beatmaps")

    for r in cur:
      Channel_id.append(r[0])

    mapstr = ""

    for i in range(len(maps)):
      if i % 15 == 0 and i != 0 and i != len(maps) - 1:
        embed = discord.Embed(title="新着譜面一覧",
                              description=mapstr,
                              color=discord.Colour.green())
        embed.set_thumbnail(
          url="https://b.ppy.sh/thumb/{}l.jpg".format(beatmapset_id[0]))

        for j in range(len(Channel_id)):
          channel = bot.get_channel(Channel_id[j])
          try:
            await channel.send(embed=embed)
            print(f"通知を送信しました。Channel_ID：{Channel_id[j]}")
            print("")
          except AttributeError:
            print(f"チャンネルが見つかりませんでした。Channel_ID：{Channel_id[j]}")

        mapstr = ""

      mapstr += maps[i]

    embed = discord.Embed(title="新着譜面一覧",
                          description=mapstr,
                          color=discord.Colour.green())
    embed.set_thumbnail(
      url="https://b.ppy.sh/thumb/{}l.jpg".format(beatmapset_id[0]))

    for i in range(len(Channel_id)):
      channel = bot.get_channel(Channel_id[i])
      try:
        await channel.send(embed=embed)
        print(f"通知を送信しました。Channel_ID：{Channel_id[i]}")
        print("")
      except AttributeError:
        cur.execute("DELETE FROM notice_new_beatmaps WHERE channel_id = ?",
                    (Channel_id[i], ))
        conn.commit()
        print(f"チャンネルが見つかりませんでした。Channel_ID：{Channel_id[i]}")

    print(f"{date}から現在まで、新たにランク付けされた{count}個の譜面の出力が完了しました。")
    print(f'次回は、{approved_date[len(approved_date) - 1]}以降にランク付けされた譜面を出力します。\n')

    if len(req_json) < 500:
      flag = 1


@tasks.loop(minutes=30)
async def add_beatmap():

  flag = 0

  while (flag == 0):

    count = 0

    beatmap_id = []
    approved_date = []

    f_path = "data/add-beatmap.json"

    with open(f_path, "r") as json_file:
      json_data = json.load(json_file)

    date = json_data["date"]

    print(f"{date}以降にランク付けされた譜面を登録します。")

    request_url = f"https://osu.ppy.sh/api/get_beatmaps?k={api_key}&since={date}"

    try:
      response = requests.get(request_url)
    except:
      return

    req_json = response.json()

    if len(req_json) == 0:
      print(f"\n{date}以降にランク付けされた譜面はありませんでした。\n")
      return

    for i in range(len(req_json)):

      beatmap_id.append(req_json[i]["beatmap_id"])

      if req_json[i]["approved"] != '3':

        approved_date.append(req_json[i]["approved_date"])

        url = 'https://osu.ppy.sh/osu/{}'.format(beatmap_id[i])
        file_path = 'data/{}.osu'.format(beatmap_id[i])
        temp = await download_file(url, file_path)

        if temp != -1:
          try:
            beatmap = api.get_beatmap(id=beatmap_id[i])
            jsonData = beatmap.json()

            if jsonData['ranked'] == 1 or jsonData['ranked'] == 2:

              cur.execute(
                'INSERT INTO beatmaps(beatmap_id, artist, title, version, type_id, difficulty, bpm, length) values(?, ?, ?, ?, (SELECT id FROM maptype WHERE type = ?), ?, ?, ?) ON CONFLICT(beatmap_id) DO UPDATE SET type_id = (SELECT id FROM maptype WHERE type = ?), artist = ?, title = ?, version = ?, bpm = ?, difficulty = ?, length = ?',
                (
                  beatmap_id[i],
                  jsonData['beatmapset']['artist'],
                  jsonData['beatmapset']['title'],
                  jsonData['version'],
                  jsonData['mode'],
                  jsonData['difficulty_rating'],
                  jsonData['bpm'],
                  jsonData['total_length'],
                  jsonData['mode'],
                  jsonData['beatmapset']['artist'],
                  jsonData['beatmapset']['title'],
                  jsonData['version'],
                  jsonData['bpm'],
                  jsonData['difficulty_rating'],
                  jsonData['total_length'],
                ))
              conn.commit()
              print("Added Beatmap to DB：{}".format(beatmap_id[i]))
              count += 1
            else:
              print("Beatmap is not Ranked：{}".format(beatmap_id[i]))
          except:
            print("Not Found：{}".format(beatmap_id[i]))
          os.remove(file_path)
        else:
          print("ERR_HTTP2_PROTOCOL_ERROR：{}".format(beatmap_id[i]))

        await asyncio.sleep(2)

    if count == 0:
      print(f"\n{date}以降にランク付けされた譜面はありませんでした。\n")
      return

    dump_date = {"date": approved_date[len(approved_date) - 1]}

    with open(f_path, "w") as json_file:
      json.dump(dump_date, json_file)

    print(f"{date}から現在まで、新たにランク付けされた{count}個の譜面の登録が完了しました。")
    print(f'次回は、{approved_date[len(approved_date) - 1]}以降にランク付けされた譜面を登録します。\n')

    if len(req_json) < 500:
      flag = 1


@bot.command()
async def nbon(ctx):
  '''
  try:
    cur.execute("INSERT INTO notice_new_beatmaps(channel_id) values(?)",
                (ctx.message.channel.id, ))
    conn.commit()

    embed = discord.Embed(
      title="新着譜面通知をonにしました！！",
      description='毎日0時に新着譜面のリストを投稿します。\noffにするには、同じチャンネルに".nboff"を入力してください。')
    await ctx.send(embed=embed)
  except:
    await ctx.send("**すでに登録されています。**")
    '''

  await ctx.send("**現在使用不可**")

  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.nbon [ {} ]".format(cuser))


@bot.command()
async def nboff(ctx):
  r = [None]
  cur.execute(
    "SELECT channel_id FROM notice_new_beatmaps WHERE channel_id = ?",
    (ctx.message.channel.id, ))

  for r in cur:
    pass

  if r[0] != None:
    cur.execute("DELETE FROM notice_new_beatmaps WHERE channel_id = ?",
                (ctx.message.channel.id, ))
    conn.commit()

    embed = discord.Embed(title="新着譜面通知をoffにしました！！",
                          description='再度onにするには、".nbon"を入力してください。')
    await ctx.send(embed=embed)
  else:
    await ctx.send("**すでに削除されています。**")

  cuser = await bot.fetch_user(ctx.author.id)
  print("コマンドが使用されました：.nboff [ {} ]".format(cuser))


try:
  keep_alive()
  bot.run(TOKEN)
  print("RESTARTING NOW...\n\n")
  os.system("kill 1")
except Exception:
  print("\n\nBLOCKED BY RATE LIMITS")
  print("RESTARTING NOW...\n\n")
  os.system("kill 1")
