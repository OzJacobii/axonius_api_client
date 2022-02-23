# -*- coding: utf-8 -*-
"""Tools for working with SSL certificate files."""
import logging
import pathlib
from typing import Any, List, Optional, Tuple, TypeVar, Union

from .exceptions import PathError, PathNotFoundError
from .utils import bytes_to_str, check_type, str_to_bytes, type_str

LOG: logging.Logger = logging.getLogger(__name__)
PathLike: TypeVar = TypeVar("PathLike", pathlib.Path, str, bytes)


def read_bytes(path: PathLike, exts: Optional[List[str]] = None) -> Tuple[pathlib.Path, bytes]:
    """Read data from a file as bytes.

    Args:
        path (PathLike): str or pathlib.Path object to file to read data from

    Returns:
        Tuple[pathlib.Path, bytes]: resolved path from value, data from path as bytes
    """
    path = pathify(path=path, as_file=True, exts=exts)
    data = path.read_bytes()
    return path, data


def find_file_exts(
    path: PathLike, exts: List[str], error: bool = True
) -> Tuple[pathlib.Path, List[pathlib.Path]]:
    """Pass."""
    path = pathify(path=path, as_dir=error)
    files = [x for x in path.glob("*") if x.suffix in exts] if path.is_dir() else []

    if not files and error:
        raise PathNotFoundError(f"Supplied path {str(path)!r} has no files with extensions {exts}")

    return path, files


def write_bytes(
    path: PathLike, content: Union[str, bytes], strict: bool = True, **kwargs
) -> pathlib.Path:
    """Write data to a file."""
    content = str_to_bytes(value=content, strict=strict)
    path = create_file(path=path, **kwargs)
    path.write_bytes(data=content)
    return path


def is_existing_file(path: Any) -> bool:
    """Check if the supplied value refers to an existing file."""
    if isinstance(path, pathlib.Path) and path.is_file():
        return True

    if isinstance(path, (str, bytes)):
        return pathify(path=path).is_file()

    return False


def octify(
    value: Optional[Union[int, str, bytes]],
    allow_empty: bool = False,
    fallback: Union[Optional[int], Tuple[Optional[int], Optional[str]]] = (None, None),
    oct_len: int = 5,
    error: bool = True,
) -> Tuple[Optional[int], Optional[str]]:
    """Coerce str or bytes into base 8 octal int."""

    def get_fallback():
        return (
            fallback if (isinstance(fallback, tuple) and len(fallback) == 2) else (fallback, None)
        )

    str_ex = "like '0700' or '0o700'"
    int_ex = "like 448"
    err = f"Value must be str/bytes {str_ex} or base 8 int {int_ex}, not {type_str(value)}"

    if value is None:
        if not allow_empty:
            raise ValueError(f"{err}\nNone not allowed")
        return get_fallback()

    try:
        resolved: Union[int, str, bytes] = value

        if isinstance(value, (str, bytes)) and value:
            try:
                resolved: int = int(value, 8)
            except Exception as exc:
                raise ValueError(f"{err}\nError during 'int({value!r}, 8)':\n{exc}")
        elif isinstance(value, int):
            resolved: int = value
        else:
            raise TypeError(f"{err}")

        oval: str = oct(resolved)
        ovlen: int = len(oval)
        LOG.debug(f"Resolved {type_str(value)} to octal {oval!r}, int {resolved!r}")

        if oct_len and ovlen != oct_len:
            raise ValueError(
                f"{err}\nOctal result {oval!r} must be {oct_len} characters, not {ovlen}"
            )
        return resolved, oval
    except Exception:
        LOG.exception(f"Error while converting value {value!r} to octal")
        if error:
            raise

    return get_fallback()


def pathify(
    path: PathLike,
    resolve: bool = True,
    expanduser: bool = True,
    as_file: bool = False,
    as_dir: bool = False,
    strict: bool = True,
    encoding: str = "utf-8",
    exts: Optional[List[str]] = None,
) -> pathlib.Path:
    """Convert a str into a fully resolved & expanded Path object."""
    check_type(value=path, exp=(str, bytes, pathlib.Path))

    if isinstance(path, bytes):
        path = bytes_to_str(value=path, strict=strict, encoding=encoding)

    if isinstance(path, str):
        resolved = pathlib.Path(path.splitlines()[0])
    else:
        resolved = path

    if expanduser:
        resolved = resolved.expanduser()

    if resolve:
        resolved = resolved.resolve()

    vstr = f"(supplied {type_str(path)})"
    rstr = f"Resolved path {str(resolved)!r}"
    if as_file and not resolved.is_file():
        raise PathNotFoundError(f"{rstr} does not exist as a file {vstr}")

    if as_dir and not resolved.is_dir():
        raise PathNotFoundError(f"{rstr} does not exist as a directory {vstr}")

    if isinstance(exts, list) and exts and resolved.suffix not in exts:
        raise PathError(f"{rstr} with extension {resolved.suffix!r} is not one of {exts}")

    return resolved


def create_file(
    path: PathLike,
    overwrite: bool = False,
    make_parent: bool = True,
    make_file: bool = True,
    perm_file: Optional[Union[int, str, bytes]] = "0600",
    perm_parent: Optional[Union[int, str, bytes]] = "0700",
    error: bool = True,
) -> pathlib.Path:
    """Create a file at a path.

    Args:
        path (PathLike): str of path or pathlib.Path object to file to create
        overwrite (bool, optional): error if the file exists already
        make_parent (bool, optional): make the parent directory of value if it does not exist
        make_file (bool, optional): create an empty file if it does not exist
        perm_file (Optional[Union[int, str, bytes]], optional): permissions to set on file
            when creating
        perm_parent (Optional[Union[int, str, bytes]], optional): permissions to set on
            parent directory when creating
        error (bool, optional): raise errors, otherwise just return the resolved path

    Raises:
        PathError: if value exists as file and overwrite is False
        PathNotFoundError: if parent directory of value does not exist and make_parent is False

    Returns:
        pathlib.Path: the resolved path of value
    """
    resolved = pathify(path=path)
    perm_file_int, perm_file_oct = octify(value=perm_file, allow_empty=True, error=error)
    perm_parent_int, perm_parent_oct = octify(value=perm_parent, allow_empty=True, error=error)

    rstr = f"Resolved path {str(resolved)!r}"
    pstr = f"Parent directory {str(resolved.parent)!r} of {rstr}"

    try:
        if resolved.is_file() and overwrite is False:
            raise PathError(f"{rstr} already exists as a file and overwrite is False")

        if not resolved.parent.is_dir():
            if not make_parent:
                raise PathNotFoundError(f"{pstr} does not exist and make_parent is False")
            LOG.debug(f"Creating {pstr}")
            resolved.parent.mkdir(parents=True, exist_ok=True)

        if not resolved.is_file() and make_file:
            LOG.debug(f"Creating {rstr}")
            resolved.touch()

        if isinstance(perm_parent_int, int) and resolved.parent.is_dir():
            LOG.debug(f"{pstr} chmod to {perm_parent_oct}")
            resolved.parent.chmod(mode=perm_parent_int)

        if isinstance(perm_file_int, int) and resolved.is_file():
            LOG.debug(f"{rstr} chmod to {perm_file_oct}")
            resolved.chmod(mode=perm_file_int)

    except Exception as exc:
        LOG.exception(f"{rstr} Error creating file: {exc}")
        if error:
            raise

    return resolved
