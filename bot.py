import discord
from discord.ext import tasks
from geopy.geocoders import GoogleV3
from .scraper import load_old_df, scan_new_data, save_df
from safe_u import API_KEY_LOCAL, USER_ID
import pandas as pd
import collections 

class DiscordBot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.receiver = self.get_user(int(USER_ID))
        print("Communicating with", self.receiver)
        self.geolocator = GoogleV3(api_key=API_KEY_LOCAL)
        self.df = load_old_df()
        print(self.df.dtypes)
        #print(self.df.head())
        self.tasks_queue = collections.deque()
        for _, row in self.df[~self.df['Checked']].iterrows():
            self.push((row, 'old'))
        
        #print("Queue:",list(self.tasks_queue.queue))
        #while not self.empty(): pass
        #save_df(self.df)
        self.do_task.start()
 
    @tasks.loop(minutes=5.)
    async def do_task(self):
        as_of_date = None if self.df is None or len(self.df) == 0 else self.df.loc[0, 'Date']
        df_new = scan_new_data(self.geolocator, as_of_date)
        #print(df_new.head())
        for _, row in df_new.iterrows():
            self.push((row, 'new'))
        #print("Queue:",list(self.tasks_queue.queue))
        num_tasks=len(self.tasks_queue)
        cnt = 1
        while not self.empty(): 
            front, which_df = self.pop()
            notification = "[%d/%d]\t%s\n%s\n\nExtracted locations:\n%s.\n\nIs this correct?" % (cnt, num_tasks, front['Date'].strftime("%Y-%m-%d %H:%M"), front['Content'], "\n".join(["\t\u2022 " + x[0] for x in front['Location']]))
            await self.receiver.send(notification)
            msg = await self.wait_for('message', check=lambda m: m.content == "!yes" or (len(m.content) != 0 and m.content.split()[0] == "!no"))
            if msg.content == '!yes':
                await msg.add_reaction("👍")
                front['Checked'] = True
                if which_df == 'old': self.df.iloc[front.name] = front
                else: df_new.iloc[front.name] = front
                cnt += 1
            else:
                msg_split = msg.content.split()
                assert len(msg_split) != 0 and msg_split[0] == "!no"
                await msg.add_reaction("🔨")
                corrected_addresses = " ".join(msg_split[1:]).split(";")
                print("corrected_addresses:", corrected_addresses)
                corrected_locations = []
                for address_raw in corrected_addresses:
                    address = address_raw.strip()
                    if "minneapolis" not in address.lower(): 
                        address += ", Minneapolis"
                    if "mn" not in address.lower() and "minnesota" not in address.lower():
                        address += ", MN"
                    location = self.geolocator.geocode(address,  timeout=10)
                    corrected_locations.append((location.address, location.latitude, location.longitude))
                front['Location']= corrected_locations
                self.push_front((front, which_df))
                #front['Checked'] = True

        self.df = pd.concat([df_new, self.df])
        #print(self.df.head())
        save_df(self.df)
        
    def push(self, item):
        self.tasks_queue.append(item)
    def push_front(self, item):
        self.tasks_queue.appendleft(item)
    def pop(self):
        return self.tasks_queue.popleft()
    def empty(self):
        return not bool(self.tasks_queue)
'''
if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    bot = DiscordBot(intents=intents)
    bot.run(BOT_TOKEN)
'''