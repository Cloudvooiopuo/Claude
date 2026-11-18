"""11/28〜12/11 の写真の割り当て（hook, コツ1, コツ2, コツ3, cta, カルーセル表紙）。どれも photos/credits.json に出典あり。"""
P = {
 "1128": ["w6/1111_onsen_hook", "w6/1108_heating_1", "w6/1111_onsen_2", "w6/1105_morning_3", "w6/1111_onsen_cta", "w6/1111_onsen_3"],
 "1129": ["office/notebook_latte_1", "w6/1104_pens_1", "w6/1104_pens_2", "w6/1104_pens_3", "w6/1104_pens_cta", "w6/1104_pens_hook"],
 "1130": ["office/meeting_room_1", "office/desk_top_1", "w6/1104_pens_2", "w8/1016_bgm_1", "office/desk_plants_1", "office/desk_flowers_1"],
 "1201": ["w6/1107_library_hook", "w6/1101_osouji_1", "w8/1017_packing_1", "w8/1017_packing_2", "w6/1107_library_cta", "w6/1107_library_1"],
 "1202": ["w6/1112_nabe_hook", "w6/1112_nabe_1", "w6/1112_nabe_2", "w6/1112_nabe_3", "w6/1112_nabe_cta", "w6/1112_nabe_2"],
 "1203": ["office/desk_top_1", "office/notebook_latte_1", "office/desk_plants_1", "office/meeting_room_1", "w8/1016_bgm_hook", "office/desk_top_1"],
 "1204": ["w8/1022_dry_hook", "w8/1018_heyaboshi_1", "w8/1022_dry_2", "w8/1022_dry_1", "w8/1018_heyaboshi_hook", "w8/1018_heyaboshi_2"],
 "1205": ["sleep/night_starry_sky", "sleep/night_milkyway", "sleep/night_moon_fjord", "sleep/night_moon_bay", "sleep/night_moon_beach", "sleep/night_starry_sky"],
 "1206": ["w8/1029_night_1", "w8/1017_packing_3", "w8/1017_packing_hook", "w6/1105_morning_1", "w8/1029_night_2", "w8/1029_night_1"],
 "1207": ["office/desk_flowers_1", "w6/1107_library_2", "w6/1104_pens_hook", "w8/1016_bgm_2", "office/desk_top_1", "office/desk_plants_1"],
 "1208": ["w6/1101_osouji_hook", "w6/1101_osouji_3", "w6/1101_osouji_2", "w6/1101_osouji_cta", "w6/1101_osouji_1", "w6/1101_osouji_hook"],
 "1209": ["w6/1104_pens_3", "w6/1108_heating_cta", "w6/1104_pens_1", "w6/1104_pens_cta", "office/notebook_latte_1", "w6/1104_pens_2"],
 "1210": ["w8/1025_cable_hook", "w8/1030_desk_cable_hook", "w8/1030_desk_cable_2", "w8/1025_cable_2", "office/desk_top_1", "w8/1030_desk_cable_3"],
 "1211": ["w6/1112_nabe_3", "w6/1112_nabe_1", "w7/1014_mealprep_hook", "w6/1112_nabe_cta", "w6/1112_nabe_hook", "w6/1112_nabe_1"],
}
P = {k: [f"photos/{x}.jpg" for x in v] for k, v in P.items()}
