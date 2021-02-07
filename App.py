from lbcapi import api
import urllib.parse
import time

HMAC_KEY = 'cf4120eb00bebe14ea07784c601eb34f'
HMAC_SECRET = '122687e7d6c63a7eb9f1835dfac37deddb4ebe5b9d587585f19b7addd38c81a8'

MAX_PRICE_INR = 2950000
MIN_PRICE_INR = 2930000


CURRENCY = 'INR'
PROVIDER_IMPS = 'BANK_TRANSFER_IMPS'
SLEEP_TIME = 3

conn = api.hmac(HMAC_KEY, HMAC_SECRET)


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


def get_all_ads_selling_info():
    response = conn.call('GET', '/sell-bitcoins-online/INR/.json').json()
    selling_price_dict = {}
    selling_price_dict = read_selling_info_data(response['data'], selling_price_dict)

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

    return selling_price_dict


def read_selling_info_data(data, selling_price_dict):
    for ad in data['ad_list']:
        ad_id = ad['data']['ad_id']
        price = ad['data']['temp_price']
        user = ad['data']['profile']['username']

        if ad_id not in selling_price_dict.keys():
            selling_price_dict[ad_id] = {'price': price, 'user': user}

    return selling_price_dict


def get_ad_with_imps_provider(ads):
    ads_with_matching_provider = []
    for ad_id, ad_info in ads.items():
        if ad_info['provider'] == PROVIDER_IMPS:
            ads_with_matching_provider.append({'ad_id': ad_id, 'price': ad_info['price']})
    return ads_with_matching_provider


def update_ad_price(ad_id, price):
    response = conn.call('POST', '/api/ad-equation/{ad_id}/'.format(ad_id=ad_id), params={'price_equation': price}).json()
    print(response)
    print('price updated to {price} for {ad_id}'.format(ad_id=ad_id, price=price))


def run():
    while True:
        current_ads = get_current_ads_info()
        ads_with_selected_provider = get_ad_with_imps_provider(current_ads)

        if len(ads_with_selected_provider) < 1:
            print('No ads found.')
            return

        all_selling_price_ads = get_all_ads_selling_info()

        filtered_ads = {k: v for (k, v) in all_selling_price_ads.items() if MAX_PRICE_INR >= float(v['price']) >= MIN_PRICE_INR}

        if len(filtered_ads.keys()) < 1:
            print('No ads found in the defined range')
            continue

        max_selling_price = max(float(v['price']) for v in filtered_ads.values())
        max_keys = [k for k, v in filtered_ads.items() if float(v['price']) == max_selling_price]
        user_with_max_selling_price = filtered_ads[max_keys[0]]['user']

        print('Found max selling price of {price} by user {user}'
              .format(price=max_selling_price, user=user_with_max_selling_price))

        for ad in ads_with_selected_provider:
            #if float(ad['price']) <= max_selling_price:
            new_price = max_selling_price + 1
            if new_price < MAX_PRICE_INR:
                print('current selling price for ad {id} - {current_price}'.
                      format(id=ad['ad_id'], current_price=ad['price']))
                update_ad_price(ad['ad_id'], new_price)
            else:
                print('Max limit reached for ad id {ad_id}'.format(ad_id=ad['ad_id']))
            #else:
                #print('Current selling price of {current_price} for ad is higher than max selling price in market'.
                      #format(current_price=ad['price']))

        time.sleep(SLEEP_TIME)

run()

