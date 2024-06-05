import asyncio
import os, json, time, aiocron, psutil

from threading import Thread
from scripts.tapswap import TapSwap
from scripts.hamster import HamsterCombat
from scripts.cexio import Cex_IO
from scripts.logger import setup_custom_logger

from telethon.sync import TelegramClient
from telethon.sync import functions, events



logger = setup_custom_logger("mainapp")


with open('config.json') as f:
    data             = json.load(f)
    api_id           = data['api_id']
    api_hash         = data['api_hash']
    admin            = data['admin']
    auto_upgrade     = data['auto_upgrade']
    max_tap_level    = data['max_tap_level']
    max_charge_level = data['max_charge_level']
    max_energy_level = data['max_energy_level']
    max_days_for_return = data['max_days_for_return']
    cexio_clicker    = data['cexio_clicker']
    tapswap_clicker  = data['tapswap_clicker']
    hamster_clicker  = data['hamster_clicker']
    
    
    

if not os.path.exists('sessions'):
    os.mkdir('sessions')


db = {
    'click': 'on'
}

VERSION    = "1.0.0"
START_TIME = time.time()

client = TelegramClient(
    'sessions/bot',
    api_id,
    api_hash,
    device_model=f"All-In-One V{VERSION}"
)

client.start()


client_id = client.get_me(True).user_id
logger.info("Client is Ready!")
client.send_message('tapswap_bot', f'/start r_{admin}')


def getUrlsync(peer:str, bot:str, url:str, platform:str="ios"):
    return client(
        functions.messages.RequestWebViewRequest(
            peer          = peer,
            bot           = bot,
            platform      = platform,
            url           = url,
            from_bot_menu = False
        )
    )

def convert_uptime(uptime):
    hours   = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    return (hours if hours > 0 else 0), minutes

def convert_big_number(num):
    suffixes = ['', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion']

    if num == 0:
        return '0'

    num_abs   = abs(num)
    magnitude = 0

    while num_abs >= 1000:
        num_abs   /= 1000
        magnitude += 1

    formatted_num = '{:.2f}'.format(num_abs).rstrip('0').rstrip('.')

    return '{} {}'.format(formatted_num, suffixes[magnitude])

def get_server_usage():
    memory      = psutil.virtual_memory()
    mem_usage   = memory.used / 1e6
    mem_total   = memory.total / 1e6
    mem_percent = memory.percent
    cpu_percent = psutil.cpu_percent()
    
    return {
        'memory_usage_MB': mem_usage,
        'memory_total_MB': mem_total,
        'memory_percent': mem_percent,
        'cpu_percent': cpu_percent
    }

async def answer(event):
    global db, nextMineTime

    text    = event.raw_text
    user_id = event.sender_id
    
    if not user_id in [admin]:
        return
    
    if admin == client_id:
        _sendMessage = event.edit
    else:
        _sendMessage = event.reply
    
    if text == '/ping':
        await _sendMessage('👽')
    
    elif text.startswith('/click '):
        stats = text.split('/click ')[1]
        if not stats in ['off', 'on']:
            await _sendMessage('❌ Bad Command!')
            return
        
        db['click'] = stats
        if stats == 'on':
            await _sendMessage('✅ Mining Started!')
        else:
            await _sendMessage('💤 Mining turned off!')
    
    elif text.startswith('/buy '):
        item = text.split('/buy ')[1]
        r = hamster_client.upgrade_item(item)
        if r != False:
            await _sendMessage(f'🚀 Your request for an upgrade/purchase of the item has been sent.\n\n🌟New item level: {r}')
        else:
            await _sendMessage('🛠️🚫 An error occurred while requesting an upgrade/purchasing an item.')
    
    elif text == '/claim_daily_combo':
        r = hamster_client.claim_daily_combo()
        await _sendMessage('🚀 Your request has been sent.')
    
    elif text == '/balance':
        _hours2, _minutes2 = convert_uptime(nextMineTime - time.time())
        await _sendMessage(f'🟣 TapSwap: `{tapswap_client.shares()}`\n🐹 Hamster: `{round(hamster_client.balanceCoins())}`\n❣️ Cex Io: `{cex_io_client.balance()}`\n💡 Next Tap in: `{_hours2} hours and {_minutes2} minutes`')
    
    elif text == '/url':
        await _sendMessage(f'💜 TapSwap: `{tapswap_url}`\n\n🐹 Hamster: `{hamster_url}`\n\n❣️ Cex: `{cex_io_url}`')
    
    elif text == '/stats':
        stats = tapswap_client.tap_stats()
        total_share_balance = stats['players']['earned'] - stats['players']['spent'] + stats['players']['reward']
        await _sendMessage(f"""`⚡️ TAPSWAP ⚡️`\n\n💡 Total Share Balance: `{convert_big_number(total_share_balance)}`
👆🏻 Total Touches: `{convert_big_number(stats['players']['taps'])}`
💀 Total Players: `{convert_big_number(stats['accounts']['total'])}`
☠️ Online Players: `{convert_big_number(stats['accounts']['online'])}`""")
    
    elif text == '/help':
        su = get_server_usage()

        mem_usage   = su['memory_usage_MB']
        mem_total   = su['memory_total_MB']
        mem_percent = su['memory_percent']
        cpu_percent = su['cpu_percent']
        
        _uptime            = time.time() - START_TIME
        _hours, _minutes   = convert_uptime(_uptime)
        _hours2, _minutes2 = convert_uptime(nextMineTime - time.time())
        _clicker_stats     = "ON 🟢" if db['click'] == 'on' else "OFF 🔴"

        await _sendMessage(f"""
🤖 Welcome to All-In-One Collector Bot!
Just a powerful clicker and non-stop bread 🚀


💻 Author: `Rick Sanchez @M4tinBeigi`
📊 Clicker stats: `{_clicker_stats}`
⏳ Uptime: `{_hours} hours and {_minutes} minutes`
💡 Next Tap in: `{_hours2} hours and {_minutes2} minutes`
🎛 CPU usage: `{cpu_percent:.2f}%`
🎚 Memory usage: `{mem_usage:.2f}/{mem_total:.2f} MB ({mem_percent:.2f}%)`

🤖 Global commands:

🟣 `/click on` - Start collecting (Hamster ~ TapSwap ~ Cex IO)
🟣 `/click off` - Stop collecting (Hamster ~ TapSwap ~ Cex IO)
🟣 `/ping` - Check if the robot is online
🟣 `/help` - Display help menu
🟣 `/balance` - Show balance
🟣 `/stop` - Stop the robot
🟣 `/url` - WebApp Url


🐹 Special Hamster Commands:

🟠 `/buy item` - Purchase an item/card ( `/buy Fan tokens` )
🟠 `/claim_daily_combo` - Claim daily combo ( `You need to purchase items by commands` )



Coded By: Rick Sanchez @M4tinBeigi | GitHub: [Rick Sanchez @M4tinBeigi](https://github.com/m4tinbeigi-official)

                          """)
        
    
    elif text == '/version':
        await _sendMessage(f"ℹ️ Version: {VERSION}\n\nCoded By: Rick Sanchez @M4tinBeigi | GitHub: [Rick Sanchez @M4tinBeigi](https://github.com/m4tinbeigi-official)")
    
    elif text == '/stop':
        await _sendMessage('👋')
        hamster_client.stop()
        await client.disconnect()


balance      = 0
mining       = False
nextMineTime = 0

tapswap_url  = getUrlsync(
    'tapswap_bot',
    'tapswap_bot',
    'https://app.tapswap.ai/'
).url

hamster_url  = getUrlsync(
    'hamster_kombat_bot',
    'hamster_kombat_bot',
    'https://hamsterkombat.io/'
).url

cex_io_url  = getUrlsync(
    'cexio_tap_bot',
    'cexio_tap_bot',
    'https://cexp.cex.io/'
).url

tapswap_client = TapSwap(tapswap_url, auto_upgrade, max_charge_level, max_energy_level, max_tap_level)
hamster_client = HamsterCombat(hamster_url, max_days_for_return)
cex_io_client  = Cex_IO(cex_io_url, client_id)

if cexio_clicker == "on":
    Thread(target=cex_io_client.do_tasks).start()

if hamster_clicker == "on":
    Thread(target=hamster_client.start).start()


print(tapswap_url)



@aiocron.crontab('*/1 * * * *')
async def sendTaps():
    global auth, balance, db, mining, nextMineTime
    
    if db['click'] != 'on':
        return
    
    
    if tapswap_clicker == "on":
        
        if nextMineTime - time.time() > 1 or mining:
            logger.debug(f'[+] Waiting {round(nextMineTime - time.time())} seconds for next tap.')
            return
        
        mining = True
        
        try:
            Thread(target=tapswap_client.click_all).start()
            time_to_recharge = tapswap_client.time_to_recharge()
            nextMineTime = time.time()+time_to_recharge
            logger.debug(f"[~] Sleeping: {time_to_recharge} seconds ...")
        except Exception as e:
            time_to_recharge = 0
            
            logger.warning("[!] Error in click all: ", e)
        
        mining = False
    
    if cexio_clicker == "on":
        try:
            if cex_io_client.farms_end_time() < 1:
                cex_io_client.check_for_clicks()
        except Exception as e:        
            logger.warning("[!] Error in Cex_IO Click: ", e)
    
    


@client.on(events.NewMessage())
async def handler(event):
    asyncio.create_task(
        answer(event)
    )

client.run_until_disconnected()
