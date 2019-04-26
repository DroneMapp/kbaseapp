import asyncio
import sys

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError
from prettyconf import config


def register_method(self, name):
    def decorator(method):
        method.wamp_name = name
        return method
    return decorator



class WampApp(ApplicationSession):
    PRINCIPAL = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_status = 0
        self.init()
        self.methods = {}

        for thing_name in dir(self):
            thing = getattr(self, thing_name)
            method_name = getattr(thing, 'wamp_name', None)
            if method_name:
                self.methods[method_name] = method

    def init(self):
        pass

    def onOpen(self, *args, **kwargs):
        print('Opened.')
        super().onOpen(*args, **kwargs)

    def onWelcome(self, *args, **kwargs):
        print('Welcome message received.')
        super().onWelcome(*args, **kwargs)

    def onConnect(self):
        print("Client session connected. Starting WAMP-Ticket authentication on realm '{}' as principal '{}' ..".format(
            self.config.realm, PRINCIPAL)
        )
        self.join(self.config.realm, [u"ticket"], self.PRINCIPAL)

    async def onJoin(self, details):
        last_exception = None
        for counter in range(0, 3):
            if counter > 0:
                await asyncio.sleep(5)

            try:
                for method_name, method in self.methods.items():
                    await self.register(method, method_name)
            except ApplicationError as e:
                last_exception = e
                continue
            else:
                print("All methods registered")
                break
        else:
            print(f"Could not register some methods: {last_exception}")
            self.exit_status = 10
            self.disconnect()

    def onChallenge(self, challenge):
        if challenge.method == u"ticket":
            print("WAMP-Ticket challenge received: {}".format(challenge))
            return config('WAMPYSECRET')
        else:
            raise Exception("Invalid authmethod {}".format(challenge.method))

    def onLeave(self, *args, **kwargs):
        # 1 - leave
        super().onLeave(*args, **kwargs)
        print('Left.')

    def onDisconnect(self):
        # 2- disconnect
        super().onDisconnect()
        print("Disconnected.")

    def onClose(self, *args, **kwargs):
        # 3- close
        super().onClose(*args, **kwargs)
        print('Closed.')
        sys.exit(self.exit_status)

    @classmethod
    def run(cls):
        url = config('URL', default='ws://crossbar.dronemapp.com:80/ws')
        realm = config('REALM', default='kotoko')

        runner = ApplicationRunner(url, realm)

        try:
            runner.run(cls)
        except OSError as ex:
            print('OSError:', ex)
            sys.exit(100)