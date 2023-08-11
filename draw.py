import cairosvg, io, requests, json, datetime, os
from PIL import Image, ImageDraw, ImageFont

# 1. Get API key from secret
# Moved to request.get
 
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
            api_key = os.environ["APIKEY"]
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
with open("faction_branch.json", "r") as f:
    fb = json.load(f)

ns_faction = fb['ns']
jfk_faction = fb['jfk']
sa_faction = fb['sa']
ptcr_faction = fb['ptcr']
m_faction = fb['m']
facs = [ns_faction, jfk_faction, sa_faction, ptcr_faction, m_faction]

# 4. Draw
# 4.1 Funcs
def make_svg(citymap, tt_color, war_tts, unocc_tts):
    svg_prefix = '<svg width="6384" height="3648" style="background-color: transparent">'
    svg_suffix = '</svg>'
    svg_item = '<path d="{}" stroke-width="0" fill="{}" fill-opacity="0.27"/>'
    svg_unocc = '<path d="{}" stroke-width="0" fill="{}" fill-opacity="0.07"/>'
    svg_war_stroke = '<path d="{}" stroke="{}" stroke-width="3" stroke-opacity="1" fill-opacity="0"/>'
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
        'WestWorld(Monarch&etc.)': 'cyan',
        'CRyPTo(PT&CR&etc.)': 'yellow',
        'SA/RoD': 'DodgerBlue',
        'JFK': '#00b23a',
        'OBN(NS&etc.)': '#f11414',
        'Not Affliated': 'fuchsia',
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
        color = '#f11414' # red
    elif facid in jfk_faction:
        color = '#00b23a' #green
    elif facid in sa_faction:
        color = 'blue'
    elif facid in ptcr_faction:
        color = 'yellow'
    elif facid in m_faction:
        color = 'cyan'
    elif facid != 0:
        color = '#cc00cc'  # fuchsia
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
        if ttcolor[tt] == '#cc00cc':
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
