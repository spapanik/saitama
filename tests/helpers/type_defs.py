from collections.abc import Callable
from contextlib import AbstractContextManager

StrFactory = Callable[[], str]
IntFactory = Callable[[], int]

MaxQueriesFixture = Callable[[int], AbstractContextManager[None]]
