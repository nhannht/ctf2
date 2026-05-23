from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from bcsfe import core
from bcsfe.core.game.catbase.cat import Talent


ROOT = Path(__file__).resolve().parent
BCSFE_ROOT = ROOT / "bcsfe"
CONFIG_PATH = BCSFE_ROOT / "config.yaml"
LOG_PATH = BCSFE_ROOT / "bcsfe.log"

CHECK_URL = "https://nyanko.blackpinker.com/check"
CHECK_COOKIE = "cf_clearance"
CHECK_TIMEOUT = 60

COUNTRY_CODE = core.CountryCode.from_code("en")
GAME_VERSION = core.GameVersion(150000)
TOTAL_CATS = 774
CHEETAH_ID = 673
MOVE_SPEED_UP_TALENT_ID = 27
MOVE_SPEED_UP_TALENT_LEVEL = 10


def init_bcsfe() -> None:
    core.set_config_path(core.Path(str(CONFIG_PATH)))
    core.set_log_path(core.Path(str(LOG_PATH)))
    core.core_data.init_data()


def make_save() -> core.SaveFile:
    save = core.SaveFile(cc=COUNTRY_CODE, load=False, gv=GAME_VERSION)
    save.cats = core.Cats([core.Cat.init(i) for i in range(TOTAL_CATS)])

    # Fresh modern saves default these to empty, but bcsfe still expects the
    # old fixed-width shape for menu unlock bookkeeping.
    save.menu_unlocks = [0] * 6
    save.unlock_popups_0 = [0] * 6
    return save


def apply_winning_state(save: core.SaveFile) -> None:
    cat = save.cats.cats[CHEETAH_ID]
    cat.unlocked = 1
    cat.gatya_seen = 1
    cat.current_form = 0
    cat.unlocked_forms = 1
    cat.upgrade.base = 20
    cat.max_upgrade_level.base = 50
    cat.catguide_collected = True
    cat.talents = [Talent(MOVE_SPEED_UP_TALENT_ID, MOVE_SPEED_UP_TALENT_LEVEL)]
    save.cats.chara_new_flags[CHEETAH_ID] = 0


def get_transfer_codes(save: core.SaveFile) -> tuple[str, str]:
    server = core.ServerHandler(save, print=False)
    if not server.create_new_account():
        raise RuntimeError("failed to provision a synthetic Battle Cats account")

    codes = server.get_codes(upload_managed_items=False)
    if codes is None:
        raise RuntimeError("failed to upload save and obtain transfer codes")
    return codes


def submit_to_checker(transfer_code: str, confirmation_code: str) -> dict[str, object]:
    cookie = os.environ.get("CF_CLEARANCE")
    if not cookie:
        raise RuntimeError("CF_CLEARANCE is required to submit to the checker")

    response = requests.post(
        CHECK_URL,
        files={
            "transfer_code": (None, transfer_code),
            "confirmation_code": (None, confirmation_code),
        },
        cookies={CHECK_COOKIE: cookie},
        timeout=CHECK_TIMEOUT,
    )
    response.raise_for_status()

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"checker returned non-JSON: {response.text[:200]!r}"
        ) from exc


def main() -> int:
    init_bcsfe()

    save = make_save()
    apply_winning_state(save)
    transfer_code, confirmation_code = get_transfer_codes(save)
    result = submit_to_checker(transfer_code, confirmation_code)

    print(
        json.dumps(
            {
                "transfer_code": transfer_code,
                "confirmation_code": confirmation_code,
                "result": result,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
