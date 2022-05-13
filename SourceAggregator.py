import requests
import json

import numpy as np
import ccxt
import pprint
pprint.sorted = lambda x, key=None: x
from pprint import pprint


expiry_aliases = {
    None: 'PERP',
    '': 'PERP',
    'swap': 'PERP',
    'PERPETUAL': 'PERP',
    'CURRENT_QUARTER': 'CQ',
    'NEXT_QUARTER': 'NQ',
    'next_quarter': 'NQ',
    'next_week': 'NW',
    'quarter': 'CQ',
    'this_week': 'CW',
}

ctr_type_alias_from_quote = {
    'USDT': 'R',
    'USD': 'i'.upper(),
}


class SourcesAggregator:
    """Sources aggregator for FFT's models.

    Shell above the ccxt package and exchanges REST-API,
    provides methods for useful sources auto-collecting"""

    def __init__(self, *args, **kwargs):
        self.bs_ccxt_client = ccxt.binance()
        self.bf_ccxt_client = ccxt.binanceusdm()
        self.bcf_ccxt_client = ccxt.binancecoinm()
        self.okx_ccxt_client = ccxt.okx()
        self.hb_ccxt_client = ccxt.huobi()
        self.ftx_ccxt_client = ccxt.ftx()
        self.cb_ccxt_client = ccxt.coinbase()
        self.bs_markets = self.bs_ccxt_client.fetch_markets()
        self.bf_markets = self.bf_ccxt_client.fetch_markets()
        self.bcf_markets = self.bcf_ccxt_client.fetch_markets()
        self.okx_markets = self.okx_ccxt_client.fetch_markets()
        self.hb_markets = self.hb_ccxt_client.fetch_markets()
        self.ftx_markets = self.ftx_ccxt_client.fetch_markets()
        self.cb_markets = self.cb_ccxt_client.fetch_markets()

    @staticmethod
    def make_source(*, base, quote, exchange, inst_type,
                    vol24usd, ctr_type_alias=None, expiry_alias=None,
                    ctr_size=None, ctr_size_units=None):
        name_parts = [base, quote]
        if inst_type == 'future':
            name_parts.append(expiry_alias)
        unified_name = '_'.join(name_parts)
        source = {
            'unified_symbol_name': unified_name,
            'base': base,
            'quote': quote,
            'exchange': exchange,
            'inst_type': inst_type,
            'ctr_type_alias': ctr_type_alias,
            'expiry_alias': expiry_alias,
            'ctr_size': ctr_size,
            'ctr_size_units': ctr_size_units,
            'vol24_usd': vol24usd,
        }

        return source

    def get_bs_sources(self, base):
        quotes = ['USDT', 'BUSD']
        sources = []
        for market in filter(lambda x:
                             x['active'] is True
                             and x['base'] == base
                             and x['quote'] in quotes,
                             self.bs_markets):
            quote = market['quote']
            vol24usd = self.bs_ccxt_client.fetch_ticker(
                market['symbol'])['quoteVolume']
            sources.append(self.make_source(
                base=base, quote=quote, exchange='binance', inst_type='spot',
                vol24usd=vol24usd))
        assert len(sources) <= 2

        return sources

    def get_bf_sources(self, base):
        quotes = ['USDT', 'BUSD']
        sources = []
        for market in filter(lambda x:
                             x['active'] is True
                             and x['base'] == base
                             and x['quote'] in quotes,
                             self.bf_markets):
            quote = market['quote']
            vol24usd = self.bf_ccxt_client.fetch_ticker(
                market['symbol'])['quoteVolume']
            sources.append(self.make_source(
                base=base, quote=quote, exchange='binance_futures',
                inst_type='future', vol24usd=vol24usd, ctr_type_alias='R',
                expiry_alias=expiry_aliases[market['info']['contractType']],
                ctr_size=market['contractSize'], ctr_size_units=base))

        return sources

    def get_bcf_sources(self, base):
        quote = 'USD'
        sources = []
        for market in filter(lambda x:
                             x['active'] is True
                             and x['base'] == base
                             and x['quote'] == quote,
                             self.bcf_markets):
            ticker = self.bcf_ccxt_client.fetch_ticker(market['symbol'])
            vol24usd = ticker['baseVolume'] * ticker['average']
            sources.append(self.make_source(
                base=base, quote=quote, exchange='binance_coin_futures',
                inst_type='future', vol24usd=vol24usd,
                ctr_type_alias='i'.upper(),
                expiry_alias=expiry_aliases[market['info']['contractType']],
                ctr_size=market['contractSize'], ctr_size_units=quote))

        return sources

    def get_okx_sources(self, base):
        def get_vol24usd(ticker, inverse):
            if inverse is None:
                return ticker['quoteVolume']
            elif inverse is False:
                return float(ticker['info']['volCcy24h']) * ticker['average']
            elif inverse is True:
                return float(ticker['info']['volCcy24h']) * ticker['average']
            else:
                raise ValueError('inverse must be bool or NoneType')

        exchange_names = {
            'spot': 'okex_v5',
            'future': 'okex_v5_futures',
            'swap': 'okex_v5_swap',
        }
        quotes = ['USDT', 'USD']
        sources = []
        for market in filter(lambda x:
                             x['active'] is True
                             and x['base'] == base
                             and x['quote'] in quotes
                             and x['type'] in ['spot', 'future', 'swap'],
                             self.okx_markets):

            exchange = exchange_names[market['type']]
            quote = market['quote']
            ticker = self.okx_ccxt_client.fetch_ticker(market['symbol'])
            vol24usd = get_vol24usd(ticker, market['inverse'])
            make_source_kwargs = {'inst_type': market['type']}
            if market['type'] in ['future', 'swap']:
                make_source_kwargs.update({
                    'inst_type': 'future',
                    'ctr_type_alias': ctr_type_alias_from_quote[quote],
                    'expiry_alias': expiry_aliases[market['info']['alias']],
                    'ctr_size': market['contractSize'],
                    'ctr_size_units': market['info']['ctValCcy'],
                })
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        return sources

    def get_hb_sources(self, base):
        exchange_names = {
            ('spot', 'USDT'): 'huobi_global',
            ('swap', 'USD'): 'huobi_swap',
            ('swap', 'USDT'): 'huobi_usdt_swap',
            ('future', 'USD'): 'huobi_dm',
            ('future', 'USDT'): 'huobi_dm',
        }
        quotes = ['USDT', 'USD']
        sources = []
        for market in filter(lambda x:
                             x['active'] is True
                             and x['base'] == base
                             and x['quote'] in quotes,
                             self.hb_markets):

            exchange = exchange_names[(market['type'], market['quote'])]
            quote = market['quote']
            ticker = self.hb_ccxt_client.fetch_ticker(market['symbol'])
            if market['linear'] in (True, None):
                vol24usd = ticker['baseVolume'] * ticker['average']
            elif market['linear'] is False:
                vol24usd = ticker['quoteVolume'] * market['contractSize']
            make_source_kwargs = {'inst_type': market['type']}
            if market['type'] in ['future', 'swap']:

                if market['type'] == 'swap':
                    expiry_alias = 'PERP'
                else:
                    expiry_alias = expiry_aliases[market['info']['contract_type']]

                make_source_kwargs.update({
                    'inst_type': 'future',
                    'ctr_type_alias': ctr_type_alias_from_quote[quote],
                    'expiry_alias': expiry_alias,
                    'ctr_size': market['contractSize'],
                    'ctr_size_units': 'USD' if market['inverse'] is True
                    else base,
                })
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        return sources

    def get_ftx_sources(self, base):  # FIXMELATER (and so it will do)
        exchange_names = {
            ('spot', 'USD'): 'ftx',
            ('swap', 'USD'): 'ftx_futures',
            ('future', 'USD'): 'ftx_futures',
        }
        quote = 'USD'
        sources = []
        markets = list(filter(lambda x:
                              x['active'] is True
                              and x['base'] == base
                              and x['quote'] == quote,
                              self.ftx_markets))

        spot_markets = list(filter(lambda x: x['type'] == 'spot', markets))
        swap_markets = list(filter(lambda x: x['type'] == 'swap', markets))
        exp_markets = list(filter(lambda x: x['type'] == 'future', markets))

        assert len(spot_markets) <= 1
        assert len(swap_markets) <= 1
        assert len(exp_markets) <= 2

        for market in spot_markets:
            exchange = exchange_names[(market['type'], market['quote'])]
            vol24usd = float(market['info']['volumeUsd24h'])
            make_source_kwargs = {
                'inst_type': 'spot',
                'ctr_type_alias': None,
                'expiry_alias': None,
                'ctr_size': None,
                'ctr_size_units': None,
            }
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        for market in swap_markets:
            exchange = exchange_names[(market['type'], market['quote'])]
            vol24usd = float(market['info']['volumeUsd24h'])
            make_source_kwargs = {
                'inst_type': 'future',
                'ctr_type_alias': 'R',
                'expiry_alias': 'PERP',
                'ctr_size': market['contractSize'],
                'ctr_size_units': base,
            }
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        if len(exp_markets) == 1:

            market = exp_markets[0]

            exchange = exchange_names[(market['type'], market['quote'])]
            vol24usd = float(market['info']['volumeUsd24h'])
            make_source_kwargs = {
                'inst_type': 'future',
                'ctr_type_alias': 'R',
                'expiry_alias': 'CQ',
                'ctr_size': market['contractSize'],
                'ctr_size_units': base,
            }
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        elif len(exp_markets) == 2:

            exp_tstamps = np.array([i['expiry'] for i in exp_markets])
            cq_index = np.argmin(exp_tstamps)
            nq_index = np.argmax(exp_tstamps)

            market = exp_markets[cq_index]
            exchange = exchange_names[(market['type'], market['quote'])]
            vol24usd = float(market['info']['volumeUsd24h'])
            make_source_kwargs = {
                'inst_type': 'future',
                'ctr_type_alias': 'R',
                'expiry_alias': 'CQ',
                'ctr_size': market['contractSize'],
                'ctr_size_units': base,
            }
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

            market = exp_markets[nq_index]
            exchange = exchange_names[(market['type'], market['quote'])]
            vol24usd = float(market['info']['volumeUsd24h'])
            make_source_kwargs = {
                'inst_type': 'future',
                'ctr_type_alias': 'R',
                'expiry_alias': 'NQ',
                'ctr_size': market['contractSize'],
                'ctr_size_units': base,
            }
            sources.append(
                self.make_source(
                    base=base, quote=quote, exchange=exchange,
                    vol24usd=vol24usd, **make_source_kwargs))

        return sources

    def get_cb_sources(self, base):
        quote = 'USD'
        sources = []
        for market in filter(
                lambda x: x['base'] == base and x['quote'] == quote,
                self.cb_markets):
            cb_product_id = market['id']
            url_tpl = 'https://api.exchange.coinbase.com/products/{}/ticker'
            url = url_tpl.format(cb_product_id)
            response = requests.get(url)
            parsed = json.loads(response.content.decode('utf-8'))
            if 'volume' in parsed:
                vol24usd = float(parsed['volume']) * float(parsed['price'])

                sources.append(self.make_source(
                    base=base, quote=quote, exchange='coinbase', inst_type='spot',
                    vol24usd=vol24usd))

        assert len(sources) <= 1

        return sources

    def get_sources(self, base):
        sources = []
        sources.extend(self.get_bs_sources(base))
        sources.extend(self.get_bf_sources(base))
        sources.extend(self.get_bcf_sources(base))
        sources.extend(self.get_okx_sources(base))
        sources.extend(self.get_hb_sources(base))
        sources.extend(self.get_ftx_sources(base))
        sources.extend(self.get_cb_sources(base))

        return sorted(sources, key=(lambda x: x['vol24_usd']), reverse=True)

    def src_stats(self, base):
        raw_sources = self.get_sources(base)
        total_vol_usd = sum([s['vol24_usd'] for s in raw_sources])
        sources = []
        for rs in raw_sources:
            src = {
                'exchange': rs['exchange'],
                'symbol': rs['unified_symbol_name'],
                'percent': round(rs['vol24_usd'] / total_vol_usd * 100, 2),
                'vol24_kkusd': round(rs['vol24_usd'] / 1e6, 1),
            }
            if rs['inst_type'] == 'future':
                src.update({'ctr_size': str(rs['ctr_size']) + ' ' + rs['ctr_size_units']})
            sources.append(src)

        return sources