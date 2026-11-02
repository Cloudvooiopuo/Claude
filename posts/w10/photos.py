"""11/14〜11/27 の写真の割り当て（hook, コツ1, コツ2, コツ3, cta, カルーセル表紙）。どれも photos/credits.json に出典あり。"""
P = {
 "1114": ["w6/1105_morning_cta", "w6/1105_morning_1", "w6/1108_heating_2", "w6/1105_morning_2", "w6/1105_morning_3", "w8/1022_dry_1"],
 "1115": ["w8/1023_photo_hook", "w8/1023_photo_3", "w8/1023_photo_1", "w8/1023_photo_2", "w8/1023_photo_cta", "w6/1113_photos_hook"],
 "1116": ["sleep/snow_1", "w6/1108_heating_hook", "sleep/fire_3", "sleep/snow_3", "sleep/snownight_2", "sleep/snow_4"],
 "1117": ["w6/1107_library_hook", "w6/1104_pens_1", "w8/1024_daytrip_1", "w6/1101_osouji_hook", "w6/1104_pens_hook", "w6/1104_pens_2"],
 "1118": ["w8/1022_dry_2", "w8/1022_dry_1", "w8/1022_dry_cta", "w8/1022_dry_hook", "w6/1108_heating_cta", "w8/1022_dry_2"],
 "1119": ["w8/1030_desk_cable_hook", "w8/1025_cable_hook", "w8/1025_cable_1", "w8/1025_cable_3", "w8/1030_desk_cable_3", "w8/1028_rakuten_point_hook"],
 "1120": ["w6/1111_onsen_hook", "w6/1111_onsen_1", "w6/1111_onsen_2", "w6/1111_onsen_3", "w6/1111_onsen_cta", "w6/1111_onsen_1"],
 "1121": ["sleep/city_1", "w8/1029_night_3", "sleep/nightcafe_1", "sleep/city_4", "w8/1029_night_hook", "sleep/city_2"],
 "1122": ["sleep/sunflower_2", "sleep/sunny_blossom", "w8/1021_cafe_1", "sleep/sunflower_3", "sleep/sunflower_1", "sleep/sunflower_2"],
 "1123": ["w8/1021_cafe_hook", "w8/1021_cafe_2", "w8/1019_book_hook", "w8/1021_cafe_3", "w8/1016_bgm_hook", "w8/1021_cafe_hook"],
 "1124": ["w6/1101_osouji_hook", "w6/1101_osouji_2", "w6/1101_osouji_1", "w6/1101_osouji_cta", "w6/1101_osouji_3", "w6/1108_heating_cta"],
 "1125": ["w6/1105_morning_hook", "w6/1105_morning_1", "w6/1105_morning_2", "w8/1022_dry_1", "w6/1105_morning_cta", "w6/1105_morning_hook"],
 "1126": ["w6/1108_heating_3", "w6/1108_heating_1", "w6/1108_heating_2", "sleep/fire_5", "sleep/fire_4", "w6/1108_heating_3"],
 "1127": ["sleep/rain_window_frame", "sleep/rain_drops_gray", "w6/1101_osouji_2", "sleep/rain_bokeh", "w6/1101_osouji_3", "sleep/rain_window_frame"],
}
P = {k: [f"photos/{x}.jpg" for x in v] for k, v in P.items()}
