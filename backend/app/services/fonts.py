"""Locate a CJK-capable font for ReportLab and Matplotlib.

Font files are not vendored. Docker images install `fonts-noto-cjk`;
Windows typically has Malgun Gothic.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\malgunsl.ttf",
    r"C:\Windows\Fonts\NotoSansCJKkr-Regular.otf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NotoSansCJKkr-Regular.otf",
)

REGISTERED_FONT_NAME = "FactoryHRCJK"


@dataclass(frozen=True)
class CjkFont:
    path: str | None
    family: str
    available: bool
    warning: str | None


def find_cjk_font_path() -> str | None:
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def resolve_cjk_font() -> CjkFont:
    path = find_cjk_font_path()
    if path is None:
        warning = (
            "CJK font not found. Korean labels may not render. "
            "Install Noto Sans CJK (Debian/Ubuntu: fonts-noto-cjk) "
            "or use a system Korean font such as Malgun Gothic."
        )
        logger.warning(warning)
        return CjkFont(
            path=None, family="Helvetica", available=False, warning=warning
        )
    return CjkFont(path=path, family=REGISTERED_FONT_NAME, available=True, warning=None)
