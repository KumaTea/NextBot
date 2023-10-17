import os

if os.name == 'posix':
    import uvloop
    uvloop.install()


from session import bot
from starting import starting


starting()


if __name__ == '__main__':
    bot.run()
