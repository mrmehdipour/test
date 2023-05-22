import os
import asyncio
from metaapi_cloud_sdk import MetaApi
from metaapi_cloud_sdk.clients.metaApi.tradeException import TradeException
from datetime import datetime

# Note: for information on how to use this example code please read https://metaapi.cloud/docs/client/usingCodeExamples

token = os.getenv('TOKEN') or 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI1ZDhlNWNiM2MwNzI0OWM5ZjlmOTUzMGM3ZWM5YWRlMCIsInBlcm1pc3Npb25zIjpbXSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6IjVkOGU1Y2IzYzA3MjQ5YzlmOWY5NTMwYzdlYzlhZGUwIiwiaWF0IjoxNjg0NzQ0ODM4fQ.AzAVnxHXZWDWVqa0J0b5iM0bm7xxO9DjhuGLLHNpgQNtj6xLDRPAhJuyFP5ueaEgdygfH5jemurSucRsCKxGLmQB-cc4NJ8RHl3vj_H5HyS3hsw0fvC2YzS3rYI3KJnhAuXbAYag_wowMKx3Wvpz_u1_1gBKx1I7qV1_C3YfqtsGtcOLDD8Ik7eSX-Ssnj6e1xIgpy5o5J4EWC7Ph2FnXtILFKPcVcaqkBQ4IJziIv3cLGbSBwTBxgMX9u49Z-VqxbQZMiE7bsWAwV1JI2Se3FH9FKgITtRnhdmVn0kdnu80HUim0wvuO6FZKCdoXdfFkBOvxc9OXm8YLE8b4Kz0kWR84Ye6lFaL26e39plkYaVXMnRxwKIcPZLSWYvdnnq6WpGmEh49Ec4R8R_IGlVI1ZA9PB3_uAi2UrSoMS6q7dyNU9kYoNFg6vO7NrhMcb8K607xN-T6vzOLpYu_em7P1k1r5xwlrm6YSCPE-XmN5qoq9Kpem9ipmk8DCUflPcHR00Yc4y56I9ViutExR0CPLe0HpDMJ79DTPhWjMlN4Kuchg5PMpVVHYoD1JOeznuXrsWl486pb3BRRf7gpTpOckETLj1dIqANIrglasWTFAlN8i3HVRBosxPjs3sFi54kC9dY6Q7n7XZrqmyOMNJI5hayHA-29z1S4RP5LLkJaVQ4'
accountId = os.getenv('ACCOUNT_ID') or '04b1b5d4-2f8e-4f51-a3cd-5b583dd11c90'


async def test_meta_api_synchronization():
    api = MetaApi(token)
    try:
        account = await api.metatrader_account_api.get_account(accountId)
        initial_state = account.state
        deployed_states = ['DEPLOYING', 'DEPLOYED']

        if initial_state not in deployed_states:
            #  wait until account is deployed and connected to broker
            print('Deploying account')
            await account.deploy()

        print('Waiting for API server to connect to broker (may take couple of minutes)')
        await account.wait_connected()

        # connect to MetaApi API
        connection = account.get_streaming_connection()
        await connection.connect()

        # wait until terminal state synchronized to the local state
        print('Waiting for SDK to synchronize to terminal state (may take some time depending on your history size)')
        await connection.wait_synchronized()

        # access local copy of terminal state
        print('Testing terminal state access')
        terminal_state = connection.terminal_state
        print('connected:', terminal_state.connected)
        print('connected to broker:', terminal_state.connected_to_broker)
        print('account information:', terminal_state.account_information)
        print('positions:', terminal_state.positions)
        print('orders:', terminal_state.orders)
        print('specifications:', terminal_state.specifications)
        print('EURUSD specification:', terminal_state.specification('EURUSD'))
        print('EURUSD price:', terminal_state.price('EURUSD'))

        # access history storage
        history_storage = connection.history_storage
        print('deals:', history_storage.deals[-5:])
        print('deals with id=1:', history_storage.get_deals_by_ticket('1'))
        print('deals with positionId=1:', history_storage.get_deals_by_position('1'))
        print('deals for the last day:', history_storage.get_deals_by_time_range(
            datetime.fromtimestamp(datetime.now().timestamp() - 24 * 60 * 60), datetime.now()))

        print('history orders:', history_storage.history_orders[-5:])
        print('history orders with id=1:', history_storage.get_history_orders_by_ticket('1'))
        print('history orders with positionId=1:', history_storage.get_history_orders_by_position('1'))
        print('history orders for the last day:', history_storage.get_history_orders_by_time_range(
            datetime.fromtimestamp(datetime.now().timestamp() - 24 * 60 * 60), datetime.now()))

        # calculate margin required for trade
        print('margin required for trade', await connection.calculate_margin({
            'symbol': 'GBPUSD',
            'type': 'ORDER_TYPE_BUY',
            'volume': 0.1,
            'openPrice': 1.1
        }))

        # trade
        print('Submitting pending order')
        try:
            result = await connection.create_limit_buy_order('GBPUSD', 0.07, 1.0, 0.9, 2.0,
                                                             {'comment': 'comm', 'clientId': 'TE_GBPUSD_7hyINWqAlE'})
            print('Trade successful, result code is ' + result['stringCode'])
        except Exception as err:
            print('Trade failed with error:')
            print(api.format_error(err))

        if initial_state not in deployed_states:
            # undeploy account if it was undeployed
            print('Undeploying account')
            await account.undeploy()

    except Exception as err:
        print(api.format_error(err))
    exit()

asyncio.run(test_meta_api_synchronization())
