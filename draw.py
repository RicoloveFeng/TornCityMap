import cairosvg, io, requests, json, datetime, os
from PIL import Image, ImageDraw, ImageFont

# 1. Get API key from secret
api_key = os.environ["APIKEY"]
 
# 2. Get TT info from API
with open("shapes.json", 'r') as f:
    tt_shape = json.load(f)
    
tts = list(tt_shape.keys())

# 2.1 Try to load history info from file if exist
today = datetime.datetime.today()
ttinfo_path = './tt_history/ttinfo_{}_{}_{}.json'.format(today.year, today.month, today.day)
for _, _, files in os.walk('./tt_history'):
    if ttinfo_path.split('/')[-1] in files:
        with open(ttinfo_path, 'r') as f:
            ttinfo = json.load(f)
    else:
        ttinfo = {}

# 2.2 Get tt info for those not in file
start_idx = 0
call = "https://api.torn.com/torn/{}?selections=territory&key={}"
call_timeout = False
while start_idx < 4150:
    if any(tt in ttinfo for tt in tts[start_idx:start_idx+50]):
        print("skip", start_idx)
        start_idx += 50
        continue

    try_count = 0
    while try_count <= 5:
        try:
            tt_call_res = requests.get(call.format(','.join(tts[start_idx:start_idx+50]), api_key), timeout=5).json()
            break
        except:
            print("call for", start_idx, "timeout, retry", try_count)
            try_count += 1
            if try_count > 5:
                # Reach call limit, dump current tt info and exit
                call_timeout = True
                break
            else:
                continue

    if not tt_call_res["territory"]:
        print("tt all done")
        break
    for k, v in tt_call_res["territory"].items():
        ttinfo[k] = v
    print("done", start_idx)
    start_idx += 50

with open(ttinfo_path, 'w') as f:
    json.dump(ttinfo, f)
if call_timeout:
    exit(-1)

# 3. Fac information
ns_faction=[35318,10820,28073,33007,8803,15222,9412,42125,25025,9110,13502,9533,11747,11581,9055,21526,13784,35507,22492,1149,12863,29865,11062,21526,40992,8520]
jfk_faction=[355,3241,6924,7652,7986,8076,8422,8715,9100,9356,9405,9674,9953,10174,10741,11428,11796,14365,14821,16335,16424,20465,21234,21665,23952,25874,27902,31764,32781,35776,36134]
sa_faction=[11782,27312,16634,11376,9357,23193,35840,16247,42505,15644,48989,48112,39960,49763,37185,48002,43325,20747,28349,41297,14686,40959,525,13872,48680,48832,8285,13307,23492,46127,49346,33783,8811,48640,41363,11131,28205,43836,45595,12894,7990,17587,9280,41164,6974,38887,41234,36140,33458,16296,46089,27554,937,2013,13377,40905,7935,7227,18597,17991,21716,15154,39531,44467,37498,46442,49184,6780,47100,40624,44562,37093,12255,40591]
ptcr_faction=[31397,41218,9036,30009,37595,41775,8400,36274,13842,40449,8867,18090,5431,7049,8537,16503,21368,8400,13343,42681,10856,8938,2736,9689,230,13665,8867,18569,9041,10610,41853,16628,478,8836,44758,946,89,8151,19,44404,41419,10566,10850,26043,22680,16312,1117,8124,22295,14052,12912,44445,9517,15151,16053,26154,7818,7197]
m_faction=[38481,26885,8336,20514,231,14078,39756,12249,8468,16299,9047,12893,27370,14760,15446,9745,366,36891,21040,12645,39549,11522,2095,10818,41028,27223,9118,7835,9336,18736,33241,8954,8085,21028,12094,13851,16282,40518,29107,9171,15655,35423,9420,8384,15929,9176,37530,6731,26437,11539,22781,17133,7709,40775,16120,42685,30085,7969,9032,15120,20303,30820,10960,6984]

facs = [ns_faction, jfk_faction, sa_faction, ptcr_faction, m_faction]

# 4. Draw
# 4.1 Funcs
def make_svg(citymap, tt_color, war_tts, unocc_tts):
    svg_prefix = '<svg width="6384" height="3648" style="background-color: transparent">'
    svg_suffix = '</svg>'
    svg_item = '<path d="{}" stroke-width="0" fill="{}" fill-opacity="0.27"/>'
    svg_unocc = '<path d="{}" stroke-width="0" fill="{}" fill-opacity="0.07"/>'
    svg_war_stroke = '<path d="{}" stroke="{}" stroke-width="2" stroke-opacity="1" fill-opacity="0"/>'
    svg_str = [svg_prefix]
    for tt in tt_color.keys():
        if tt not in tt_shape:
            print(tt, " not in shapes")
            continue
        color = tt_color[tt]
        svg_path = tt_shape[tt]
        if tt in unocc_tts:
            svg_str.append(svg_unocc.format(svg_path, color))
        else:
            svg_str.append(svg_item.format(svg_path, color))
        if tt in war_tts:
            svg_str.append(svg_war_stroke.format(svg_path, war_tts[tt]))
    svg_str.append(svg_suffix)
    out = cairosvg.svg2png(bytestring=''.join(svg_str).encode('utf-8'))
    svgimg = Image.open(io.BytesIO(out)).convert('RGBA')
    citymap.paste(svgimg, (0, 0), svgimg)
    
def draw_legend(citymap):
    dr = ImageDraw.Draw(citymap, 'RGBA')
    font = ImageFont.truetype('./arial.ttf', 60)
    fac2color = {
        'WestWorld(Monarch)': 'fuchsia',
        'CRyPTo(PT&CR&etc.)': 'yellow',
        'Subversive Alliance': 'DodgerBlue',
        'JFK': '#00b23a',
        'Natural Selection': '#ef4444',
        'Not Affliated': 'cyan',
        'NPC Buildings': 'orange'
    }
    line = 0
    x = 50
    ls = 30
    basey = citymap.size[1] - 50
    for facname, color in fac2color.items():
        y = basey - line * 100
        dr.rectangle((x - ls, y - ls, x + ls, y + ls), 'black', width=1)
        dr.rectangle((x - ls + 5, y - ls + 5, x + ls - 5, y + ls - 5), color, width=1)
        dr.text((x + 50, y - 35), facname, color, font, stroke_fill='black', stroke_width=5)
        line += 1
    basex = 800
    dr.line((basex, basey, basex + 200, basey), 'lime', width=5)
    dr.text((basex + 250, basey - 35),"Fake Wall", 'lime', font, stroke_fill='black', stroke_width=5)
    dr.line((basex, basey - 100, basex + 200, basey - 100), 'red', width=5)
    dr.text((basex + 250, basey - 135),"Real Wall", 'red', font, stroke_fill='black', stroke_width=5)
    dr.text((4200, basey - 200), f'Production by @SPGoding // Created at {today.day}/{today.month}/{today.year}', 'white', font, stroke_fill='black', stroke_width=5)

# 4.2 Main logic
ttcolor = {}
is_war = {}
is_unocc = set()
vis = set()
bfs_queue = []
for tt, detail in ttinfo.items():
    color = None
    facid = detail["faction"]
    if facid in ns_faction:
        color = '#ef4444' # red
    elif facid in jfk_faction:
        color = '#00b23a' #green
    elif facid in sa_faction:
        color = 'blue'
    elif facid in ptcr_faction:
        color = 'yellow'
    elif facid in m_faction:
        color = '#cc00cc' # fuchsia
    elif facid != 0:
        color = 'cyan'
    if color:
        ttcolor[tt] = color
        vis.add(tt)
        bfs_queue.append(tt)
    if 'war' in detail:
        war_detail = detail['war']
        assfac = war_detail['assaulting_faction']
        deffac = war_detail['defending_faction']
        is_war[tt] = 'red'
        for fac in facs:
            if assfac in fac and deffac in fac:
                is_war[tt] = 'lime'
                break

for tt, shape in tt_shape.items():
    if tt not in ttinfo:
        ttcolor[tt] = 'orange'

while bfs_queue:
    tmp = []
    for tt in bfs_queue:
        if tt not in ttinfo:
            print("we need info of", tt)
            continue
        if ttcolor[tt] == 'cyan':
            continue
        nbs = ttinfo[tt]['neighbors']
        for nb in nbs:
            if nb not in vis:
                ttcolor[nb] = ttcolor[tt]
                is_unocc.add(nb)
                vis.add(nb)
                tmp.append(nb)
    bfs_queue = tmp

city = Image.open("map.png")
make_svg(city, ttcolor, is_war, is_unocc)
draw_legend(city)
city.save(f"city.jpg")
