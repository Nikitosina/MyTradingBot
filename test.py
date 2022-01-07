import asyncio
import tinvest as ti
import tokens


async def main():
    async with ti.Streaming(tokens.TRADE_TOKEN) as streaming:
        await streaming.candle.subscribe('BBG0013HGFT4', ti.CandleResolution.min1)
        # await streaming.orderbook.subscribe('BBG0013HGFT4', 5)
        # await streaming.instrument_info.subscribe('BBG0013HGFT4')
        async for event in streaming:
            print(event)


asyncio.run(main())