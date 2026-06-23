class DaLiuRenEngine:
    def __init__(self):
        self.ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 十干寄宫表 (天干映射到地盘的固定坐标)
        self.JI_GONG = {'甲':'寅', '乙':'辰', '丙':'巳', '戊':'巳', '丁':'未', '己':'未', '庚':'申', '辛':'戌', '壬':'亥', '癸':'丑'}
        
        # 地支五行属性，用于三传的生克计算
        self.ZHI_WUXING = {
            '寅':'木', '卯':'木',
            '巳':'火', '午':'火',
            '申':'金', '酉':'金',
            '亥':'水', '子':'水',
            '辰':'土', '戌':'土', '丑':'土', '未':'土'
        }
        
        # 十二天将序列
        self.TIAN_JIANG = ["贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙", "天空", "白虎", "太常", "玄武", "太阴", "天后"]

    def _check_ke(self, zhi1, zhi2):
        """五行生克判定：返回 zhi1 对 zhi2 的生克关系"""
        wx1 = self.ZHI_WUXING[zhi1]
        wx2 = self.ZHI_WUXING[zhi2]
        
        ke_map = {'木':'土', '土':'水', '水':'火', '火':'金', '金':'木'}
        if ke_map[wx1] == wx2:
            return "克"  # zhi1 克 zhi2
        elif ke_map[wx2] == wx1:
            return "贼"  # zhi2 克 zhi1 (下克上称为贼)
        return "平"

    def _get_tian_jiang(self, day_gan, hour_zhi, tian_pan):
        """计算十二天将落宫 (基于昼夜贵人法)"""
        # 1. 判断昼夜 (卯到申为昼，酉到寅为夜)
        is_daytime = hour_zhi in ['卯', '辰', '巳', '午', '未', '申']
        
        # 2. 贵人起点决断 (甲戊庚牛羊...)
        gui_ren_start = {
            '甲': '丑' if is_daytime else '未', '戊': '丑' if is_daytime else '未', '庚': '丑' if is_daytime else '未',
            '乙': '子' if is_daytime else '申', '己': '子' if is_daytime else '申',
            '丙': '亥' if is_daytime else '酉', '丁': '亥' if is_daytime else '酉',
            '辛': '午' if is_daytime else '寅',
            '壬': '巳' if is_daytime else '卯', '癸': '巳' if is_daytime else '卯'
        }
        
        # 贵人星在天盘的哪个字上
        tian_gui = gui_ren_start[day_gan]
        
        # 找到这个天盘字，落在哪个地盘上
        di_for_gui = None
        for di, tian in tian_pan.items():
            if tian == tian_gui:
                di_for_gui = di
                break
                
        # 3. 顺逆排布决断 (地盘在亥子丑寅卯辰为顺，巳午未申酉戌为逆)
        is_forward = di_for_gui in ['亥', '子', '丑', '寅', '卯', '辰']
        
        # 4. 生成天将排盘字典
        jiang_pan = {}
        tian_gui_idx = self.ZHI.index(tian_gui)
        
        for i in range(12):
            if is_forward:
                current_jiang = self.TIAN_JIANG[i]
                current_tian = self.ZHI[(tian_gui_idx + i) % 12]
            else:
                current_jiang = self.TIAN_JIANG[i]
                current_tian = self.ZHI[(tian_gui_idx - i) % 12]
            
            jiang_pan[current_tian] = current_jiang
            
        return jiang_pan

    def _get_san_chuan(self, sike):
        """
        计算三传 (初传、中传、末传)。
        大六壬共有九宗门（贼克、比用、涉害、遥克、昴星、别责、八专、伏吟、反吟）。
        此处实现核心的【贼克法】（元首课、重审课），覆盖约70%常规情况。
        """
        ze_list = [] # 下克上 (贼)
        ke_list = [] # 上克下 (克)
        
        for idx, lesson in enumerate(sike):
            relation = self._check_ke(lesson['top'], lesson['bottom'])
            if relation == "贼":
                ze_list.append((idx, lesson))
            elif relation == "克":
                ke_list.append((idx, lesson))
                
        chu_chuan = None
        rule_name = ""
        
        # 1. 贼克法：有贼取贼 (下克上优先)
        if len(ze_list) == 1:
            chu_chuan = ze_list[0][1]['top']
            rule_name = "重审课 (下贼上)"
        elif len(ze_list) > 1:
            # 简化版比用：如果多个下克上，暂时取第一个（完整逻辑需对比日干阴阳）
            chu_chuan = ze_list[0][1]['top']
            rule_name = "比用课 (下贼上多传)"
            
        # 2. 无贼取克 (上克下)
        elif len(ke_list) == 1:
            chu_chuan = ke_list[0][1]['top']
            rule_name = "元首课 (上克下)"
        elif len(ke_list) > 1:
            chu_chuan = ke_list[0][1]['top']
            rule_name = "比用课 (上克下多传)"
            
        # 3. 兜底逻辑 (涉害/遥克等复杂门类暂用第一课代入)
        else:
            chu_chuan = sike[3]['top'] # 第一课上神
            rule_name = "贼克不入 (其他宗门兜底)"
            
        return chu_chuan, rule_name

    def run(self, yue_jiang, hour_zhi, day_gan, day_zhi):
        # ----------------------------------------
        # 第一步：排天地盘 (月将加时)
        # ----------------------------------------
        y_idx = self.ZHI.index(yue_jiang)
        h_idx = self.ZHI.index(hour_zhi)
        shift = (y_idx - h_idx) % 12
        
        tian_pan = {}
        for i in range(12):
            tian_pan[self.ZHI[i]] = self.ZHI[(i + shift) % 12]
            
        # ----------------------------------------
        # 第二步：排四课
        # ----------------------------------------
        gan_ji = self.JI_GONG[day_gan] # 日干寄宫
        
        lesson1_bottom = gan_ji
        lesson1_top = tian_pan[lesson1_bottom]
        
        lesson2_bottom = lesson1_top
        lesson2_top = tian_pan[lesson2_bottom]
        
        lesson3_bottom = day_zhi
        lesson3_top = tian_pan[lesson3_bottom]
        
        lesson4_bottom = lesson3_top
        lesson4_top = tian_pan[lesson4_bottom]
        
        sike = [
            {"top": lesson4_top, "bottom": lesson4_bottom, "name": "四课(辰阴)"},
            {"top": lesson3_top, "bottom": lesson3_bottom, "name": "三课(辰课)"},
            {"top": lesson2_top, "bottom": lesson2_bottom, "name": "二课(日阴)"},
            {"top": lesson1_top, "bottom": lesson1_bottom, "name": "一课(日课)"}
        ]
        
        # ----------------------------------------
        # 第三步：排三传 (初、中、末)
        # ----------------------------------------
        chu_chuan, rule_name = self._get_san_chuan(sike)
        zhong_chuan = tian_pan[chu_chuan] # 中传 = 初传的天盘神
        mo_chuan = tian_pan[zhong_chuan]  # 末传 = 中传的天盘神
        
        san_chuan = [
            {"pos": "初传", "zhi": chu_chuan},
            {"pos": "中传", "zhi": zhong_chuan},
            {"pos": "末传", "zhi": mo_chuan}
        ]

        # ----------------------------------------
        # 第四步：排十二贵神 (天将)
        # ----------------------------------------
        jiang_pan = self._get_tian_jiang(day_gan, hour_zhi, tian_pan)
        
        # 将贵神附加到三传中返回
        for chuan in san_chuan:
            chuan["jiang"] = jiang_pan[chuan["zhi"]]

        return {
            "tian_pan": tian_pan,
            "jiang_pan": jiang_pan,
            "ji_gong": gan_ji,
            "sike": sike,
            "san_chuan": san_chuan,
            "san_chuan_rule": rule_name
        }