"""Daily raid gambit refresh loop."""

import asyncio

import lib.config as config
from lib.raid_pool_utils import current_gambit_refresh_interval, refresh_gambits


async def gambit_refresh_task():
    """Refresh daily raid gambits from WynnSource with burst/slow cadence."""
    print(
        f"[Gambit refresh] task started, rotation={config.GAMBIT_ROTATION_HOUR_ET}:00 ET, "
        f"base={config.GAMBIT_REFRESH_BASE_INTERVAL}s fast={config.GAMBIT_REFRESH_FAST_INTERVAL}s"
    )
    while True:
        try:
            result = await refresh_gambits()
            if "error" in result:
                print(f"[Gambit refresh] failed: {result['error']}")
            else:
                print(
                    f"[Gambit refresh] ok gambits={result.get('gambits', 0)} "
                    f"rotation={result.get('rotation_start')}->{result.get('rotation_end')}"
                )
        except Exception as error:
            print(f"[Gambit refresh] unexpected error: {type(error).__name__}: {error}")

        next_interval = current_gambit_refresh_interval()
        print(f"[Gambit refresh] sleeping {next_interval}s")
        await asyncio.sleep(next_interval)
