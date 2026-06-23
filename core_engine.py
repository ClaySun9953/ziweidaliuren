import datetime
import math
import ephem

class PrecisionSolarEngine:
    def __init__(self):
        self.terms = ["春分","清明","谷雨","立夏","小满","芒种","夏至","小暑","大暑","立秋","处暑","白露","秋分","寒露","霜降","立冬","小雪","大雪","冬至","小寒","大寒","立春","雨水","惊蛰"]
        
    def get_solar_data(self, dt):
        sun = ephem.Sun()
        sun.compute(ephem.Date(dt - datetime.timedelta(hours=8)))
        slong = math.degrees(ephem.Ecliptic(sun).lon) % 360
        term_idx = int(slong // 15)
        term_name = self.terms[term_idx]
        
        yin_terms = ["夏至","小暑","大暑","立秋","处暑","白露","秋分","寒露","霜降","立冬","小雪","大雪"]
        dun_type = "阴遁" if term_name in yin_terms else "阳遁"
        yang_map = {"冬至":[1,7,4], "小寒":[2,8,5], "大寒":[3,9,6], "立春":[8,5,2], "雨水":[9,6,3], "惊蛰":[1,7,4], "春分":[3,9,6], "清明":[4,1,7], "谷雨":[5,2,8], "立夏":[4,1,7], "小满":[5,2,8], "芒种":[6,3,9]}
        yin_map = {"夏至":[9,3,6], "小暑":[8,2,5], "大暑":[7,1,4], "立秋":[2,5,8], "处暑":[1,4,7], "白露":[9,3,6], "秋分":[7,1,4], "寒露":[6,9,3], "霜降":[5,8,2], "立冬":[6,9,3], "小雪":[5,8,2], "大雪":[4,7,1]}
        
        jiang_idx = int(slong // 30)
        jiang_list = ["戌","酉","申","未","午","巳","辰","卯","寅","丑","子","亥"]
        return slong, term_name, dun_type, yang_map if dun_type=="阳遁" else yin_map, jiang_list[jiang_idx]

class TimeAndGeo:
    def __init__(self):
        self.GAN = list("甲乙丙丁戊己庚辛壬癸")
        self.ZHI = list("子丑寅卯辰巳午未申酉戌亥")
        self.JIAZI = [g+z for i in range(60) for g,z in zip([self.GAN[i%10]], [self.ZHI[i%12]])]
        self.XUN_KONG = {"甲子":"戌亥", "甲戌":"申酉", "甲申":"午未", "甲午":"辰巳", "甲辰":"寅卯", "甲寅":"子丑"}
        self.BASE_DATE = datetime.datetime(1900, 1, 31)

    def get_pillars(self, dt):
        is_early_zi = dt.hour == 23
        dt_calc = dt + datetime.timedelta(days=1) if is_early_zi else dt
        year_gan_idx = (dt_calc.year - 4) % 10
        year_zhi_idx = (dt_calc.year - 4) % 12
        
        jieqi_map = [(1,5,"丑",12),(2,4,"寅",1),(3,6,"卯",2),(4,5,"辰",3),(5,6,"巳",4),(6,6,"午",5),(7,7,"未",6),(8,8,"申",7),(9,8,"酉",8),(10,8,"戌",9),(11,8,"亥",10),(12,7,"子",11)]
        m_zhi, m_num = "丑", 12
        for i in range(12):
            sm, sd, z, n = jieqi_map[i]
            nm, nd, _, _ = jieqi_map[(i+1)%12]
            try:
                c_dt = dt_calc.replace(month=sm, day=sd)
                n_dt = dt_calc.replace(year=dt_calc.year+1, month=nm, day=nd) if nm<sm else dt_calc.replace(month=nm, day=nd)
                if c_dt <= dt_calc < n_dt: m_zhi, m_num = z, n; break
            except: pass

        month_gan_idx = (year_gan_idx * 2 + m_num + 1) % 10
        delta = (dt_calc - self.BASE_DATE).days
        day_idx = (40 + delta) % 60
        day_gan, day_zhi = self.GAN[day_idx % 10], self.ZHI[day_idx % 12]

        hour_zhi_idx = ((dt.hour + 1) % 24) // 2
        shi_zhi = self.ZHI[hour_zhi_idx]
        shi_gan = self.GAN[({'甲':0,'己':0,'乙':2,'庚':2,'丙':4,'辛':4,'丁':6,'壬':6,'戊':8,'癸':8}[day_gan] + hour_zhi_idx) % 10]
        
        shi_ganzhi_idx = self.JIAZI.index(f"{shi_gan}{shi_zhi}")
        xun_shou = self.JIAZI[shi_ganzhi_idx - (shi_ganzhi_idx % 10)]
        
        offset = 0; temp_gan = day_gan
        while temp_gan not in ['甲', '己'] and offset < 10:
            offset += 1; temp_gan = self.GAN[(day_idx - offset) % 10]
        yz = self.ZHI[(day_idx - offset) % 12]
        yuan_idx = 0 if yz in '子午卯酉' else (1 if yz in '寅申巳亥' else 2)

        return {
            "year": f"{self.GAN[year_gan_idx]}{self.ZHI[year_zhi_idx]}", "month": f"{self.GAN[month_gan_idx]}{m_zhi}",
            "day": f"{day_gan}{day_zhi}", "hour": f"{shi_gan}{shi_zhi}",
            "day_gan": day_gan, "day_zhi": day_zhi, "h_gan": shi_gan, "h_zhi": shi_zhi,
            "xun": xun_shou, "kw": self.XUN_KONG.get(xun_shou, ""), "yuan_idx": yuan_idx, "is_early_zi": is_early_zi
        }

class QimenEngine:
    def run(self, ju, is_yang, xun, h_gan, h_zhi, kw):
        x_map = {"甲子":"戊", "甲戌":"己", "甲申":"庚", "甲午":"辛", "甲辰":"壬", "甲寅":"癸"}
        l_stem = x_map.get(xun, "戊")
        stars = ["","天蓬","天芮","天冲","天辅","天禽","天心","天柱","天任","天英"]
        doors = ["","休门","死门","伤门","杜门","","开门","惊门","生门","景门"]
        p_zhi = {1:"子", 2:"未申", 3:"卯", 4:"辰巳", 5:"", 6:"戌亥", 7:"酉", 8:"寅丑", 9:"午"}

        di = [""] * 10
        seq = list("戊己庚辛壬癸丁丙乙") if is_yang else list("戊乙丙丁癸壬辛庚己")
        curr = ju
        for s in seq:
            di[curr] = s
            curr = curr % 9 + 1 if is_yang else (curr - 2) % 9 + 1
            if curr == 0: curr = 9
            
        try: lp = di.index(l_stem)
        except: lp = 5
        if lp == 5: lp = 2
        
        ring = [1, 8, 3, 4, 9, 2, 7, 6]
        t_stem = l_stem if h_gan == "甲" else h_gan
        try: hp = di.index(t_stem)
        except: hp = lp
        if hp == 5: hp = 2
        
        try: shift = ring.index(hp) - ring.index(lp)
        except: shift = 0
            
        layout = {i: {"di": di[i], "star":"", "tian":"", "door":"", "god":"", "kw": any(z in p_zhi[i] for z in kw)} for i in range(1, 10)}
            
        for o_pos in range(1, 10):
            if o_pos == 5: continue
            s_name = "天芮" if o_pos == 2 else stars[o_pos]
            st_name = di[2] if o_pos == 2 else di[o_pos]
            try:
                np = ring[(ring.index(o_pos) + shift) % 8]
                layout[np]["star"], layout[np]["tian"] = s_name, st_name
            except: pass

        zhis = list("子丑寅卯辰巳午未申酉戌亥")
        dp = lp + (zhis.index(h_zhi) - zhis.index(xun[1])) if is_yang else lp - (zhis.index(h_zhi) - zhis.index(xun[1]))
        while dp > 9: dp -= 9
        while dp <= 0: dp += 9
        if dp == 5: dp = 2
        
        door_seq = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
        try:
            zs_idx = door_seq.index(doors[lp])
            d_ring_idx = ring.index(dp)
            for k in range(8): layout[ring[(d_ring_idx + k) % 8]]["door"] = door_seq[(zs_idx + k) % 8]
        except: pass

        gods = ["值符","螣蛇","太阴","六合","白虎","玄武","九地","九天"] if is_yang else ["值符","九天","九地","玄武","白虎","六合","太阴","螣蛇"]
        try:
            g_start = ring.index(hp)
            for k in range(8): layout[ring[(g_start + k) % 8] if is_yang else ring[(g_start - k) % 8]]["god"] = gods[k]
        except: pass
        
        layout[5]["star"], layout[5]["god"], layout[5]["door"] = "天禽", layout[2].get("god", ""), layout[2].get("door", "")
        return layout, stars[lp], doors[lp]

class LiuYaoEngine:
    def process(self, codes):
        trigrams = {(1,1,1):"乾", (0,1,1):"兑", (1,0,1):"离", (0,0,1):"震", (1,1,0):"巽", (0,1,0):"坎", (1,0,0):"艮", (0,0,0):"坤"}
        h_map = {"乾乾":"乾为天","坤坤":"坤为地","坎坎":"坎为水","离离":"离为火","艮艮":"艮为山","震震":"震为雷","巽巽":"巽为风","兑兑":"兑为泽","乾坤":"天地否","坤乾":"地天泰","坎离":"水火既济","离坎":"火水未济","艮坤":"山地剥","坤艮":"地山谦","震巽":"雷风恒","巽震":"风雷益","乾坎":"天水讼","坎乾":"水天需","乾艮":"天山遁","艮乾":"山天大畜","乾震":"天雷无妄","震乾":"雷天大壮","乾巽":"天风姤","巽乾":"风天小畜","乾离":"天火同人","离乾":"火天大有","乾兑":"天泽履","兑乾":"泽天夬","坤坎":"地水师","坎坤":"水地比","坤震":"地雷复","震坤":"雷地豫","坤巽":"地风升","巽坤":"风地观","坤离":"地火明夷","离坤":"火地晋","坤兑":"地泽临","兑坤":"泽地萃","坎艮":"水山蹇","艮坎":"山水蒙","坎震":"水雷屯","震坎":"雷水解","坎巽":"水风井","巽坎":"风水涣","坎兑":"水泽节","兑坎":"泽水困","离艮":"火山旅","艮离":"山火贲","离震":"火雷噬嗑","震离":"雷火丰","离巽":"火风鼎","巽离":"风火家人","离兑":"火泽睽","兑离":"泽火革","艮震":"山雷颐","震艮":"雷山小过","艮巽":"山风蛊","巽艮":"风山渐","艮兑":"山泽损","兑艮":"泽山咸","震兑":"雷泽归妹","兑震":"泽雷随","巽兑":"风泽中孚","兑巽":"泽风大过"}
        o_bits, c_bits, m_lines = [], [], []
        for idx, val in enumerate(codes):
            bit = 0 if val in [6, 8] else 1
            o_bits.append(bit)
            if val == 6: c_bits.append(1); m_lines.append(idx+1)
            elif val == 9: c_bits.append(0); m_lines.append(idx+1)
            else: c_bits.append(bit)
        
        uo, lo = tuple(reversed(o_bits[3:])), tuple(reversed(o_bits[:3]))
        uc, lc = tuple(reversed(c_bits[3:])), tuple(reversed(c_bits[:3]))
        bk = trigrams.get(uo, "") + trigrams.get(lo, "")
        ck = trigrams.get(uc, "") + trigrams.get(lc, "")
        return {"ben": h_map.get(bk, bk), "bian": h_map.get(ck, ck), "moves": m_lines, "codes": codes}