from abc import abstractmethod, ABC


class MessageBusInterface(ABC):
    @abstractmethod
    async def dispatch(self, message: object) -> None:
        pass


class EventBus(MessageBusInterface):
    def __init__(self) -> None:
        self.__subscribers: dict[type, list[callable]] = {}

    async def dispatch(self, message: object) -> None:
        message_type = type(message)
        if message_type in self.__subscribers:
            for subscriber in self.__subscribers[message_type]:
                await subscriber(message)

    def subscribe(self, message_type: type, subscriber: callable) -> None:
        if message_type not in self.__subscribers:
            self.__subscribers[message_type] = []
        self.__subscribers[message_type].append(subscriber)
