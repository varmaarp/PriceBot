from lbcapi import api
import urllib.parse
import logging
import time
import datetime

HMAC_KEY = ''
HMAC_SECRET = ''

MAX_PRICE_INR = 3395000
MIN_PRICE_INR = 3393000

PROVIDER_IMPS = 'BANK_TRANSFER_IMPS'
SLEEP_TIME = 1

conn = api.hmac(HMAC_KEY, HMAC_SECRET)

date = datetime.datetime.now()
logging.basicConfig(filename='logFile{datetime_val}.log'.format(datetime_val=date.strftime("%d%m%Y%H%M%S")),
                    level=logging.DEBUG)


def get_current_ads_info():
    response = conn.call('GET', '/api/ads/').json()
    data = response['data']
    ad_list = data['ad_list']
    price_dict = {}

    for ad in ad_list:
        ad_data = ad['data']
        ad_id = ad_data['ad_id']
        price = ad_data['price_equation']
        provider = ad_data['online_provider']

        if ad_id not in price_dict.keys():
            price_dict[ad_id] = {'price': price, 'provider': provider}

    return price_dict


def get_all_ads_selling_info(current_ad_ids):
    response = conn.call('GET', '/sell-bitcoins-online/INR/.json').json()
    selling_price_dict = {}
    selling_price_dict = read_selling_info_data(response['data'], selling_price_dict, current_ad_ids)

    '''
    while True:
        if 'pagination' in response.keys():
            pages = response['pagination']

            if 'next' in pages.keys():
                url = urllib.parse.urlparse(pages['next'])
                params = urllib.parse.parse_qs(url.query)
                response = conn.call('GET', '/sell-bitcoins-online/INR/.json', params=params).json()
                selling_price_dict = read_selling_info_data(response['data'], selling_price_dict)
            else:
                break
        else:
            break
    '''

    return selling_price_dict


def read_selling_info_data(data, selling_price_dict, current_ad_ids):
    for ad in data['ad_list']:
        ad_id = ad['data']['ad_id']
        price = ad['data']['temp_price']
        user = ad['data']['profile']['username']
        provider = ad['data']['online_provider']

        if ad_id in current_ad_ids:
            continue

        if ad_id not in selling_price_dict.keys():
            selling_price_dict[ad_id] = {'price': price, 'user': user, 'provider': provider}

    return selling_price_dict


def get_ad_with_imps_provider(ads):
    ads_with_matching_provider = {}
    for ad_id, ad_info in ads.items():
        if ad_info['provider'] == PROVIDER_IMPS:
            ads_with_matching_provider[ad_id] = ad_info['price']
    return ads_with_matching_provider


def update_ad_price(ad_id, price):
    response = conn.call('POST', '/api/ad-equation/{ad_id}/'.format(ad_id=ad_id),
                         params={'price_equation': price}).json()
    print(response)
    return 'error' not in response.keys()


def log_message(msg):
    print(msg)
    logging.debug(msg)


def run():
    current_ads = get_current_ads_info()
    ads_with_selected_provider = get_ad_with_imps_provider(current_ads)
    ad_ids = list(ads_with_selected_provider)

    if len(ads_with_selected_provider) < 1:
        print('No ads found.')
        return

    log_message('our range is from {min_val} to {max_val}'.format(min_val=MIN_PRICE_INR, max_val=MAX_PRICE_INR))

    prev_price = float(ads_with_selected_provider[ad_ids[0]])
    log_message('our starting price {price}'.format(price=prev_price))

    while True:
        all_selling_price_ads = get_all_ads_selling_info(ad_ids)
        log_message('\nall selling prices on first page count - {total}'.format(total=len(all_selling_price_ads)))
        for k, v in all_selling_price_ads.items():
            log_message('{k} - {v1} {v2} {v3}'.format(k=k, v1=v['price'], v2=v['user'], v3=v['provider']))

        filtered_ads = {k: v for (k, v) in all_selling_price_ads.items() if
                        MAX_PRICE_INR >= float(v['price']) >= MIN_PRICE_INR}

        log_message('\nfiltered prices count - {filtered}'.format(filtered=len(filtered_ads)))
        for k, v in filtered_ads.items():
            log_message('{k} - {v1} {v2} {v3}'.format(k=k, v1=v['price'], v2=v['user'], v3=v['provider']))

        filtered_dict = {}
        for k,v in all_selling_price_ads.items():
            if float(v['price']) < MAX_PRICE_INR and float(v['price']) > MIN_PRICE_INR:
                filtered_dict[k] = {'price': v['price'], 'user': v['user'], 'provider': v['provider']}

        log_message('\nfiltered prices count2 - {filtered}'.format(filtered=len(filtered_dict)))
        for k, v in filtered_dict.items():
            log_message('{k} - {v1} {v2} {v3}'.format(k=k, v1=v['price'], v2=v['user'], v3=v['provider']))

        if len(filtered_ads.keys()) < 1:
            log_message('No ads found in the defined range')
            continue

        max_selling_price = max(float(v['price']) for v in filtered_ads.values())
        max_keys = [k for k, v in filtered_ads.items() if float(v['price']) == max_selling_price]
        user_with_max_selling_price = filtered_ads[max_keys[0]]['user']

        log_message('\nFound max selling price of {price} by user {user}'
                    .format(price=max_selling_price, user=user_with_max_selling_price))

        for ad_id, price in ads_with_selected_provider.items():
            new_price = max_selling_price + 1
            log_message('\nour price should be {price}'.format(price=new_price))

        time.sleep(SLEEP_TIME)


run()

