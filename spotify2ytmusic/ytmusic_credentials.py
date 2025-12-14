# import ytmusicapi
import ytmusicapi
import os

def setup_ytmusic_with_raw_headers(credentials_file="oauth.json"):
    """
    Sets up YTMusic connection using ytmusicapi.setup with hardcoded raw headers.
    Parameters:
        credentials_file (str): Path to save the configuration headers (credentials).
    Returns:
        str: Configuration headers string returned by ytmusicapi.setup.
    """
    # Hardcoded raw headers
    headers_raw = """POST /youtubei/v1/browse?prettyPrint=false HTTP/2
Host: music.youtube.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br, zstd
Content-Type: application/json
Content-Length: 3134
Referer: https://music.youtube.com/
X-Goog-Visitor-Id: CgswMW1pNmlVU05kQSi75vvJBjIKCgJVUxIEGgAgXg%3D%3D
X-Youtube-Bootstrap-Logged-In: true
X-Youtube-Client-Name: 67
X-Youtube-Client-Version: 1.20251210.03.00
X-Goog-AuthUser: 0
X-Origin: https://music.youtube.com
Origin: https://music.youtube.com
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: same-origin
Sec-Fetch-Site: same-origin
Authorization: SAPISIDHASH 1765733190_45530844ea8cf6f15917d6d281032b9194b120ee_u SAPISID1PHASH 1765733190_45530844ea8cf6f15917d6d281032b9194b120ee_u SAPISID3PHASH 1765733190_45530844ea8cf6f15917d6d281032b9194b120ee_u
Connection: keep-alive
Cookie: VISITOR_INFO1_LIVE=01mi6iUSNdA; VISITOR_PRIVACY_METADATA=CgJVUxIEGgAgXg%3D%3D; __Secure-ROLLOUT_TOKEN=CKqx_MDl5pTBiQEQjezyzLCpkQMYqLvYrrq9kQM%3D; PREF=tz=America.Los_Angeles&f6=40000000&f7=100; __Secure-1PSIDTS=sidts-CjUBflaCdYnzGsfEXTjG4UVUTCmhkRgFmwNvhmt6jTeD8sLszXadL9sa_Y2aqEfnz3ll7AYyEBAA; __Secure-3PSIDTS=sidts-CjUBflaCdYnzGsfEXTjG4UVUTCmhkRgFmwNvhmt6jTeD8sLszXadL9sa_Y2aqEfnz3ll7AYyEBAA; HSID=AuWpu_PNnthOdNjU1; SSID=A5WxjLb2Hirzof4R_; APISID=MVnhLTx7g6hii0VG/AqTSNYMBKDYDIcETu; SAPISID=oXauPfgjCImjsUt1/ATSNgEMmQcL4AmYmA; __Secure-1PAPISID=oXauPfgjCImjsUt1/ATSNgEMmQcL4AmYmA; __Secure-3PAPISID=oXauPfgjCImjsUt1/ATSNgEMmQcL4AmYmA; SID=g.a0004QjqzYsU4mk_Y7KRn3qb3I1-ah5GHEh5yUx9wQNe3v9wEjah608Nef2lG_SwLy5C76nPHwACgYKAU0SARASFQHGX2Mib9H6ICsjh97olmBJqBGjwhoVAUF8yKoLe2v_tByrp-ZykTWvCqnr0076; __Secure-1PSID=g.a0004QjqzYsU4mk_Y7KRn3qb3I1-ah5GHEh5yUx9wQNe3v9wEjahqQr8P4m7tPAQjrq7dMiHZQACgYKAe0SARASFQHGX2Mitmv0WiQH0tj7QB7cBaBpghoVAUF8yKq5h8-KhGRiwcTJGJkiBuZA0076; __Secure-3PSID=g.a0004QjqzYsU4mk_Y7KRn3qb3I1-ah5GHEh5yUx9wQNe3v9wEjahr9RGyynK2WyuZURbKKbuEAACgYKAR0SARASFQHGX2MiXNU7ziutHkQfAvQFiTfZQBoVAUF8yKpS28A_9ogKpUj-tcjKsq1_0076; LOGIN_INFO=AFmmF2swRQIgCoNup44h-8C9jLppDo3me9W4Zc977m9HG7EZ0CAHixECIQDwTQAAvm24mAw4rA3bAZMTsNO1JS3X3pLIz61Ja_hRBQ:QUQ3MjNmeW5paXFmTHAzekZlYUM4c09BZUdXZHBlM29TaF9ONTRZWGRIc2RoTGxMT2RHUjY2aEJheDJwMmlJbVRGVnN5bUJrRW5yZXBEMkdpUXc1cEE5UHV3dlFmLTQ1RUdsd2VFZEdTcEFXLXlGUi1wT0U1NHBNSU84bHRXRjN4eW0tWDF6Z3NmcEQ3SEM5N3h1ME8xSW9VTjNYaElyck5n; SIDCC=AKEyXzVf9QEYF3oEEJ5fX_W9hlkn5_nSjnu52fWBlhxnx6fQRuTzxs1Dzgy40RonoEPzJ8Yjgy0; __Secure-1PSIDCC=AKEyXzV5LmwzpSzGX6RYmV9xtdPmtAR3kswtLP0pIm0dp02sL3WWsmRgOi9iD288wQC636i6JuE; __Secure-3PSIDCC=AKEyXzVqxs4rXeGfhheRM2_9OgQlufqrE4LhtwI2mSlj31lQFlxwDzeazm2JSBY4em08uHFGiA; YSC=LTCGtO5rZ0M; _gcl_au=1.1.1293368935.1765728266
Priority: u=0
TE: trailers"""

    # Use ytmusicapi.setup to process headers and save the credentials
    config_headers = ytmusicapi.setup(
        filepath=credentials_file, headers_raw=headers_raw
    )
    print(f"Configuration headers saved to {credentials_file}")
    return config_headers

if __name__ == "__main__":
    try:
        # Specify credentials file path
        credentials_file = "oauth.json"
        # Set up YTMusic with raw headers
        print("Setting up YTMusic using hardcoded headers...")
        setup_ytmusic_with_raw_headers(credentials_file=credentials_file)
        print("YTMusic setup completed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")