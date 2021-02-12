from lbcapi import api
import urllib.parse
import time

HMAC_KEY_READ = ''
HMAC_SECRET_READ = ''

HMAC_KEY_WRITE = ''
HMAC_SECRET_WRITE = ''

MAX_PRICE_INR = 2880000
MIN_PRICE_INR = 2850000

PROVIDER_IMPS = 'NATIONAL_BANK'
SLEEP_TIME = 1

conn_read = api.hmac(HMAC_KEY_READ, HMAC_SECRET_READ)
conn_write = api.hmac(HMAC_KEY_WRITE, HMAC_SECRET_WRITE)


def get_current_ads_info():
    response = conn_write.call('GET', '/api/ads/').json()
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
    response = conn_read.call('GET', '/sell-bitcoins-online/INR/.json').json()
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

        if ad_id in current_ad_ids:
            continue

        if ad_id not in selling_price_dict.keys():
            selling_price_dict[ad_id] = {'price': price, 'user': user}

    return selling_price_dict


def get_ad_with_imps_provider(ads):
    ads_with_matching_provider = {}
    for ad_id, ad_info in ads.items():
        if ad_info['provider'] == PROVIDER_IMPS:
            ads_with_matching_provider[ad_id] = ad_info['price']
    return ads_with_matching_provider


def update_ad_price(ad_id, price):
    response = conn_write.call('POST', '/api/ad-equation/{ad_id}/'.format(ad_id=ad_id), params={'price_equation': price}).json()
    print(response)
    return 'error' not in response.keys()


def run():
    current_ads = get_current_ads_info()
    ads_with_selected_provider = get_ad_with_imps_provider(current_ads)
    ad_ids = list(ads_with_selected_provider)

    if len(ads_with_selected_provider) < 1:
        print('No ads found.')
        return

    prev_price = float(ads_with_selected_provider[ad_ids[0]])
    print('our starting price {price}'.format(price=prev_price))

    print('our range is from {min_val} to {max_val}'.format(min_val=MIN_PRICE_INR, max_val=MAX_PRICE_INR))

    while True:
        all_selling_price_ads = get_all_ads_selling_info(ad_ids)

        filtered_ads = {k: v for (k, v) in all_selling_price_ads.items() if MAX_PRICE_INR >= float(v['price']) >= MIN_PRICE_INR}

        if len(filtered_ads.keys()) < 1:
            print('No ads found in the defined range')
            continue

        max_selling_price = max(float(v['price']) for v in filtered_ads.values())
        max_keys = [k for k, v in filtered_ads.items() if float(v['price']) == max_selling_price]
        user_with_max_selling_price = filtered_ads[max_keys[0]]['user']

        print('Found max selling price of {price} by user {user}'
              .format(price=max_selling_price, user=user_with_max_selling_price))

        for ad_id, price in ads_with_selected_provider.items():
            new_price = max_selling_price + 1
            if prev_price == new_price:
                print('We are top selling price')
                continue
            if new_price < MAX_PRICE_INR:
                if update_ad_price(ad_id, new_price):
                    prev_price = new_price
                    print('price updated to {price} for {ad_id}'.format(ad_id=ad_id, price=new_price))
                else:
                    print('Could not update price due to error')
            else:
                print('Max limit reached for ad id {ad_id}'.format(ad_id=ad_id))

        time.sleep(SLEEP_TIME)


run()

