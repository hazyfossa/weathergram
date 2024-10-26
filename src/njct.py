from contextlib import contextmanager
from typing import Annotated, Callable, Literal, overload
from typing import Protocol as Protocol  # re-export

from attrs import define, field
from loguru import logger

type Auto = Annotated[None, "Automatically assigned value."]

type Dynamic[Value] = Callable[..., Value]
type ProtocolFor[Object] = type[Object]
type LoaderFor[Object: object] = ProtocolFor[Object] | Dynamic[Object]


@define
class Implementation[Object: object]:
    init: LoaderFor[Object]
    name: str

    @staticmethod
    def dynamic_priority(field: int | Dynamic[int]) -> int:
        return field() if isinstance(field, Callable) else field

    priority: int = field(default=1, converter=dynamic_priority)

    def __repr__(self) -> str:
        return f"'{self.name}' implementation"


@define
class Provider[Object: object]:
    name: str
    inject: ProtocolFor[
        Object
    ]  # This is a syntax-hack to replace the inject[`Provider`] generic type, which is not supported (in python) yet
    implementations: dict[str, Implementation[Object]]

    def register_implementation(self, implementation: Implementation, override: bool = False) -> None:
        name = implementation.name

        if not override and name in self.implementations:
            raise KeyError("This name is already taken. If replacing it is the intended behaviour, set override to True.")

        self.implementations[name] = implementation

    def __getitem__(self, name: str) -> LoaderFor[Object]:
        return self.implementations[name].init

    def __call__(self, *args, **kwargs) -> Object:
        if len(self.implementations) == 0:
            raise NotImplementedError("This provider isn't implemented anywhere.")

        implementations = sorted(self.implementations.values(), key=lambda i: i.priority, reverse=True)

        for i in implementations:
            try:
                return i.init(*args, **kwargs)
            except ImplementationUnavailable as e:
                log = logger.error if e.is_error else logger.debug
                log("{} of {} unavailable, skipping.", i, self)
            except Exception:
                logger.exception(
                    "While instantiating {} of {}, the following error occurred: ",
                    i,
                    self,
                )

        raise RuntimeError(f"Cannot find a valid implementation for {self}.")

    def __repr__(self) -> str:
        return f"'{self.name} provider'"


# type inject[Object, Provider: Provider[Object]] = ProtocolFor[Object]  # Requires HKT's in python.


class ImplementationUnavailable(Exception):
    def __init__(self, reason: str | None = None, is_error: bool = False) -> None:
        self.reason = reason
        self.is_error = is_error


def provider[T: object](name: str | Auto = None) -> Callable[[ProtocolFor[T]], Provider[T]]:
    def decorator(cls: ProtocolFor[T]) -> Provider[T]:
        provider = Provider(name or cls.__name__, cls, {})

        logger.debug("Registered {}", provider)

        return provider

    return decorator


@overload
def implements[Object: object](
    provider: Provider[Object],
    name: str | None = None,
    priority: int | Callable[..., int] | Auto = None,
    coerce: Literal[False] = False,
) -> Callable[[LoaderFor[Object]], LoaderFor[Object]]: ...


@overload
def implements[Object: object](
    provider: Provider[Object],
    name: str | None = None,
    priority: int | Callable[..., int] | Auto = None,
    coerce: Literal[True] = True,
) -> Callable: ...


def implements[Object: object](
    provider: Provider[Object],
    name: str | None = None,
    priority: int | Callable[..., int] | Auto = None,
    coerce: bool = False,
):
    def decorator(cls: LoaderFor[Object], /):
        implementation = Implementation(cls, name or cls.__name__, priority or 1)
        provider.register_implementation(implementation)

        logger.debug("Registered {} of {}.", implementation, provider)

        return cls

    return decorator


# This can be replaced with importlib.util.LazyLoader
# if the text inside __import__ is typed as a forward reference to the module.
# Unfortunately, as of right now, it is not, so we'll have to use this and import manually.
@contextmanager
def require_module():
    try:
        yield
    except ModuleNotFoundError:
        raise ImplementationUnavailable


def import_implementation(
    provider: Provider,
    module: str,
    attr: str | None = None,
    name: str | Auto = None,
    priority: int | Auto = None,
):
    def lazy_loader():  # This can be replaced with importlib.LazyLoader, see above.
        with require_module():
            return __import__(module)

    implements(provider, name or module, priority)(
        (lambda: getattr(lazy_loader(), attr)) if attr else lazy_loader,
    )


__all__ = [
    "provider",
    "implements",
    "import_implementation",
    "Protocol",
    "ImplementationUnavailable",
]
