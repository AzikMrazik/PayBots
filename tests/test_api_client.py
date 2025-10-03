import pytest
from aioresponses import aioresponses

from api_client import RefeeApiClient, RefeeApiError


@pytest.mark.asyncio
async def test_precounters_success():
    client = RefeeApiClient("test", base_url="https://api.refee.bot")
    with aioresponses() as mocked:
        mocked.post("https://api.refee.bot/precountOrder", payload={"priceUSDT": 1.23})
        mocked.post("https://api.refee.bot/precountBandwidth", payload={"priceUSDT": 0.45})

        order = await client.precount_order({"x": 1})
        bw = await client.precount_bandwidth({"y": 2})

        assert order["priceUSDT"] == 1.23
        assert bw["priceUSDT"] == 0.45


@pytest.mark.asyncio
async def test_error_raises():
    client = RefeeApiClient("test")
    with aioresponses() as mocked:
        mocked.post("https://api.refee.bot/buyenergy", status=400, payload={"message": "bad"})
        with pytest.raises(RefeeApiError):
            await client.buy_energy({"ownerAddress": "T...", "energyAmount": "10"})

